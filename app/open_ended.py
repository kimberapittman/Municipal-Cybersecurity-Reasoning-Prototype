import streamlit as st
from datetime import datetime
from io import BytesIO
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
import textwrap
import html
import json


def _safe_rerun():
    try:
        if hasattr(st, "rerun"):
            st.rerun()
        elif hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
    except Exception:
        pass


def _html_block(s: str) -> str:
    return "\n".join(line.lstrip() for line in s.splitlines())

def render_divider():
    st.markdown(
        """
        <hr style="
            margin: 1.25rem 0;
            border: none;
            height: 1px;
            background: linear-gradient(
                90deg,
                rgba(255,255,255,0.00),
                rgba(255,255,255,0.35),
                rgba(255,255,255,0.00)
            );
        ">
        """,
        unsafe_allow_html=True,
    )


def csf_section_open(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="csf-section">
          <div style="font-size: 1.35rem; font-weight: 750; margin: 0 0 0.25rem 0;">
            {title}
          </div>
          <div style="color: rgba(229,231,235,0.75); margin: 0 0 0.75rem 0; line-height: 1.45;">
            {subtitle}
          </div>
        """,
        unsafe_allow_html=True,
    )

def csf_section_close():
    st.markdown("</div>", unsafe_allow_html=True)


OE_STEP_TITLES = {
    1: "Scenario Description",
    2: "Decision Point",
    3: "Procedural Context",
    4: "Technical Consideration(s)",
    5: "Stakeholder(s) Identification",
    6: "Ethical Consideration(s)",
    7: "Tension Identification",
    8: "Institutional and Governance Constraints",
    9: "Decision (and documented rationale)",
}
OE_TOTAL_STEPS = max(OE_STEP_TITLES.keys())
assert set(OE_STEP_TITLES.keys()) == set(range(1, OE_TOTAL_STEPS + 1)), "Step numbers must be contiguous."

OE_RECORD_KEY = "oe_record"

def oe_init_record():
    if OE_RECORD_KEY in st.session_state:
        return

    st.session_state[OE_RECORD_KEY] = {
        "scenario_description": "",
        "decision_point": "",
        "procedural_context": "",

        "technical": {
            "csf_categories": [],
            "csf_outcomes": [],
            "other_notes": "",
        },

        "stakeholders": [],

        "ethical": {
            "pfce_salience_selected": [],
            "pfce_principles": [],
            "pfce_pressure_summary": "",
        },

        "tension": {
            "a": "",
            "b": "",
        },

        "tradeoff_reasoning": "",

        "constraints": {
            "selected": [],
            "other": "",
        },

        "decision": {
            "decision_text": "",
            "documented_rationale": "",
        },
    }

OE_KEYMAP = {
    # Steps 1–3
    "scenario_description": "oe_scenario_description",
    "decision_point": "oe_decision_point",
    "procedural_context": "oe_csf_function",

    # Step 4 (technical)
    "technical_other_notes": "oe_technical_other",
    # If you implement CSF mapping checkboxes later, store these lists:
    "csf_categories": "oe_csf_categories_selected",
    "csf_outcomes": "oe_csf_outcomes_selected",

    # Step 5 (stakeholders)
    "stakeholders_combined": "oe_stakeholders",  # set this yourself after parsing "Other"

    # Step 6 (ethical)
    "pfce_salience_selected": "oe_pfce_salience_selected",
    "pfce_principles": "oe_pfce_principles",
    "pfce_pressure_summary": "oe_pfce_pressure_summary",

    # Step 7 (tension)
    "tension_a": "oe_tension_a",              # strongly recommend splitting, not one blob
    "tension_b": "oe_tension_b",
    "tradeoff_reasoning": "oe_reasoning_tradeoff",

    # Step 8 (institutional and governance constraints)
    "constraints_selected": "oe_constraints",
    "constraints_other": "oe_constraints_other",

    # Step 9 (decision documentation)
    "decision_text": "oe_decision_documentation",
    "decision_rationale": "oe_decision_rationale",
}

def oe_sync_record():
    rec = st.session_state.get(OE_RECORD_KEY)
    if not rec:
        return

    km = OE_KEYMAP

    def _get(key, default=""):
        return st.session_state.get(key, default)

    # Step 1–3
    rec["scenario_description"] = str(_get(km["scenario_description"], "")).strip()
    rec["decision_point"] = str(_get(km["decision_point"], "")).strip()
    rec["procedural_context"] = str(_get(km["procedural_context"], "")).strip()

    # Step 4
    rec["technical"]["csf_categories"] = _get(km["csf_categories"], []) or []
    rec["technical"]["csf_outcomes"] = _get(km["csf_outcomes"], []) or []
    rec["technical"]["other_notes"] = str(_get(km["technical_other_notes"], "")).strip()

    # Step 5
    rec["stakeholders"] = _get(km["stakeholders_combined"], []) or []

    # Step 6
    rec["ethical"]["pfce_salience_selected"] = _get(km["pfce_salience_selected"], []) or []
    rec["ethical"]["pfce_principles"] = _get(km["pfce_principles"], []) or []
    rec["ethical"]["pfce_pressure_summary"] = str(_get(km["pfce_pressure_summary"], "")).strip()

    # Step 7
    rec["tension"]["a"] = str(_get(km.get("tension_a", ""), "")).strip()
    rec["tension"]["b"] = str(_get(km.get("tension_b", ""), "")).strip()
    rec["tradeoff_reasoning"] = str(_get(km["tradeoff_reasoning"], "")).strip()
    rec["tension"]["statement"] = (
        f"{rec['tension']['a']}  ⟷  {rec['tension']['b']}".strip(" ⟷ ")
)

    # Step 8
    rec["constraints"]["selected"] = _get(km["constraints_selected"], []) or []
    rec["constraints"]["other"] = str(_get(km["constraints_other"], "")).strip()
    rec["decision"]["decision_text"] = str(_get(km["decision_text"], "")).strip()
    rec["decision"]["documented_rationale"] = str(_get(km["decision_rationale"], "")).strip()

    st.session_state[OE_RECORD_KEY] = rec


STAKEHOLDER_OPTIONS = [
    "Local Residents/Businesses",
    "City Leadership (Mayor, City Manager, City Council)",
    "Department leadership (Public Works, Utilities, Police, Fire, etc.)",
    "IT/Cybersecurity Team",
    "City Employees/Internal Staff",
    "Vendors/Managed Service Providers",
    "State or Federal Partners/Regulators",
    "Law enforcement / investigative partners",
    "Finance/Procurement/Legal",
    "Media/Public Information Office",
]

CSF_EXPORT_PATH = Path("data/csf-export.json")  # update if you renamed the file

@st.cache_data(show_spinner=False)
def load_csf_export_index(path: str):
    """
    Builds indexes from the NIST CSF reference-tool export schema.
    Returns:
      functions: {FN_ID: {"title":..., "description":...}}
      categories: {CAT_ID: {"title":..., "description":..., "function": FN_ID}}
      subcats: {SUB_ID: {"text":..., "category": CAT_ID}}
      cats_by_fn: {FN_ID: [CAT_ID, ...]}
      subs_by_cat: {CAT_ID: [SUB_ID, ...]}
      refs_by_subcat: {SUB_ID: [ {doc_name, doc_version, doc_url, dest_element_identifier} ... ]}
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))

    elems = raw.get("response", {}).get("elements", {}).get("elements", [])
    docs = raw.get("response", {}).get("elements", {}).get("documents", [])
    rels = raw.get("response", {}).get("elements", {}).get("relationships", [])

    doc_map = {d.get("doc_identifier"): d for d in docs if d.get("doc_identifier")}

    functions = {}
    categories = {}
    subcats = {}
    cats_by_fn = {}
    subs_by_cat = {}
    refs_by_subcat = {}

    # --- Parse CSF core elements ---
    for e in elems:
        if e.get("doc_identifier") != "CSF_2_0_0":
            continue

        et = e.get("element_type")
        eid = e.get("element_identifier")
        title = (e.get("title") or "").strip()
        text = (e.get("text") or "").strip()

        if et == "function":
            functions[eid] = {"title": title or eid, "description": text}
            cats_by_fn.setdefault(eid, [])

        elif et == "category":
            fn_id = eid.split(".")[0]  # GV.OC -> GV
            categories[eid] = {"title": title or eid, "description": text, "function": fn_id}
            cats_by_fn.setdefault(fn_id, []).append(eid)
            subs_by_cat.setdefault(eid, [])

        elif et == "subcategory":
            cat_id = eid.split("-")[0]  # GV.OC-01 -> GV.OC
            subcats[eid] = {"text": text, "category": cat_id}
            subs_by_cat.setdefault(cat_id, []).append(eid)

    # Dedupe category lists
    for fn_id, lst in cats_by_fn.items():
        cats_by_fn[fn_id] = list(dict.fromkeys(lst))

    # --- Parse informative references (external_reference relationships) ---
    for r in rels:
        if r.get("relationship_identifier") != "external_reference":
            continue
        if r.get("source_doc_identifier") != "CSF_2_0_0":
            continue

        src_subcat = r.get("source_element_identifier")  # e.g., GV.OC-01
        dest_doc = r.get("dest_doc_identifier")
        dest_elem = r.get("dest_element_identifier")

        d = doc_map.get(dest_doc, {})
        refs_by_subcat.setdefault(src_subcat, []).append({
            "doc_name": d.get("name") or dest_doc,
            "doc_version": d.get("version") or "",
            "doc_url": d.get("website") or "",
            "dest_element_identifier": dest_elem or "",
        })

    return functions, categories, subcats, cats_by_fn, subs_by_cat, refs_by_subcat


