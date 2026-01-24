import streamlit as st
from datetime import datetime
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
import textwrap


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


# Practitioner-friendly NIST CSF 2.0 function prompts for Open-Ended Mode
CSF_FUNCTION_OPTIONS = {
    "GV": {
        "label": "GOVERN (GV)",
        "prompt": (
            "Are you establishing, reviewing, or implementing cybersecurity policy, "
            "governance expectations, or organizational risk strategy?"
        ),
    },
    "ID": {
        "label": "IDENTIFY (ID)",
        "prompt": (
            "Are you assessing vulnerabilities, reviewing system risks, or determining "
            "what assets or stakeholders are affected?"
        ),
    },
    "PR": {
        "label": "PROTECT (PR)",
        "prompt": (
            "Are you applying safeguards or controls to prevent unauthorized access or "
            "data exposure?"
        ),
    },
    "DE": {
        "label": "DETECT (DE)",
        "prompt": (
            "Have you observed indicators of compromise or suspicious behavior that "
            "require investigation?"
        ),
    },
    "RS": {
        "label": "RESPOND (RS)",
        "prompt": (
            "Has a cybersecurity incident been detected and you must take action "
            "immediately?"
        ),
    },
    "RC": {
        "label": "RECOVER (RC)",
        "prompt": (
            "Are you restoring systems, data, or services after an incident and deciding "
            "what to prioritize or how transparent to be?"
        ),
    },
}


OE_STEP_TITLES = {
    1: "Scenario Description",
    2: "Decision Point",
    3: "Decision Context Classification",
    4: "NIST CSF Mapping",
    5: "PFCE Analysis and Ethical Tension",
    6: "Institutional and Governance Constraints",
    7: "Decision (and documented rationale)",
}
OE_TOTAL_STEPS = max(OE_STEP_TITLES.keys())
assert set(OE_STEP_TITLES.keys()) == set(range(1, OE_TOTAL_STEPS + 1)), "Step numbers must be contiguous."


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

PFCE_PROMPTS = {
    "Beneficence": "Could this decision affect human well-being or access to essential services?",
    "Non-maleficence": "Could this decision foreseeably cause harm (directly or indirectly)?",
    "Autonomy": "Could this decision constrain people’s ability to make informed choices about how they are affected?",
    "Justice": "Could impacts or protections be distributed unevenly across groups or neighborhoods?",
    "Explicability": "Is accountability, transparency, or explainability central to this decision?",
}


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

