from pathlib import Path
from typing import List, Dict, Any

import json
import yaml
import streamlit as st

# Base data directories
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
CASES_DIR = DATA_DIR / "cases"
CROSSWALK_DIR = DATA_DIR / "crosswalk"


# ---------- Generic file helpers ----------

def _safe_read_yaml(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _safe_read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ---------- NIST CSF / PFCE loaders ----------

@st.cache_data
def load_csf_data() -> Dict[str, Any]:
    """
    Load the minimal NIST CSF 2.0 structure from data/crosswalk/csf_min.json.

    Expected shape:
    {
      "functions": [
        {
          "id": "...",
          "name": "...",
          "categories": [
            {
              "id": "...",
              "name": "...",
              "subcategories": [
                {"id": "...", "outcome": "..."},
                ...
              ]
            },
            ...
          ]
        },
        ...
      ]
    }
    """
    path = CROSSWALK_DIR / "csf_min.json"
    return _safe_read_json(path)


@st.cache_data
def load_pfce_crosswalk() -> List[Dict[str, Any]]:
    """
    Load the CSF→PFCE crosswalk from data/crosswalk/pfce_crosswalk_scaffold.yaml.

    Expected shape: list of rows such as
    - csf_id: "PR.AC-3"
      csf_outcome: "Least privilege is enforced"
      pfce: ["Justice", "Non-maleficence"]
      rationale: "..."
    """
    path = CROSSWALK_DIR / "pfce_crosswalk_scaffold.yaml"
    data = _safe_read_yaml(path)
    # Support both list-at-root and {"rows": [...]}
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return data["rows"]
    return []


@st.cache_data
def load_pfce_principles() -> List[Dict[str, Any]]:
    """
    Load PFCE principles from data/crosswalk/pfce_principles.yaml.

    Supports shapes:
    1) {"principles": [ {...}, {...} ]}
    2) {"principles": {"beneficence": {...}, "non-maleficence": {...}, ...}}
    3) [ {...}, {...} ]
    """
    path = CROSSWALK_DIR / "pfce_principles.yaml"
    data = _safe_read_yaml(path)

    if data is None:
        return []

    # Shape 1 or 2: wrapped under "principles"
    if isinstance(data, dict) and "principles" in data:
        principles = data["principles"]

        # Shape 1: list
        if isinstance(principles, list):
            return principles

        # Shape 2: dict-of-dicts (your current YAML)
        if isinstance(principles, dict):
            result: List[Dict[str, Any]] = []
            for pid, p in principles.items():
                if isinstance(p, dict):
                    entry = dict(p)      # copy
                    entry.setdefault("id", pid)
                    result.append(entry)
            return result

        # Anything else under "principles" is unusable
        return []

    # Shape 3: bare list at top level
    if isinstance(data, list):
        return data

    # Fallback: unsupported shape
    return []



@st.cache_data
def load_constraints() -> List[str]:
    """
    Load a generic list of institutional/governance constraints if a file exists.

    If no structured file exists, fall back to a standard list used across the prototype.
    """
    # Try a YAML-based constraints file first, if you later add one.
    candidates = [
        DATA_DIR / "scenario_constraints.yaml",
        DATA_DIR / "constraints.yaml",
    ]
    for p in candidates:
        if p.exists():
            data = _safe_read_yaml(p)
            if isinstance(data, list):
                return [str(x) for x in data]
            if isinstance(data, dict):
                if isinstance(data.get("constraints"), list):
                    return [str(x) for x in data["constraints"]]
                # Flatten any simple dict of values
                return [str(v) for v in data.values()]

    # Fallback: standard list baked into thesis text / earlier prototype
    return [
        "Fragmented authority / unclear decision rights",
        "Procurement did not disclose ethical/surveillance risk",
        "Limited budget / staffing",
        "No/weak incident playbooks or continuity plans",
        "Vendor opacity (limited audit of code/training data)",
        "Lack of public engagement / oversight",
        "Legacy tech / poor segmentation / patch backlog",
        "Ambiguous data sharing/retention policies",
    ]


# ---------- Case-based mode helpers ----------

@st.cache_data
def list_cases() -> List[Dict[str, Any]]:
    """
    Return a list of available thesis cases from data/cases as:

    [
      {"id": "baltimore", "title": "City of Baltimore Ransomware Attack (2019)", "path": "..."},
      ...
    ]
    """
    cases: List[Dict[str, Any]] = []
    if not CASES_DIR.exists():
        return cases

    for path in sorted(CASES_DIR.glob("*.yaml")):
        data = _safe_read_yaml(path)
        cid = str(data.get("id") or path.stem)
        title = data.get("title") or path.stem
        ui_title = data.get("ui_title") or title
        short_summary = data.get("short_summary") or ""  # <-- ADD THIS LINE

        cases.append(
            {
                "id": cid,
                "title": title,          # canonical / thesis title
                "ui_title": ui_title,    # display-only title
                "short_summary": short_summary,
                "path": str(path),
                "raw": data,
            }
        )


    # Sort by title for stable UI
    cases.sort(key=lambda c: c["title"])
    return cases


@st.cache_data
def load_case(case_id: str) -> Dict[str, Any]:
    """
    Load a single case by id from data/cases/<id>.yaml (or matching id inside the file).

    Returns an empty dict if not found.
    """
    if not CASES_DIR.exists():
        return {}

    # First try by filename
    direct_path = CASES_DIR / f"{case_id}.yaml"
    if direct_path.exists():
        return _safe_read_yaml(direct_path) or {}

    # Fallback: scan for matching 'id' field
    for path in CASES_DIR.glob("*.yaml"):
        data = _safe_read_yaml(path)
        if str(data.get("id")) == case_id:
            return data

    return {}