CSF_FUNCTION_PROMPTS = {
    "GV": {
        "label": "GOVERN (GV)",
        "prompt": "Are you establishing, reviewing, or overseeing cybersecurity risk management strategy, policies, or governance expectations?",
    },
    "ID": {
        "label": "IDENTIFY (ID)",
        "prompt": "Are you working to understand current cybersecurity risks, such as identifying assets, systems, vulnerabilities, or risk exposure?",
    },
    "PR": {
        "label": "PROTECT (PR)",
        "prompt": "Are you applying or managing safeguards to reduce or manage cybersecurity risk?",
    },
    "DE": {
        "label": "DETECT (DE)",
        "prompt": "Are you monitoring for, identifying, or analyzing potential cybersecurity attacks or compromises?",
    },
    "RS": {
        "label": "RESPOND (RS)",
        "prompt": "Are you taking action in response to a confirmed cybersecurity incident?",
    },
    "RC": {
        "label": "RECOVER (RC)",
        "prompt": "Are you restoring systems, data, or operations affected by a cybersecurity incident?",
    },
}

PFCE_PRESSURE_PROMPTS = {
    "Beneficence": {
        "label": "Beneficence",
        "prompt": "What benefit is being protected or promoted—and for whom?",
    },
    "Non-maleficence": {
        "label": "Non-maleficence",
        "prompt": "What foreseeable harm is being avoided or accepted?",
    },
    "Autonomy": {
        "label": "Autonomy",
        "prompt": "Whose choices or agency are being constrained, overridden, or preserved?",
    },
    "Justice": {
        "label": "Justice",
        "prompt": "Are impacts or protections distributed unevenly across groups or communities?",
    },
    "Explicability": {
        "label": "Explicability",
        "prompt": "What would be difficult to explain, justify, or defend about this decision?",
    },
}