def _render_open_header(step: int, total_steps: int):
    step_title = OE_STEP_TITLES.get(step, OE_STEP_TITLES[1])

    st.markdown(
        f"""
        <div style="text-align:center; margin-top: 0;">
          <h2 style="margin: 0 0 0.1rem 0;">{step_title}</h2>
          <div style="
            color: rgba(229,231,235,0.70);
            font-size: 0.95rem;
            margin: 0 0 0.75rem 0;
          ">
            Step {step} of {total_steps}
          </div>
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
    if "oe_step" not in st.session_state:
        st.session_state["oe_step"] = 1

    total_steps = OE_TOTAL_STEPS
    step = int(st.session_state["oe_step"])

    step = max(1, min(step, total_steps))
    st.session_state["oe_step"] = step

    _render_open_header(step, total_steps)
    st.progress(step / float(total_steps))


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
            What is the specific operational decision being considered?:
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
    # STEP 3: Decision Context Classification
    # ==========================================================
    elif step == 3:
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
            What type of decision context best describes the s?:
            </div>
            """,
            unsafe_allow_html=True
        )

        # Text box with ONLY guidance as placeholder
        decision_context = st.text_area(
            "Decision Context",
            key="oe_decision_context",
            height=120,
            placeholder="(Example: Following a suspected ransomware incident, some municipal systems have been restored while others remain offline. A decision is required on whether to further isolate network segments to limit potential spread, which would disrupt services that are currently functioning. The decision must be made quickly with limited information about the scope of compromise.)",
            label_visibility="collapsed",
        )

    # ==========================================================
    # STEP 4: NIST CSF
    # ==========================================================
    elif step == 4:
        # ---------- CSF Function ----------
        with st.container():
            st.markdown('<div class="csf-func-anchor"></div>', unsafe_allow_html=True)

            csf_section_open(
                "NIST CSF Function",
                "Within your current decision context, where are you operating in the cybersecurity process?"
            )

    # ==========================================================
    # STEP 5: PFCE + TENSION
    # ==========================================================
    elif step == 5:

        # ---------- PFCE principle triage (multi-select) ----------
        with st.container():
            st.markdown('<div class="pfce-principles-anchor"></div>', unsafe_allow_html=True)

            csf_section_open(
                "PFCE Principle Triage",
                "Use the prompts below to identify which PFCE principles are implicated by this decision context. "
                "This does not prescribe outcomes; it structures ethical reasoning."
            )

            selected_pfce_ids = []
            pfce_ids = list(PFCE_DEFINITIONS.keys())  # e.g., ["Beneficence", "Non-maleficence", ...]

            # Keep list scannable; definitions available on demand
            with st.container(height=280):
                for pid in pfce_ids:
                    prompt = PFCE_PROMPTS.get(pid, "").strip()
                    definition = PFCE_DEFINITIONS.get(pid, "").strip()

                    checked = st.checkbox(
                        f"**{pid}** — {prompt}" if prompt else f"**{pid}**",
                        key=f"oe_pfce_{pid}",
                    )
                    if checked:
                        selected_pfce_ids.append(pid)

                    # Optional definition without clutter
                    if definition:
                        with st.expander(f"View {pid} definition", expanded=False):
                            st.write(definition)

            st.session_state["oe_pfce_principles"] = selected_pfce_ids

            if selected_pfce_ids:
                st.info(f"Selected PFCE principle(s): **{', '.join(selected_pfce_ids)}**")
            else:
                st.info("Selected PFCE principles: **None selected**")

            csf_section_close()

        if not st.session_state.get("oe_pfce_principles"):
            st.warning("Select at least one PFCE principle to continue to analysis and ethical tension.")
        else:


            # ---------- PFCE analysis (now grounded in selected principles) ----------
            with st.container():
                st.markdown('<div class="pfce-analysis-anchor"></div>', unsafe_allow_html=True)

                csf_section_open(
                    "PFCE Analysis",
                    "In 2–4 sentences, explain what is ethically significant about this decision context using the selected principles as reference points."
                )

                st.text_area(
                    "PFCE analysis",
                    key="oe_pfce_analysis",
                    height=160,
                    placeholder=(
                        "Example: Containment actions may reduce spread but disrupt essential services; "
                        "limited visibility constrains defensible scoping; impacts may fall unevenly across residents."
                    ),
                    label_visibility="collapsed",
                )

                csf_section_close()

            # ---------- Ethical tension (two justified obligations) ----------
            with st.container():
                st.markdown('<div class="pfce-tension-anchor"></div>', unsafe_allow_html=True)

                csf_section_open(
                    "Ethical Tension",
                    "State the central tension as two justified obligations that cannot both be fully fulfilled."
                )

                a = st.text_area(
                    "Obligation A",
                    key="oe_tension_a",
                    height=90,
                    placeholder="Example: Maintain continuity of essential services to prevent harm to residents.",
                )

                b = st.text_area(
                    "Obligation B",
                    key="oe_tension_b",
                    height=90,
                    placeholder="Example: Contain the threat quickly to prevent wider compromise and longer disruption.",
                )

                st.session_state["oe_ethical_tension"] = f"{a.strip()}  ⟷  {b.strip()}".strip(" ⟷ ")

                csf_section_close()


    # ==========================================================
    # STEP 6: CONSTRAINTS
    # ==========================================================
    elif step == 6:
        _render_step_tile_html(
            "Document constraints that shape or limit feasible actions or justification.",
        )

        st.text_area(
            "Other constraints (optional)",
            key="oe_constraints_other",
            height=90,
        )

    # ==========================================================
    # STEP 7: DECISION + OUTPUT 
    # ==========================================================
    elif step == 7:
        _render_step_tile_html(
            "Record the decision in operational terms, then generate a structured rationale for demonstration purposes.",
        )

        st.text_area(
            "Decision (operational)",
            key="oe_decision",
            height=120,
            placeholder="Example: Disconnect additional systems while confirming scope; preserve critical service workflows via manual workarounds.",
        )


    # NAV CONTROLS
    with st.container():
        st.markdown('<div class="oe-nav-anchor"></div>', unsafe_allow_html=True)

        col_l, col_r = st.columns(2, gap="large")

        with col_l:
            if step > 1:
                if st.button("◀ Previous", key=f"oenav_prev_{step}", use_container_width=False):
                    st.session_state["oe_step"] = step - 1
                    _safe_rerun()
            else:
                st.empty()

        with col_r:
            if step < total_steps:
                if st.button("Next ▶", key=f"oenav_next_{step}", use_container_width=False):
                    st.session_state["oe_step"] = step + 1
                    _safe_rerun()
            else:
                if st.button("Generate PDF", key="oe_generate_pdf", use_container_width=False):
                    st.session_state["oe_generate"] = True
                    _safe_rerun()


