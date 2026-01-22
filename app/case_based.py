import streamlit as st
from logic.loaders import load_case, list_cases
import html

CB_TOTAL_STEPS = 9  

def _safe_rerun():
    try:
        if hasattr(st, "rerun"):
            st.rerun()
        elif hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
    except Exception:
        pass


PFCE_DEFINITIONS = {
    "Beneficence": (
        "Cybersecurity technologies should be used to benefit humans, "
        "promote human well-being, and make our lives better overall."
    ),
    "Non-maleficence": (
        "Cybersecurity technologies should not be used to intentionally harm humans "
        "or to make our lives worse overall."
    ),
    "Autonomy": (
        "Cybersecurity technologies should be used in ways that respect human autonomy. "
        "Humans should be able to make informed decisions for themselves about how that "
        "technology is used in their lives."
    ),
    "Justice": (
        "Cybersecurity technologies should be used to promote fairness, equality, "
        "and impartiality. They should not be used to unfairly discriminate, "
        "undermine solidarity, or prevent equal access."
    ),
    "Explicability": (
        "Cybersecurity technologies should be used in ways that are intelligible, "
        "transparent, and comprehensible, and it should be clear who is accountable "
        "and responsible for their use."
    ),
}


NIST_CSF_URL = "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf"
PFCE_URL = "https://doi.org/10.1016/j.cose.2021.102382"


NIST_CSF_HOVER = (
    "National Institute of Standards and Technology (NIST) Cybersecurity Framework (CSF): "
    "A voluntary framework that provides a common structure for identifying, assessing, and "
    "managing cybersecurity activities across the cybersecurity lifecycle. In this prototype, "
    "the CSF is used to situate decisions procedurally, "
)

PFCE_HOVER = (
    "Principlist Framework for Cybersecurity Ethics (PFCE): "
    "A normative, non-prescriptive framework that supports ethical reasoning by identifying "
    "ethically relevant principles and tensions within cybersecurity decision contexts."
)

CASE_HOOKS = {
    "baltimore": "Responding to a ransomware attack while maintaining essential public services",
    "sandiego": "Deploying surveillance technology while managing privacy, oversight, and public trust",
    "riverton": "Relying on AI-enabled security systems while retaining human accountability",
}

def _html_block(s: str) -> str:
    # Prevent Markdown from treating indented HTML as a code block.
    return "\n".join(line.lstrip() for line in s.splitlines())

def _step_tile_close():
    st.markdown("</div>", unsafe_allow_html=True)

def _bullets_html(value) -> str:
    if value is None:
        return "<div class='wt-tbd'>TBD</div>"

    if isinstance(value, list):
        if not value:
            return "<div class='wt-tbd'>TBD</div>"
        items = "".join(f"<li>{html.escape(str(item))}</li>" for item in value)
        return f"<ul class='wt-list'>{items}</ul>"

    # plain string
    return f"<div class='wt-text'>{html.escape(str(value))}</div>"
    