PFCE_DEFINITIONS = {
    "Beneficence": (
        "Cybersecurity technologies should be used to benefit humans, promote human well-being, "
        "and make our lives better overall."
    ),
    "Non-maleficence": (
        "Cybersecurity technologies should not be used to intentionally harm humans or to make "
        "our lives worse overall."
    ),
    "Autonomy": (
        "Cybersecurity technologies should be used in ways that respect human autonomy. Humans "
        "should be able to make informed decisions for themselves about how that technology is used "
        "in their lives."
    ),
    "Justice": (
        "Cybersecurity technologies should be used to promote fairness, equality, and impartiality. "
        "They should not be used to unfairly discriminate, undermine solidarity, or prevent equal access."
    ),
    "Explicability": (
        "Cybersecurity technologies should be used in ways that are intelligible, transparent, and "
        "comprehensible, and it should be clear who is accountable and responsible for their use."
    ),
}

PFCE_SURFACING_PROMPTS = [
    {
        "id": "harm_disadvantage",
        "prompt": "This decision could cause harm or disadvantage to people, even indirectly.",
        "maps_to": ["Non-maleficence", "Justice"],
    },
    {
        "id": "cost_of_failure",
        "prompt": "The costs or burdens of failure would fall unevenly or unfairly.",
        "maps_to": ["Justice", "Non-maleficence"],
    },
    {
        "id": "rights_dependencies",
        "prompt": "This decision could affect people’s rights, expectations, or reliance on services.",
        "maps_to": ["Autonomy", "Beneficence"],
    },
    {
        "id": "public_justification",
        "prompt": "This decision would be difficult to publicly justify or defend if questioned later.",
        "maps_to": ["Explicability", "Justice", "Non-maleficence"],
    },
    {
        "id": "ethical_discomfort",
        "prompt": "This decision feels ethically uncomfortable, even if it is technically justified.",
        "maps_to": ["Beneficence", "Non-maleficence", "Explicability"],
    },
]

