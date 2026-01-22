from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List


ROOT_DIR = Path(__file__).resolve().parents[1]
CROSSWALK_DIR = ROOT_DIR / "data" / "crosswalk"

OLIR_IN = CROSSWALK_DIR / "csf_2_0_olir_export.json"
CSF_MIN_OUT = CROSSWALK_DIR / "csf_min.json"

FUNC_ORDER = ["GV", "ID", "PR", "DE", "RS", "RC"]


def _safe_load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _safe_write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _backup_file(path: Path) -> None:
    if not path.exists():
        return
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.stem}.backup-{ts}{path.suffix}")
    backup.write_bytes(path.read_bytes())


def _extract_elements(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    return (
        raw.get("response", {})
           .get("elements", {})
           .get("elements", [])
        or []
    )


def _is_inactive(eid: str, title: str, text: str) -> bool:
    """
    Conservative filter:
    - Drop wrapper IDs that start with WR-
    - Drop anything whose text/title explicitly says withdrawn
    """
    eid = (eid or "").strip()
    title = (title or "").strip()
    text = (text or "").strip()
    if eid.startswith("WR-"):
        return True
    joined = f"{title} {text}".lower()
    if "withdrawn" in joined:
        return True
    return False


def build_csf_min_from_olir(olir: Dict[str, Any]) -> List[Dict[str, Any]]:
    elements = _extract_elements(olir)
    if not elements:
        raise ValueError("OLIR export missing response.elements.elements[]")

    funcs: Dict[str, Dict[str, str]] = {}      # GV -> {title, description(text)}
    cats: Dict[str, Dict[str, str]] = {}       # GV.OC -> {title, description(text)}
    subs: Dict[str, Dict[str, str]] = {}       # GV.OC-01 -> {outcome(text)}
    ex_by_sub: Dict[str, List[str]] = {}       # GV.OC-01 -> [examples]

    for el in elements:
        etype = (el.get("element_type") or "").strip()
        eid = (el.get("element_identifier") or "").strip()
        title = (el.get("title") or "").strip()
        text = (el.get("text") or "").strip()

        if not etype or not eid:
            continue
        if _is_inactive(eid, title, text):
            continue

        if etype == "function":
            funcs[eid] = {"id": eid, "title": title, "description": text}

        elif etype == "category":
            cats[eid] = {"id": eid, "title": title, "description": text}

        elif etype == "subcategory":
            subs[eid] = {"id": eid, "outcome": text}

        elif etype == "implementation_example":
            # Example IDs are like "GV.OC-01.001" -> parent subcategory "GV.OC-01"
            if "." in eid:
                parent = eid.rsplit(".", 1)[0]
                if text:
                    ex_by_sub.setdefault(parent, []).append(text)

    # Build relationships by identifier conventions
    cats_by_func: Dict[str, List[Dict[str, str]]] = {}
    for cat_id, cat in cats.items():
        func_id = cat_id.split(".", 1)[0]  # GV.OC -> GV
        cats_by_func.setdefault(func_id, []).append(cat)

    subs_by_cat: Dict[str, List[Dict[str, str]]] = {}
    for sub_id, sub in subs.items():
        cat_id = sub_id.split("-", 1)[0]   # GV.OC-01 -> GV.OC
        subs_by_cat.setdefault(cat_id, []).append(sub)

    # Assemble final schema: LIST AT ROOT (works with your _index_csf())
    ordered_funcs = [f for f in FUNC_ORDER if f in funcs] + [f for f in sorted(funcs.keys()) if f not in FUNC_ORDER]

    out: List[Dict[str, Any]] = []
    for fid in ordered_funcs:
        fn = funcs[fid]
        fn_obj = {
            "id": fid,
            "title": fn.get("title", ""),
            "description": fn.get("description", ""),
            "categories": []
        }

        for cat in sorted(cats_by_func.get(fid, []), key=lambda x: x.get("id", "")):
            cat_id = cat["id"]
            cat_obj = {
                "id": cat_id,
                "title": cat.get("title", ""),
                "description": cat.get("description", ""),
                "outcomes": []
            }

            for sub in sorted(subs_by_cat.get(cat_id, []), key=lambda x: x.get("id", "")):
                sid = sub["id"]
                cat_obj["outcomes"].append({
                    "id": sid,
                    "outcome": sub.get("outcome", ""),
                    "examples": ex_by_sub.get(sid, []),
                })

            fn_obj["categories"].append(cat_obj)

        out.append(fn_obj)

    return out


def main() -> None:
    if not OLIR_IN.exists():
        raise FileNotFoundError(f"OLIR input not found: {OLIR_IN}")

    olir = _safe_load_json(OLIR_IN)
    csf_min = build_csf_min_from_olir(olir)

    _backup_file(CSF_MIN_OUT)
    _safe_write_json(CSF_MIN_OUT, csf_min)

    func_count = len(csf_min)
    cat_count = sum(len(f.get("categories", [])) for f in csf_min)
    sub_count = sum(len(c.get("outcomes", [])) for f in csf_min for c in f.get("categories", []))
    print(f"✅ Wrote {CSF_MIN_OUT}")
    print(f"   Functions: {func_count}, Categories: {cat_count}, Subcategories: {sub_count}")


if __name__ == "__main__":
    main()