def render_case(case_id: str):
    # ==========================================================
    # VIEW STATE (default to "select" to avoid dropdown + open button)
    # ==========================================================
    if "cb_view" not in st.session_state:
        st.session_state["cb_view"] = "select"
    view = st.session_state["cb_view"]

    # ==========================================================
    # VIEW 0: SELECT (three tiles, landing-page styling)
    # ==========================================================
    if view == "select":
        cases = list_cases() or []
        top_cases = cases[:3]

        # --- Select a Case header ---
        st.markdown(
            """
            <div style="text-align:center; margin:0;">
            <h2 style="margin: 0 0 0.1rem 0; display:inline-block;">
                Select a Case
            </h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        # --- Framing line ---
        st.markdown(
            """
            <div style="
                margin: 4px 0 16px 0;
                color: rgba(229,231,235,0.75);
                font-size: 1.05rem;
                line-height: 1.45;
                text-align: center;
            ">
            Each case demonstrates how ethical and technical reasoning unfolds under a different municipal cybersecurity decision pressure.
            </div>
            """,
            unsafe_allow_html=True
        )

        # --- Anchor for tile-scoped CSS ---
        st.markdown(
            """
            <div class="case-tiles">
            <div class="case-tiles-anchor"></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if not top_cases:
            st.error("No cases found in data/cases.")
            return

        cols = st.columns(3, gap="large")

        for col, c in zip(cols, top_cases):
            cid = c.get("id", "")
            title = c.get("ui_title") or c.get("title", "TBD")
            cid_norm = str(cid).strip().lower()
            hook = CASE_HOOKS.get(cid_norm, "")

            with col:
                # Badge selection (based on case id)
                if str(cid).lower() == "riverton":
                    badge_html = (
                        '<div class="case-badge-wrap">'
                        '<span class="case-badge hypo" '
                        'title="Constructed scenario used to demonstrate forward-looking reasoning.">'
                        'Hypothetical Scenario'
                        '</span>'
                        '</div>'
                    )
                else:
                    badge_html = (
                        '<div class="case-badge-wrap">'
                        '<span class="case-badge real" '
                        'title="Reconstructed from documented municipal incidents.">'
                        'Real-World Incident'
                        '</span>'
                        '</div>'
                    )

                st.markdown(
                    _html_block(
                        f"""
                        <a href="?cb_case_id={html.escape(str(cid))}" target="_self"
                        style="text-decoration:none; color: inherit; display:block;">
                        <div class="listbox case-tile" style="cursor:pointer;">
                            {badge_html}
                            <div class="tile-title">{html.escape(title)}</div>
                            {(
                                '<div class="tile-hook">' + html.escape(hook) + '</div>'
                            ) if hook else ""}
                        </div>
                        </a>
                        """
                    ),
                    unsafe_allow_html=True,
                )
        return

    # ==========================================================
    # WALKTHROUGH: load selected case
    # ==========================================================
    case = load_case(case_id) or {}

    # --- normalize expected top-level sections ---
    case.setdefault("background", {})
    case.setdefault("technical", {})
    case.setdefault("ethical", {})
    case.setdefault("constraints", [])
    case.setdefault("decision_outcome", {})
    case.setdefault("at_a_glance", {})  # <-- ensure at_a_glance exists

    case["technical"].setdefault("nist_csf_mapping", [])
    case["ethical"].setdefault("tensions", [])
    case["ethical"].setdefault("pfce_analysis", [])
    case["decision_outcome"].setdefault("ethical_implications", [])

    # ==========================================================
    # RESET NAVIGATION WHEN CASE CHANGES
    # ==========================================================
    prev_case = st.session_state.get("cb_prev_case_id")

    # First time a case is loaded, just store it (no rerun)
    if prev_case is None:
        st.session_state["cb_prev_case_id"] = case_id

    # Only reset state if the user actually switched cases (no rerun)
    elif prev_case != case_id:
        st.session_state["cb_step"] = 1
        st.session_state["cb_prev_case_id"] = case_id
        st.session_state["cb_view"] = "walkthrough"
        st.session_state.pop("cb_step_return", None)
        # IMPORTANT: do NOT call _safe_rerun() here

    # ==========================================================
    # VIEW 2: WALKTHROUGH (STEP-BASED)
    # ==========================================================
    if view == "walkthrough":
        st.markdown('<div class="walkthrough-scope"></div>', unsafe_allow_html=True)

        # Ensure step state
        if "cb_step" not in st.session_state:
            st.session_state["cb_step"] = 1
        step = st.session_state["cb_step"]

        def _render_step_tile_html(title, body):
            st.markdown(f"""
            <div class="cb-wt-wrap">
            <div class="cb-wt-tile-anchor"></div>
            <div class="listbox walkthrough-tile">
                <div class="walkthrough-step-title">{title}</div>
                {body}
            </div>
            </div>
            """, unsafe_allow_html=True)


        # -------------------------
        # Walkthrough header (case title)
        # -------------------------
        case_title = case.get("ui_title") or case.get("title") or case_id or ""
        st.markdown(
            f"""
            <div style="text-align:center; margin-top: 0;">
              <h2 style="margin: 0 0 0.25rem 0;">{html.escape(str(case_title))}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Divider under case title
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

        st.progress(step / 9.0)
        st.caption(f"Step {step} of 9")

        if step == 1:
            title = "Technical and Operational Background"
            body = _bullets_html(case["background"].get("technical_operational_background"))
            _render_step_tile_html(title, body)

        elif step == 2:
            title = "Triggering Condition and Key Events"
            body = _bullets_html(case["background"].get("triggering_condition_key_events"))
            _render_step_tile_html(title, body)

        elif step == 3:
            title = "Decision Context"
            body = _bullets_html(case["technical"].get("decision_context"))
            _render_step_tile_html(title, body)

        elif step == 4:
            mapping = case["technical"].get("nist_csf_mapping", [])

            if mapping:
                items = []
                for m in mapping:
                    fn = html.escape(m.get("function", "TBD"))

                    cats = m.get("categories", [])
                    if isinstance(cats, str):
                        cats = [cats]
                    cat_text = html.escape(", ".join(cats) if cats else "TBD")

                    line = f"<li><strong>{fn} — {cat_text}</strong>"

                    if m.get("rationale"):
                        rationale = html.escape(m.get("rationale"))
                        line += f"""
                        <div class="wt-rationale">
                            <span class="wt-rationale-label">Rationale:</span> {rationale}
                        </div>
                        """
                    line += "</li>"

                    items.append(line)

                body = f"<ul class='wt-list'>{''.join(items)}</ul>"
            else:
                body = "<div class='wt-tbd'>TBD</div>"

            # NIST CSF title with tooltip + link (unchanged behavior)
            nist_title = (
                f'<a href="{html.escape(NIST_CSF_URL)}" target="_blank" style="text-decoration: none;">'
                f'  <span title="{html.escape(NIST_CSF_HOVER)}" '
                f'        style="font-weight: 800; text-decoration: underline; cursor: help;">'
                f'    NIST CSF'
                f'  </span>'
                f'</a>'
            )

            title = f"{nist_title} Mapping"

            _render_step_tile_html(title, body)


        elif step == 5:
            tension = case["ethical"].get("tension", [])

            if tension:
                items = []
                for t in tension:
                    desc = html.escape(t.get("description", "TBD"))
                    items.append(f"<li>{desc}</li>")
                body = f"<ul class='wt-list'>{''.join(items)}</ul>"
            else:
                body = "<div class='wt-tbd'>TBD</div>"

            title = "Ethical Tension"

            _render_step_tile_html(title, body)


        elif step == 6:
            pfce_items = case["ethical"].get("pfce_analysis", [])

            # PFCE title tooltip + link (preserved)
            pfce_title = (
                f'<a href="{html.escape(PFCE_URL)}" target="_blank" style="text-decoration: none;">'
                f'  <span title="{html.escape(PFCE_HOVER)}" '
                f'        style="font-weight: 800; text-decoration: underline; cursor: help;">'
                f'    PFCE'
                f'  </span>'
                f'</a>'
            )

            # Body
            if isinstance(pfce_items, list) and pfce_items and isinstance(pfce_items[0], dict):
                items = []
                for p in pfce_items:
                    principle_raw = p.get("principle", "TBD")
                    desc_raw = p.get("description", "TBD")

                    principle = html.escape(str(principle_raw))
                    desc = html.escape(str(desc_raw))

                    definition = PFCE_DEFINITIONS.get(principle_raw, "")
                    if definition:
                        definition_esc = html.escape(str(definition))
                        principle_html = (
                            f"<span title='{definition_esc}' "
                            f"style='font-weight:700; text-decoration: underline; cursor: help;'>"
                            f"{principle}</span>"
                        )
                    else:
                        principle_html = f"<strong>{principle}</strong>"

                    items.append(f"<li>{principle_html}: {desc}</li>")

                body = f"<ul class='wt-list'>{''.join(items)}</ul>"
            else:
                # Fallback: render list/string/None as HTML bullets/text
                body = _bullets_html(pfce_items)

            title = f"{pfce_title} Analysis"

            _render_step_tile_html(title, body)


        elif step == 7:
            constraints = case.get("constraints", [])

            if constraints:
                items = []

                for c in constraints:
                    # Dict form: {type, description, effect_on_decision}
                    if isinstance(c, dict):
                        c_type = html.escape(str(c.get("type", "TBD")))
                        c_desc = html.escape(str(c.get("description", "TBD")))

                        line = f"<li><strong>{c_type}</strong> – {c_desc}"

                        if c.get("effect_on_decision"):
                            effect = html.escape(str(c.get("effect_on_decision")))
                            line += f"<div class='wt-effect'><em>Effect on decision:</em> {effect}</div>"

                        line += "</li>"
                        items.append(line)

                    # String fallback
                    else:
                        items.append(f"<li>{html.escape(str(c))}</li>")

                body = f"<ul class='wt-list'>{''.join(items)}</ul>"
            else:
                body = "<div class='wt-tbd'>TBD</div>"

            title = "Institutional and Governance Constraints"

            _render_step_tile_html(title, body)


        elif step == 8:
            title = "Decision"
            body = _bullets_html(case["decision_outcome"].get("decision"))
            _render_step_tile_html(title, body)


        elif step == 9:
            title = "Outcomes and Implications"
            body = _bullets_html(case["decision_outcome"].get("outcomes_implications"))
            _render_step_tile_html(title, body)


    # NAV CONTROLS
    with st.container():
        # This anchor is what your CSS is scoped to
        st.markdown('<div class="cb-nav-anchor"></div>', unsafe_allow_html=True)
        st.markdown("<!-- CB_NAV_ANCHOR_PRESENT -->", unsafe_allow_html=True)


        col_l, col_r = st.columns(2, gap="large")

        with col_l:
            if step > 1:
                if st.button("◀ Previous", key=f"cb_prev_{case_id}_{step}", use_container_width=False):
                    st.session_state["cb_step"] = step - 1
                    _safe_rerun()
            else:
                st.empty()

        with col_r:
            if step < CB_TOTAL_STEPS:
                if st.button("Next ▶", key=f"cb_next_{case_id}_{step}", use_container_width=False):
                    st.session_state["cb_step"] = step + 1
                    _safe_rerun()
            else:
                st.button("End of Case", key=f"cb_end_{case_id}", disabled=True, use_container_width=False)