OLD_PFCE_PROMPTS = {
    "Beneficence": "Could this decision affect human well-being or access to essential services?",
    "Non-maleficence": "Could this decision foreseeably cause harm (directly or indirectly)?",
    "Autonomy": "Could this decision constrain people’s ability to make informed choices about how they are affected?",
    "Justice": "Could impacts or protections be distributed unevenly across groups or neighborhoods?",
    "Explicability": "Is accountability, transparency, or explainability central to this decision?",
}

TEMP_CONSTRAINT_OPTIONS = [
    "Legal or regulatory requirements",
    "Public transparency or disclosure obligations",
    "Budgetary or resource limitations",
    "Staffing or expertise constraints",
    "Procurement or contracting limitations",
    "Political or leadership direction",
    "Interagency or third-party dependencies",
    "Time sensitivity or urgency",
    "Incomplete or uncertain information",
]


def _build_pdf(title: str, lines: list[str]) -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    x = 54
    y = height - 54

    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, title[:120])
    y -= 24

    c.setFont("Helvetica", 10)

    rec = st.session_state.get(OE_RECORD_KEY, {})
    tension = rec.get("tension", {}).get("statement", "")

    if tension:
        lines.append(f"Decision Tension: {tension}")
    else:
        lines.append("Decision Tension: Not specified")

    code = rec.get("procedural_context", "").strip()
    label = CSF_FUNCTION_PROMPTS.get(code, {}).get("label", code or "Not specified")
    lines.append(f"Procedural Context: {label}")

    for raw in lines:
        wrapped = textwrap.wrap(raw, width=100) if raw else [""]
        for wline in wrapped:
            if y < 72:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 54
            c.drawString(x, y, wline)
            y -= 14
        y -= 6

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def _render_open_header(step: int):
    step_title = html.escape(OE_STEP_TITLES.get(step) or OE_STEP_TITLES.get(1, "Step"))

    st.markdown(
        f"""
        <div style="text-align:center; margin-top: 0;">
          <h2 style="margin: 0 0 0.25rem 0;">{step_title}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <hr style='
            margin: 14px 0 20px 0;
            border: none;
            height: 2px;
            background: linear-gradient(
                90deg,
                rgba(76,139,245,0.15),
                rgba(76,139,245,0.55),
                rgba(76,139,245,0.15)
            );
        '>
        """,
        unsafe_allow_html=True,
    )


def render_open_ended():
    oe_init_record()

    if "oe_step" not in st.session_state:
        st.session_state["oe_step"] = 1

    total_steps = OE_TOTAL_STEPS
    step = int(st.session_state["oe_step"])

    step = max(1, min(step, total_steps))
    st.session_state["oe_step"] = step

    _render_open_header(step)
    st.progress(step / float(total_steps))

    st.markdown(
        f"""
        <div style="
            margin-top: -12px;
            font-size: 0.85rem;
            color: rgba(229,231,235,0.75);
        ">
            Step {step} of {total_steps}
        </div>
        """,
        unsafe_allow_html=True,
    )
    

    # ==========================================================
    # TILE HELPER (safe)
    # ==========================================================
    def _render_step_tile_html(title: str, body_html: str = ""):
        st.markdown(
            f"""
            <div class="listbox walkthrough-tile">
              <div class="walkthrough-step-title">{title}</div>
              {body_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


    # ==========================================================
    # STEP 1: Scenario Description
    # ==========================================================
    if step == 1:
        # Instruction text above the input
        st.markdown(
            """
            <div style="
                margin: 0 0 6px 0;
                font-weight: 500;
                color: rgba(229,231,235,0.90);
                font-size: 1.05rem;
                line-height: 1.45;
            ">
            Describe the situation requiring a decision. Include:
            <ul class="tight-list" style="margin-bottom: 0.75rem;">
                <li>What happened or what is being proposed</li>
                <li>When the decision must be made</li>
                <li>What constraints exist (time, resources, information)</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Text box with ONLY guidance as placeholder
        scenario_description = st.text_area(
            "Scenario Description",
            key="oe_scenario_description",
            height=120,
            placeholder="(Example: Following a suspected ransomware incident, some municipal systems have been restored while others remain offline. A decision is required on whether to further isolate network segments to limit potential spread, which would disrupt services that are currently functioning. The decision must be made quickly with limited information about the scope of compromise.)",
            label_visibility="collapsed",
        )


    # ==========================================================
    # STEP 2: Decision Point
    # ==========================================================
    elif step == 2:
        # Instruction text above the input
        st.markdown(
            """
            <div style="
                margin: 0 0 6px 0;
                font-weight: 500;
                color: rgba(229,231,235,0.90);
                font-size: 1.05rem;
                line-height: 1.45;
            ">
            What is the specific operational decision being considered?
            </div>
            """,
            unsafe_allow_html=True
        )

        # Text box with ONLY guidance as placeholder
        scenario_description = st.text_area(
            "Decision Point",
            key="oe_decision_point",
            height=120,
            placeholder="(Example: Whether to further isolate additional network segments to prevent potential ransomware spread.)",
            label_visibility="collapsed",
        )


    # ==========================================================
    # STEP 3: Procedural Context
    # ==========================================================
    elif step == 3:
        st.markdown(
            """
            <div style="
                margin: 0 0 6px 0;
                font-weight: 500;
                color: rgba(229,231,235,0.90);
                font-size: 1.05rem;
                line-height: 1.45;
            ">
            Which question best matches the procedural situation you are addressing?
            </div>
            """,
            unsafe_allow_html=True
        )

        selected = st.radio(
            label="Procedural Context",
            options=list(CSF_FUNCTION_PROMPTS.keys()),
            index=None,  # no default selection
            format_func=lambda k: CSF_FUNCTION_PROMPTS[k]["prompt"],
            key="oe_csf_function_choice",
            label_visibility="collapsed",
        )

        if selected:
            st.session_state["oe_csf_function"] = selected
            label = CSF_FUNCTION_PROMPTS.get(selected, {}).get("label", selected)
            st.info(f"Procedural context informed by NIST CSF Function: **{label}**")
        else:
            st.session_state["oe_csf_function"] = ""


    # ==========================================================
    # STEP 4: Technical Consideration(s)
    # ==========================================================
    elif step == 4:
        csf_fn_index, categories, subcats, cats_by_fn, subs_by_cat, refs_by_subcat = load_csf_export_index(str(CSF_EXPORT_PATH))

        selected_fn = st.session_state.get("oe_csf_function", "")
        fn_ids = [selected_fn] if selected_fn else list(csf_fn_index.keys())


        # --- Step 5 UI starts here ---
        st.markdown(
            """
            <div style="
                margin: 0 0 6px 0;
                font-weight: 500;
                color: rgba(229,231,235,0.90);
                font-size: 1.05rem;
                line-height: 1.45;
            ">
            Which technical considerations are relevant to this decision?
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div style="
                margin: 0 0 0.85rem 0;
                font-size: 0.9rem;
                color: rgba(229,231,235,0.65);
                line-height: 1.4;
            ">
            Select the technical consideration areas that apply. Optionally, expand an area to identify the technical outcomes implicated by this decision.
            </div>
            """,
            unsafe_allow_html=True
        )

        selected_cat_ids = []
        selected_subcat_ids = []

        for fn_id in fn_ids:
            fn = csf_fn_index.get(fn_id, {})
            fn_title = fn.get("title", fn_id)
            fn_desc = fn.get("description", "")

            st.markdown(
                f"""
                <div style="margin: 0.75rem 0 0.25rem 0; font-weight: 800;">
                {fn_title}
                </div>
                <div style="margin: 0 0 0.5rem 0; color: rgba(229,231,235,0.70); font-size: 0.9rem; line-height: 1.4;">
                {fn_desc}
                </div>
                """,
                unsafe_allow_html=True
            )

            for cat_id in cats_by_fn.get(fn_id, []):
                cat = categories.get(cat_id, {})
                cat_title = cat.get("title", cat_id)
                cat_desc = cat.get("description", "")

                cat_checked = st.checkbox(
                    f"{cat_title}",
                    key=f"oe_csf_cat_{cat_id}",
                    help=cat_desc if cat_desc else None,
                )

                if cat_checked:
                    selected_cat_ids.append(cat_id)

                # Subcategory outcomes are optional and can be selected even if category isn't checked
                with st.expander("View technical outcomes (optional)", expanded=False):
                    st.caption("Select outcomes directly implicated by this decision.")

                    for sid in subs_by_cat.get(cat_id, []):
                        s_text = subcats.get(sid, {}).get("text", sid)

                        s_checked = st.checkbox(
                            s_text,
                            key=f"oe_csf_sub_{sid}",
                        )
                        if s_checked:
                            selected_subcat_ids.append(sid)

        # De-dupe, preserve order
        selected_cat_ids = list(dict.fromkeys(selected_cat_ids))
        selected_subcat_ids = list(dict.fromkeys(selected_subcat_ids))

        # Store for export
        st.session_state["oe_csf_categories_selected"] = selected_cat_ids
        st.session_state["oe_csf_outcomes_selected"] = selected_subcat_ids  # subcategory IDs
        # Optional: record whether references were used (you can toggle this later if you want)
        # st.session_state["oe_informative_refs_viewed"] = True/False  (if you add a button)

        st.markdown("---")
        st.text_area(
            "Other technical considerations (optional)",
            key="oe_technical_other",
            height=90,
            placeholder="Add any decision-specific technical concerns not captured above.",
        )


    # ==========================================================
    # STEP 5: STAKEHOLDER IDENTIFICATION
    # ==========================================================
    elif step == 5:
        st.markdown(
            """
            <div style="
                margin: 0 0 6px 0;
                font-weight: 500;
                color: rgba(229,231,235,0.90);
                font-size: 1.05rem;
                line-height: 1.45;
            ">
            Which stakeholders are affected by or involved in this decision?
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div style="
                margin: 0 0 0.75rem 0;
                font-size: 0.9rem;
                color: rgba(229,231,235,0.65);
                line-height: 1.4;
            ">
            Select all that apply. If a stakeholder is missing, add it under “Other.”
            </div>
            """,
            unsafe_allow_html=True
        )

        selected_stakeholders = []

        # Scannable list (NO fixed-height container so "Other" sits directly under the last item)
        for stakeholder in STAKEHOLDER_OPTIONS:
            if st.checkbox(stakeholder, key=f"oe_stakeholders_{hash(stakeholder)}"):
                selected_stakeholders.append(stakeholder)


        # "Other" row: checkbox left, textbox right (appears immediately when checked)
        col_l, col_r = st.columns([1, 2], gap="large")

        with col_l:
            add_other = st.checkbox(
                "Other stakeholder(s) not listed",
                key="oe_stakeholders_other_toggle",
            )

        other_text = ""
        with col_r:
            if add_other:
                other_text = st.text_area(
                    "Other stakeholders",
                    key="oe_stakeholders_other_text",
                    height=80,
                    placeholder="Example: Regional 911 dispatch, county emergency management, union representatives",
                    label_visibility="collapsed",
                ).strip()
            else:
                st.empty()

        # Parse “Other” into list (comma-separated), combine, de-dupe
        other_list = [s.strip() for s in other_text.split(",") if s.strip()]
        combined = list(dict.fromkeys(selected_stakeholders + other_list))

        # Persist
        st.session_state["oe_stakeholders"] = combined

    # ==========================================================
    # STEP 6: Ethical Consideration(s)
    # ==========================================================
    elif step == 6:

        # ---------- A) Ethical Salience Check (checkbox triage; no writing) ----------
        with st.container():
            st.markdown('<div class="pfce-surfacing-anchor"></div>', unsafe_allow_html=True)

            csf_section_open(
                "Ethical Salience Check",
                "Select any prompts that indicate this decision has ethically significant pressures. "
                "If none apply, you may proceed."
            )

            selected_salience_ids = []
            for item in PFCE_SURFACING_PROMPTS:
                sid = item["id"]
                q = item["prompt"]

                checked = st.checkbox(
                    q,
                    key=f"oe_pfce_salience_{sid}",
                )
                if checked:
                    selected_salience_ids.append(sid)

            # Persist salience selections for export / later steps
            st.session_state["oe_pfce_salience_selected"] = selected_salience_ids

            csf_section_close()

        # ---------- B) Derive implicated PFCE principles from salience selections ----------
        implicated = []
        for item in PFCE_SURFACING_PROMPTS:
            sid = item["id"]
            if sid in (st.session_state.get("oe_pfce_salience_selected") or []):
                implicated.extend(item.get("maps_to", []))

        # De-dupe, preserve order, restrict to known principles
        known = set(PFCE_DEFINITIONS.keys())
        implicated = [p for p in list(dict.fromkeys(implicated)) if p in known]

        # If no salience selected, clear downstream state and stop UI here (no gating)
        if not selected_salience_ids:
            st.session_state["oe_pfce_principles"] = []
            st.session_state["oe_pfce_pressure"] = {}
            st.info("Ethical considerations: **None specified**")
        else:
            # ---------- C) PFCE Principles Implicated (user can refine) ----------
            with st.container():
                st.markdown('<div class="pfce-principles-anchor"></div>', unsafe_allow_html=True)

                csf_section_open(
                    "PFCE Principles Implicated",
                    "Based on your selections above, the following PFCE principles may be implicated. "
                    "You may deselect any that do not apply."
                )

                selected_pfce = []
                for pid in implicated:
                    definition = (PFCE_DEFINITIONS.get(pid, "") or "").strip()

                    # Use checkbox help tooltips instead of fragile hover hacks
                    checked = st.checkbox(
                        pid,
                        key=f"oe_pfce_implicated_{pid}",
                        value=True,
                        help=definition if definition else None,
                    )
                    if checked:
                        selected_pfce.append(pid)

                st.session_state["oe_pfce_principles"] = selected_pfce

                if selected_pfce:
                    st.info("Principles selected: **" + ", ".join(selected_pfce) + "**")
                else:
                    st.info("Principles selected: **None selected**")

                csf_section_close()

            # ---------- D) Minimal PFCE pressure capture (single short field) ----------
            with st.container():
                st.markdown('<div class="pfce-pressure-anchor"></div>', unsafe_allow_html=True)

                csf_section_open(
                    "Ethical Pressure (brief)",
                    "In 1–2 sentences, state what is ethically at stake in this decision. "
                    "This will support the next step (tension articulation)."
                )

                # Optional: show the principle-specific prompts as lightweight guidance (no extra fields)
                if st.session_state.get("oe_pfce_principles"):
                    with st.expander("View principle-guidance prompts (optional)", expanded=False):
                        for pid in st.session_state["oe_pfce_principles"]:
                            q = (PFCE_PRESSURE_PROMPTS.get(pid, {}) or {}).get("prompt", "").strip()
                            if q:
                                st.write(f"- **{pid}:** {q}")

                ethical_pressure = st.text_area(
                    "Ethical pressure",
                    key="oe_pfce_pressure_summary",
                    height=110,
                    placeholder="Example: Maintaining continuity of essential services reduces harm to residents, but rapid containment actions may restrict access and shift burdens unevenly across neighborhoods.",
                    label_visibility="collapsed",
                ).strip()

                # Store as a compact structure for export
                st.session_state["oe_pfce_pressure"] = {
                    "summary": ethical_pressure,
                    "principles": st.session_state.get("oe_pfce_principles", []) or [],
                    "salience_selected": st.session_state.get("oe_pfce_salience_selected", []) or [],
                }

                csf_section_close()
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      

    # ==========================================================
    # STEP 7: TENSION IDENTIFICATION
    # ==========================================================
    elif step == 7:
        st.markdown(
            """
            <div style="
                margin: 0 0 6px 0;
                font-weight: 500;
                color: rgba(229,231,235,0.90);
                font-size: 1.05rem;
                line-height: 1.45;
            ">
            What is the central decision tension at this decision point?
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div style="
                margin: 0 0 0.75rem 0;
                font-size: 0.9rem;
                color: rgba(229,231,235,0.65);
                line-height: 1.4;
            ">
            State the tension as two justified considerations that cannot both be fully satisfied at this decision point.
            These considerations may be ethical, technical, or both.
            </div>
            """,
            unsafe_allow_html=True
        )

        # ---- Optional context cues (pull-through from earlier steps) ----
        decision_point = (st.session_state.get("oe_decision_point", "") or "").strip()

        csf_code = (st.session_state.get("oe_csf_function", "") or "").strip()
        csf_label = CSF_FUNCTION_PROMPTS.get(csf_code, {}).get("label", csf_code) if csf_code else "Not specified"

        tech_cats = st.session_state.get("oe_csf_categories_selected", []) or []
        tech_outs = st.session_state.get("oe_csf_outcomes_selected", []) or []
        tech_other = (st.session_state.get("oe_technical_other", "") or "").strip()

        salience = st.session_state.get("oe_pfce_salience_selected", []) or []
        principles = st.session_state.get("oe_pfce_principles", []) or []
        ethical_pressure = (st.session_state.get("oe_pfce_pressure_summary", "") or "").strip()

        with st.expander("View context cues (optional)", expanded=False):
            if decision_point:
                st.write(f"**Decision point:** {decision_point}")
            st.write(f"**Procedural context (CSF):** {csf_label}")

            st.write(f"**Technical selections:** {len(tech_cats)} category area(s), {len(tech_outs)} outcome(s)")
            if tech_other:
                st.write(f"**Other technical notes:** {tech_other}")

            if salience:
                st.write(f"**Ethical salience flags selected:** {len(salience)}")
            if principles:
                st.write("**PFCE principles implicated:** " + ", ".join(principles))
            if ethical_pressure:
                st.write("**Ethical pressure (brief):** " + ethical_pressure)

        # ---- Optional tension type label (no gating) ----
        st.radio(
            "Tension type (optional)",
            options=[
                "Not specified",
                "Ethical–Technical",
                "Technical–Technical",
                "Ethical–Ethical",
            ],
            index=0,
            key="oe_tension_type",
            horizontal=True,
        )

        # ---- Decision tension input ----
        with st.container():
            st.markdown('<div class="tension-anchor"></div>', unsafe_allow_html=True)

            csf_section_open(
                "Decision Tension",
                "Write two justified considerations that pull in different directions at this decision point."
            )

            a = st.text_area(
                "Consideration A",
                key="oe_tension_a",
                height=90,
                placeholder=(
                    "Example (technical): Maintain system availability and service continuity.\n"
                    "Example (ethical): Avoid harm to residents dependent on disrupted services."
                ),
            )

            b = st.text_area(
                "Consideration B",
                key="oe_tension_b",
                height=90,
                placeholder=(
                    "Example (technical): Contain compromise quickly to prevent wider spread.\n"
                    "Example (ethical): Preserve transparency and accountability in communications."
                ),
            )

            # Persist neutral tension statement for export (no assumptions)
            a_clean = (a or "").strip()
            b_clean = (b or "").strip()

            st.session_state["oe_tension_statement"] = f"{a_clean}  ⟷  {b_clean}".strip(" ⟷ ")

            # Optional lightweight feedback
            if a_clean or b_clean:
                st.caption("Tension captured for later justification and export.")
            else:
                st.caption("No tension recorded.")

            csf_section_close()


    # ==========================================================
    # STEP 8: INSTITUTIONAL AND GOVERNANCE CONSTRAINTS
    # ==========================================================
    elif step == 8:
        st.markdown(
            """
            <div style="
                margin: 0 0 6px 0;
                font-weight: 500;
                color: rgba(229,231,235,0.90);
                font-size: 1.05rem;
                line-height: 1.45;
            ">
            What institutional or governance constraints shape this decision?
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div style="
                margin: 0 0 0.75rem 0;
                font-size: 0.9rem;
                color: rgba(229,231,235,0.65);
                line-height: 1.4;
            ">
            Select all that apply. These constraints limit or shape feasible actions or justifications.
            </div>
            """,
            unsafe_allow_html=True
        )

        selected_constraints = []

        for c in TEMP_CONSTRAINT_OPTIONS:
            if st.checkbox(c, key=f"oe_constraint_{c}"):
                selected_constraints.append(c)

        # "Other" constraint (inline)
        col_l, col_r = st.columns([1, 2], gap="large")

        with col_l:
            add_other = st.checkbox(
                "Other constraint(s) not listed",
                key="oe_constraints_other_toggle",
            )

        other_text = ""
        with col_r:
            if add_other:
                other_text = st.text_area(
                    "Other constraints",
                    key="oe_constraints_other",
                    height=80,
                    placeholder="Example: Pending litigation, labor agreement provisions, state-level oversight",
                    label_visibility="collapsed",
                ).strip()
            else:
                st.empty()

        # Combine + de-dupe
        other_list = [s.strip() for s in other_text.split(",") if s.strip()]
        combined = list(dict.fromkeys(selected_constraints + other_list))

        # Persist
        st.session_state["oe_constraints"] = combined

        # Feedback + gating
        if combined:
            st.info("Constraints identified: **" + ", ".join(combined) + "**")
        else:
            st.info("Constraints identified: **None selected**")


        st.text_area(
            "Reasoning about consequences",
            key="oe_reasoning_tradeoff",
            height=120,
        )

    # ==========================================================
    # STEP 9: DECISION + OUTPUT 
    # ==========================================================
    elif step == 9:
        _render_step_tile_html(
            "Record the decision in operational terms, then generate a structured rationale for demonstration purposes.",
        )

        st.text_area(
            "Decision (operational)",
            key="oe_decision_documentation",
            height=120,
            placeholder="Example: Disconnect additional systems while confirming scope; preserve critical service workflows via manual workarounds.",
        )

        # ✅ Sync record ONLY here (or on Next/Prev)
        oe_sync_record()
        rec = st.session_state[OE_RECORD_KEY]

        # export rec (PDF generation, etc.) goes here


        # NAV CONTROLS (NO GATING)
        with st.container():
            st.markdown('<div class="oe-nav-anchor"></div>', unsafe_allow_html=True)

            col_l, col_r = st.columns(2, gap="large")

            with col_l:
                if step > 1:
                    if st.button("◀ Previous", key=f"oenav_prev_{step}"):
                        st.session_state["oe_step"] = step - 1
                        _safe_rerun()
                else:
                    st.empty()

            with col_r:
                if step < total_steps:
                    if st.button("Next ▶", key=f"oenav_next_{step}"):
                        st.session_state["oe_step"] = step + 1
                        _safe_rerun()
                else:
                    if st.button("Generate PDF", key="oe_generate_pdf", use_container_width=False):
                        st.session_state["oe_generate"] = True
                        _safe_rerun()




