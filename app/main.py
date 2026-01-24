import sys
from pathlib import Path
import textwrap
import html

# -*- coding: utf-8 -*-
 
# Ensure project root is on sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
 
import streamlit as st

from app import open_ended

# ---------- Page config ----------
st.set_page_config(
    page_title="Municipal Cybersecurity Reasoning Tool",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown(
    """
<style>
html, body{
  overflow: auto !important;
}

/* === FONT === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, .stApp{
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji" !important;
}

/* === TOKENS === */
:root{
  --brand: #378AED;     /* Real-World Incident */
  --brand-2: #55CAFF;   /* Hypothetical Scenario */
  --bg-soft: #0b1020;
  --text-strong: #e5e7eb;
  --text-muted: #94a3b8;
  --card-bg: rgba(255,255,255,0.05);

  /* Layout rails */
  --tile-x-pad: 14px;
  --tile-edge-offset: 5px; /* 4px left stripe + 1px border */

  /* Hover affordance (match buttons) */
  --hover-lift: -3px;
  --hover-shadow-1: 0 0 0 3px rgba(76,139,245,0.65);
  --hover-shadow-2: 0 18px 38px rgba(76,139,245,0.45);
}


/* === APP BACKGROUND === */
div[data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 600px at 10% -10%, rgba(76,139,245,0.15), transparent 60%),
              radial-gradient(900px 500px at 100% 0%, rgba(122,168,255,0.10), transparent 60%),
              var(--bg-soft)
}


/* === HEADER CONTAINER === */
.block-container > div:first-child{
  border-radius: 14px;
  padding: 4px var(--tile-x-pad) 38px var(--tile-x-pad);
  border: 1px solid rgba(255,255,255,0.06);
  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
}


/* === SIDEBAR === */
section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
  border-right: 1px solid rgba(255,255,255,0.10);
  backdrop-filter: blur(6px);
}
/* The whole expander container */
section[data-testid="stSidebar"] .sb-details{
  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03)) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 14px !important;
  padding: 0 !important;
  margin: 0.35rem 0 0.75rem 0 !important;
  overflow: visible !important; /* keeps hover glow + under-glow from clipping */
}
/* === Reference List (inside Tool Foundations) === */
section[data-testid="stSidebar"] .sb-ref-list {
  margin-left: 1rem;
  margin-top: 0.5rem;
}

section[data-testid="stSidebar"] .sb-ref-item {
  margin-bottom: 0.75rem;
}

section[data-testid="stSidebar"] .sb-ref-meta {
  font-size: 0.9rem;
  opacity: 0.85;
}

section[data-testid="stSidebar"] .sb-ref-link {
  font-weight: 800;
  color: white;
  text-decoration: none;
}

/* Indent section body text (matches References indentation) */
section[data-testid="stSidebar"] .sb-section-body {
  margin-left: 1rem;
  margin-top: 0.5rem;
}

section[data-testid="stSidebar"] .sb-details > summary{
  /* layout */
  list-style: none !important;
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  /* visual */
  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03)) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
  /* spacing + typography */
  padding: 12px 14px !important;
  margin: 0 !important;
  color: var(--text-strong) !important;
  font-weight: 800 !important;
  /* behavior */
  cursor: pointer !important;
  /* hover animation */
  transition:
    background-color 0.12s ease,
    border-color 0.12s ease,
    box-shadow 0.12s ease,
    filter 0.12s ease,
    transform 0.12s ease;
}
section[data-testid="stSidebar"] .sb-details > summary:hover{
  background: linear-gradient(
    180deg,
    rgba(255,255,255,0.09),
    rgba(255,255,255,0.05)
  ) !important;
  border-color: rgba(255,255,255,0.24) !important;
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.18),
    0 0 12px rgba(255,255,255,0.18),
    0 0 24px rgba(255,255,255,0.08),
    0 16px 26px rgba(255,255,255,0.12);
  filter: brightness(1.04) !important;
  transform: translateY(-2px);
}
/* flatten summary bottom corners when open */
section[data-testid="stSidebar"] .sb-details[open] > summary{
  border-bottom-left-radius: 0 !important;
  border-bottom-right-radius: 0 !important;
}
/* Sidebar chevron */
section[data-testid="stSidebar"] .sb-details > summary::-webkit-details-marker{ display:none !important; }
section[data-testid="stSidebar"] .sb-details > summary::marker{ content:"" !important; }
section[data-testid="stSidebar"] .sb-details > summary::before{
  content: ">";
  font-size: 1rem;
  font-weight: 800;
  line-height: 1;
  opacity: 0.8;
  margin-top: -1px;
  transition: transform 0.12s ease, opacity 0.12s ease;
}
section[data-testid="stSidebar"] .sb-details[open] > summary::before{
  transform: rotate(90deg);
}
section[data-testid="stSidebar"] .sb-details-body .sb-section{
  font-weight: 800 !important;
  padding: 0 !important;
  line-height: 1.2;
  color: #ffffff !important;
  text-decoration: underline !important;
  text-decoration-color: rgba(255,255,255,0.85) !important;
  text-decoration-thickness: 2px !important;
  text-underline-offset: 4px !important;

  margin: 0 !important;             /* remove space under header */
  margin-top: 0.75rem !important;   /* add space above header */
}
/* Match the visual inset seen in mode-tile details bodies */
section[data-testid="stSidebar"] .sb-details-body{
  padding: 12px 12px !important; 
  padding-left: 6px !important;          /* match mode tiles */
  background: rgba(255,255,255,0.03) !important;
}

/* Allow long sidebar text/URLs to wrap */
section[data-testid="stSidebar"] .sb-details-body a,
section[data-testid="stSidebar"] .sb-details-body p,
section[data-testid="stSidebar"] .sb-details-body li,
section[data-testid="stSidebar"] .sb-details-body span{
  overflow-wrap: anywhere !important;
  word-break: break-word !important;
  white-space: normal !important;
}

section[data-testid="stSidebar"] details.sb-details[open] > .sb-details-body {
  margin-top: 0.6rem !important;
  padding-bottom: 0.2rem !important;
}

section[data-testid="stSidebar"] div[data-testid="stMarkdown"]{
  margin-bottom: 0.2rem !important;
}

section[data-testid="stSidebar"] .sb-details-body .sb-p{
  margin: 0 0 0.4rem 0 !important;  /* small gap after paragraphs */
}

/* === BUTTONS === */
div[data-testid="stButton"] > button:not([kind="secondary"]){
  box-sizing: border-box !important;
  padding: 0.7rem 1rem !important;
  border-radius: 12px !important;
  cursor: pointer !important;
  background: rgba(255,255,255,0.06) !important;
  color: var(--text-strong) !important;
  border: 1px solid rgba(76,139,245,0.55) !important;
  box-shadow:
    0 0 0 1px rgba(76,139,245,0.35),
    0 10px 20px rgba(76,139,245,0.35) !important;
  transition: transform .06s ease, box-shadow .15s ease, filter .15s ease !important;
  white-space: nowrap !important;
}
div[data-testid="stButton"] > button:not([kind="secondary"]):hover{
  transform: translateY(-3px) !important;
  cursor: pointer !important;
  box-shadow:
    0 0 0 3px rgba(76,139,245,0.65),
    0 18px 38px rgba(76,139,245,0.45) !important;
  border-color: rgba(76,139,245,0.95) !important;
  filter: brightness(1.05) !important;
}
/* Secondary Buttons */
div[data-testid="stButton"] > button[kind="secondary"]{
  box-sizing: border-box !important;
  padding: 0.7rem 1rem !important;
  border-radius: 12px !important;
  cursor: pointer !important;
  background: rgba(255,255,255,0.06) !important;
  color: var(--text-strong) !important;
  border: 1px solid rgba(76,139,245,0.55) !important;
  box-shadow:
    0 0 0 1px rgba(76,139,245,0.35),
    0 10px 20px rgba(76,139,245,0.35) !important;
  transition: transform .06s ease, box-shadow .15s ease, filter .15s ease !important;
  white-space: nowrap !important;
}
div[data-testid="stButton"] > button[kind="secondary"]:hover{
  transform: translateY(-3px) !important;
  cursor: pointer !important;
  box-shadow:
    0 0 0 3px rgba(76,139,245,0.65),
    0 18px 38px rgba(76,139,245,0.45) !important;
  border-color: rgba(76,139,245,0.95) !important;
  filter: brightness(1.05) !important;
}
div[data-testid="stButton"] > button:active{
  transform: translateY(-1px) !important;
  box-shadow:
    0 0 0 1px rgba(76,139,245,0.45),
    0 8px 16px rgba(76,139,245,0.30) !important;
}
div[data-testid="stButton"] > button:disabled{
  opacity: 0.55 !important;
  background: rgba(255,255,255,0.10) !important;
  border: 1px solid rgba(255,255,255,0.22) !important;
  color: var(--text-strong) !important;
  box-shadow: none !important;
  transform: none !important;
  filter: none !important;
}
div[data-testid="stButton"] > button:disabled:hover{
  transform: none !important;
  cursor: default !important;
  box-shadow: none !important;
  border-color: rgba(255,255,255,0.22) !important;
  filter: none !important;
}
/* Keyboard focus only (no mouse click outline) */
div[data-testid="stButton"] > button:focus-visible{
  outline: none !important;
  box-shadow:
    0 0 0 3px rgba(76,139,245,0.75),
    0 0 0 6px rgba(76,139,245,0.25) !important;
}

textarea::placeholder {
  color: rgba(229,231,235,0.55);
  font-size: 0.95rem;
}
.lp-section{
  font-weight: 800;
  margin-top: 0.75rem;
  margin-bottom: 0.25rem;
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: 4px;
}
.lp-button-wrap{
  display: flex;
  justify-content: center;
  margin-top: 1.5rem;
  padding-bottom: 0.5rem;
}

/* Landing page list indent
.lp-list{
  margin-left: 1rem !important;    
  padding-left: 0.5rem !important; 
}

/* === OPEN-ENDED STEP 1: EXAMPLES EXPANDER (MATCH OTHER DROPDOWNS) === */
.oe-example-expander{
  background: linear-gradient(
    180deg,
    rgba(255,255,255,0.06),
    rgba(255,255,255,0.03)
  ) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
  padding: 0 !important;
  overflow: hidden !important; /* keeps body "inside the tile" */
}

/* Summary/header row */
.oe-example-expander > summary{
  list-style: none !important;
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;

  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03)) !important;
  border: 0 !important;                 /* container provides border */
  border-radius: 12px !important;

  color: var(--text-strong) !important;
  font-weight: 500 !important;

  padding: 12px 14px !important;
  padding-left: 34px !important;        /* room for chevron */
  margin: 0 !important;

  cursor: pointer !important;
  position: relative !important;

  transition:
    background-color 0.12s ease,
    filter 0.12s ease,
    transform 0.12s ease;
}

/* Subtle hover (secondary affordance) */
.oe-example-expander > summary:hover{
  background: linear-gradient(
    180deg,
    rgba(255,255,255,0.09),
    rgba(255,255,255,0.05)
  ) !important;
  filter: brightness(1.03) !important;
  transform: translateY(-1px) !important;
}

/* Hide default marker */
.oe-example-expander > summary::-webkit-details-marker{ display:none !important; }
.oe-example-expander > summary::marker{ content:"" !important; }

/* Chevron matches your other dropdowns */
.oe-example-expander > summary::before{
  content: ">" !important;
  font-weight: 500 !important;
  font-size: 1rem !important;
  line-height: 1.45 !important;
  opacity: 0.8 !important;

  position: absolute !important;
  left: 12px !important;
  top: 50% !important;
  transform: translateY(-50%) rotate(0deg) !important;
  transition: transform 0.12s ease, opacity 0.12s ease !important;
}

.oe-example-expander[open] > summary::before{
  transform: translateY(-50%) rotate(90deg) !important;
}

/* Flatten bottom corners when open (so summary merges into body) */
.oe-example-expander[open] > summary{
  border-bottom-left-radius: 0 !important;
  border-bottom-right-radius: 0 !important;
}

/* Body stays inside the same tile */
.oe-example-body{
  padding: 12px 14px !important;
  margin: 0 !important;
  border-top: 1px solid rgba(255,255,255,0.08) !important;
  background: rgba(255,255,255,0.03) !important;
}


/* === INPUTS === */
input, textarea, select, .stTextInput input, .stTextArea textarea{
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  color: var(--text-strong) !important;
  border-radius: 10px !important;
}
label, .stRadio, .stSelectbox, .stMultiSelect, .stExpander{
  color: var(--text-strong) !important;
}


/* === CARD TILES === */
.listbox{
  background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04));
  border-left: 4px solid var(--brand);
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: 0 10px 24px rgba(0,0,0,0.25);
  padding: 12px 14px;
  border-radius: 12px;
  margin: 0 0 8px;
  transition: transform .06s ease, box-shadow .15s ease, border-color 0.12s ease, background 0.12s ease;
}
.listbox, .listbox *{ color: var(--text-strong) !important; }
section-note, .tile-hook { color: var(--text-muted) !important; }


/* === HIDE STREAMLIT CHROME === */
header[data-testid="stHeader"]{ background: transparent; }
footer, #MainMenu{ visibility: hidden; }
/* Hide header anchor icons */
div[data-testid="stMarkdownContainer"] h1 a,
div[data-testid="stMarkdownContainer"] h2 a,
div[data-testid="stMarkdownContainer"] h3 a,
div[data-testid="stMarkdownContainer"] h4 a,
div[data-testid="stMarkdownContainer"] h5 a,
div[data-testid="stMarkdownContainer"] h6 a{
  display: none !important;
  visibility: hidden !important;
}
button[aria-label*="Copy link"],
button[title*="Copy link"]{
  display: none !important;
}

.wt-rationale{
  margin-top: 8px;
  padding-left: 14px;
  font-size: 0.92rem;
  line-height: 1.45;
  color: rgba(229,231,235,0.75);
}

.wt-rationale-label{
  font-weight: 600;
  color: rgba(229,231,235,0.85);
}

/* === WALKTHROUGH TILES: NOT CLICKABLE ==== */
.listbox.walkthrough-tile{
  cursor: default !important;
  margin-top: 12px;
  margin-bottom: 12px !important;
}
.walkthrough-step-title{
  display: inline-block;     
  font-size: 1.25rem;
  letter-spacing: 0.02em;
  font-weight: 700;
  line-height: 1.45;
  margin: 0 0 0.6rem 0;
  color: var(--text-strong);
}
/* kill the hover/active "clickable" affordance */
.listbox.walkthrough-tile:hover,
.listbox.walkthrough-tile:active{
  cursor: default !important;
  transform: none !important;
  border-color: rgba(255,255,255,0.10) !important;   /* normal */
  box-shadow: 0 10px 24px rgba(0,0,0,0.25) !important; /* normal */
}
/* Optional polish: soften walkthrough tiles slightly */
.listbox.walkthrough-tile{
  box-shadow: 0 8px 18px rgba(0,0,0,0.22) !important;
}
:root{ --disclaimer-h: 56px; }
/* Reserve space so content never hides behind the footer */
div[data-testid="stMainBlockContainer"]{
  padding-bottom: calc(var(--disclaimer-h) + 16px) !important;
}
.disclaimer-overlay{
  position: fixed !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100% !important;
  max-width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  z-index: 2147483647 !important; /* go nuclear */
  pointer-events: none !important;
}
/* Prevent any ancestor from turning fixed into “fixed inside container” */
div[data-testid="stAppViewContainer"],
div[data-testid="stMain"],
div[data-testid="stMainBlockContainer"],
main{
  transform: none !important;
  filter: none !important;
  perspective: none !important;
}
/* The actual bar */
.disclaimer-footer{
  height: var(--disclaimer-h) !important;
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  background: rgba(11,16,32,0.92) !important;
  border-top: 1px solid rgba(255,255,255,0.10) !important;
  color: rgba(229,231,235,0.75) !important;
  font-size: 0.85rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.01em !important;
  margin: 0 !important;
  padding: 0 12px !important; /* small side padding */
  text-align: center !important;
  pointer-events: none !important;
}


/* === WALKTHROUGH NAV (CB + OE) — CLEAN + RELIABLE === */

/* Scope: only the nav row that contains the anchor */
div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
div[data-testid="stHorizontalBlock"]{
  width: 100% !important;
  display: flex !important;
  align-items: stretch !important;
  padding: 0 calc(var(--tile-x-pad) - var(--tile-edge-offset)) !important;
  margin-top: 12px !important;
}

/* Columns must expand to fill the row */
div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
div[data-testid="stColumn"]{
  flex: 1 1 0 !important;
  width: 100% !important;
  display: flex !important;
}

/* Column wrapper must stretch so the lane has space */
div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
div[data-testid="stColumn"] > div{
  flex: 1 1 auto !important;
  width: 100% !important;
  display: flex !important;
}

/* --- LEFT LANE: pin to left rail (wrapper row axis + inner column axis) --- */
div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
div[data-testid="stHorizontalBlock"]
div[data-testid="stColumn"]:first-child > div{
  justify-content: flex-start !important;
  padding-left: 0 !important;
}

div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
div[data-testid="stHorizontalBlock"]
div[data-testid="stColumn"]:first-child{
  padding-left: 0 !important;
}

/* Left lane true-left align (column flex => align-items controls horizontal) */
div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
div[data-testid="stHorizontalBlock"]
div[data-testid="stColumn"]:first-child
div[data-testid="stVerticalBlock"]{
  align-items: flex-start !important;
}

/* --- RIGHT LANE: pin to right rail (wrapper row axis + inner column axis) --- */
div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
div[data-testid="stHorizontalBlock"]
div[data-testid="stColumn"]:last-child > div{
  justify-content: flex-end !important;
  padding-right: 0 !important;
}

div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
div[data-testid="stHorizontalBlock"]
div[data-testid="stColumn"]:last-child{
  padding-right: 0 !important;
}

/* Right lane pinned right — actual lane is the inner stVerticalBlock in the right column */
div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
div[data-testid="stHorizontalBlock"]
div[data-testid="stColumn"]:last-child
div[data-testid="stVerticalBlock"]{
  width: 100% !important;
  display: flex !important;

  justify-content: flex-start !important;  /* vertical: top (neutral) */
  align-items: flex-end !important;        /* horizontal: RIGHT */
}

/* Keep nav buttons pill-sized */
div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
div[data-testid="stButton"] > button{
  width: auto !important;
  min-width: unset !important;
}

div[data-testid="stVerticalBlock"]:has(.walkthrough-scope){
  padding-left: var(--tile-x-pad) !important;
  padding-right: var(--tile-x-pad) !important;
}

/* Stack only when truly narrow */
@media (max-width: 520px){
  div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
  div[data-testid="stColumn"] > div{
    justify-content: stretch !important;
  }

  /* On narrow screens, don't force right-pin; let buttons go full-width */
  div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
  div[data-testid="stHorizontalBlock"]
  div[data-testid="stColumn"]:last-child
  div[data-testid="stVerticalBlock"]{
    justify-content: stretch !important;
    align-items: stretch !important;
  }

  div[data-testid="stVerticalBlock"]:has(:is(.oe-nav-anchor))
  div[data-testid="stButton"] > button{
    width: 100% !important;
    min-width: 100% !important;
  }
}

/* === CSF STEP SECTION CARD === */
.csf-section{
  border: 0 !important;
  background: transparent !important;
  padding: 0 !important;
  margin: 0 0 0.75rem 0 !important;
}

/* === SECTION WRAPPERS (CSF + PFCE) === */
div[data-testid="stContainer"]:has(
  :is(
    .csf-func-anchor,
    .csf-cat-anchor,
    .csf-sub-anchor,
    .pfce-tags-anchor,
    .pfce-principles-anchor,
    .pfce-analysis-anchor,
    .pfce-tension-anchor
  )
),
div[data-testid="stVerticalBlock"]:has(
  :is(
    .csf-func-anchor,
    .csf-cat-anchor,
    .csf-sub-anchor,
    .pfce-tags-anchor,
    .pfce-principles-anchor,
    .pfce-analysis-anchor,
    .pfce-tension-anchor
  )
){
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 14px;
  background: linear-gradient(
    180deg,
    rgba(255,255,255,0.05),
    rgba(255,255,255,0.02)
  );
  padding: 16px 18px;
  margin: 0 0 1rem 0;
}
</style>
""",
    unsafe_allow_html=True,
)


def html_block(s: str) -> str:
    # Prevent Markdown from treating indented HTML as a code block.
    return "\n".join(line.lstrip() for line in textwrap.dedent(s).splitlines())


def _open_sidebar_once():
    # Only try once per browser session (Streamlit session_state)
    if st.session_state.get("_sidebar_opened_once", False):
        return
    st.session_state["_sidebar_opened_once"] = True

    st.markdown(
        """
        <script>
        (function () {
          const doc = window.parent.document;

          function isCollapsed(sidebarEl) {
            if (!sidebarEl) return false;
            const w = sidebarEl.getBoundingClientRect().width;
            // When collapsed, sidebar width is usually very small (often < ~80px)
            return w < 120;
          }

          function findToggleButton() {
            // Try multiple selectors (Streamlit changes these)
            const selectors = [
              'button[data-testid="collapsedControl"]',
              'button[aria-label="Expand sidebar"]',
              'button[aria-label="Collapse sidebar"]',
              'button[title="Expand sidebar"]',
              'button[title="Collapse sidebar"]',
              // Fallback: any header button with "sidebar" in aria-label/title
              'button[aria-label*="sidebar"]',
              'button[title*="sidebar"]'
            ];

            for (const sel of selectors) {
              const btn = doc.querySelector(sel);
              if (btn) return btn;
            }
            return null;
          }

          function tryOpen(attempt) {
            const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
            const toggle = findToggleButton();

            if (sidebar && toggle && isCollapsed(sidebar)) {
              toggle.click();
              return;
            }

            // Retry while Streamlit finishes layout
            if (attempt < 20) {
              setTimeout(() => tryOpen(attempt + 1), 120);
            }
          }

          tryOpen(0);
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_disclaimer_footer():
    txt = "This tool is designed for research and demonstration purposes"

    st.markdown(
        f"""
        <div class="disclaimer-overlay">
          <div class="disclaimer-footer">
            {html.escape(txt)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_landing_page():
    st.markdown(
        """
        <div class="listbox walkthrough-tile landing-tile">
          <div style="text-align:center;">
            <div class="walkthrough-step-title">Before You Begin</div>
          </div>

          <div class="lp-section">Purpose of the Tool</div>
          <ul class="tight-list lp-list">
            <li>Provides a structured reasoning tool for municipal cybersecurity decision-makers</li>
            <li>Supports decisions where technical considerations and ethical obligations intersect</li>
            <li>Makes stakeholders, trade-offs, and competing obligations explicit at the point of decision</li>
          </ul>

          <div class="lp-section">How the Tool Supports Reasoning</div>
          <ul class="tight-list lp-list">
            <li>Guides you through a step-by-step reasoning sequence focused on a specific cybersecurity decision</li>
            <li>Uses the NIST Cybersecurity Framework (CSF) 2.0 to situate the technical context</li>
            <li>Uses the Principlist Framework for Cybersecurity Ethics (PFCE) to surface ethically significant considerations</li>
            <li>Supports deliberate examination of trade-offs and tensions when obligations cannot be fully satisfied at the same time</li>
            <li>Produces a documented record of reasoning explaining what was decided and why</li>
          </ul>

          <div class="lp-section">What the Tool Does Not Do</div>
          <ul class="tight-list lp-list">
            <li>Recommend, rank, or weigh actions</li>
            <li>Determine the “correct” decision</li>
            <li>Replace policy, legal guidance, or professional judgment</li>
          </ul>

          <div class="lp-btn-anchor"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Button rendered by Streamlit (keeps your exact button styling)
    btn_col = st.columns([1, 1, 1])[1]
    with btn_col:
        if st.button("Begin Reasoning Process", key="begin_reasoning"):
            st.session_state["landing_complete"] = True
            st.session_state["oe_step"] = 1
            st.rerun()


def render_app_header(show_banner: bool = True):
    # --- Back buttons (secondary nav) ---
    show_back = st.session_state.get("landing_complete", False)

    in_open_ended = st.session_state.get("oe_step", 0) > 0

    if st.session_state.get("landing_complete", False) and in_open_ended:
        if st.button("← Back to Start", key="back_to_start", type="secondary"):
            st.session_state["landing_complete"] = False
            st.session_state["oe_step"] = 0
            st.rerun()

    # --- Tool banner (select pages only) ---
    if show_banner:
        st.markdown(
            """
            <div style='text-align:center;'>
              <h1>🛡️ Municipal Cybersecurity Reasoning Tool</h1>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def render_divider():
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

def main():
    # ---------- SESSION STATE DEFAULTS ----------
    if "landing_complete" not in st.session_state:
        st.session_state["landing_complete"] = False

    if "oe_step" not in st.session_state:
        st.session_state["oe_step"] = 0

    _open_sidebar_once()

    # ---------- URL PARAM MODE ENTRY (tile click) ----------
    try:
        qp = st.query_params
        start_qp = qp.get("start", None)

        if start_qp == "walkthrough":
            st.session_state["landing_complete"] = True
            if st.session_state.get("oe_step", 0) == 0:
                st.session_state["oe_step"] = 1
            st.query_params.clear()
    except Exception:
        pass

    # ---------- SIDEBAR (ALWAYS) ----------
    import textwrap

    def sidebar_divider():
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

    def html_block(s: str) -> str:
        return "\n".join(line.lstrip() for line in textwrap.dedent(s).splitlines())

    with st.sidebar:
        sidebar_divider()

        st.markdown(
            "<h3 style='font-weight:700;'>Tool Overview</h3>",
            unsafe_allow_html=True,
        )

        st.markdown(
            html_block(
                """
                <details class="sb-details">
                  <summary>ℹ️ About This Tool</summary>
                  <div class="sb-details-body">

                    <span class="sb-section">Who It Is For</span>

                    <div class="sb-section-body">
                      <div class="sb-p">
                        This tool is designed for municipal cybersecurity decision-makers responsible for evaluating and justifying cybersecurity decisions.
                      </div>
                    </div>

                    <span class="sb-section">Reasoining Structure</span>

                    <div class="sb-section-body">
                      <div class="sb-p">
                        This tool structures ethical and technical reasoning at a defined cybersecurity decision point. It is intended to support reflective judgment, not to prescribe actions or outcomes.                   
                      </div>
                      </div>
                      <div class="sb-section-body">
                      <div class="sb-p">
                        The reasoning sequence draws on the NIST Cybersecurity Framework (CSF) 2.0 for technical context and the Principlist Framework for Cybersecurity Ethics (PFCE) for ethical analysis.
                      </div>
                    </div>

                    <span class="sb-section">Disclaimer</span>

                    <div class="sb-section-body">
                      <div class="sb-p">
                        Outputs generated by this tool represent structured reasoning, not authoritative guidance, and should be interpreted alongside organizational policy, legal requirements, and professional judgment.                  
                      </div>
                    </div>

                  </div>
                </details>
                """
            ),
            unsafe_allow_html=True,
        )

        sidebar_divider()

        st.markdown(
            "<h3 style='font-weight:700;'>Tool Foundations</h3>",
            unsafe_allow_html=True,
        )

        st.markdown(
            html_block(
                """
                <details class="sb-details">
                  <summary>📚 References</summary>
                  <div class="sb-details-body">

                    <div class="sb-p">
                      This tool draws on two established frameworks that inform how cybersecurity decisions are structured and examined:                   
                    </div>

                    <div class="sb-ref-list">

                      <div class="sb-ref-item">
                        <a href="https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf"
                          target="_blank"
                          title="Learn more about the NIST Cybersecurity Framework (CSF) 2.0"
                          style="
                            font-weight:800;
                            color: white;
                            text-decoration: none;
                          ">
                          NIST Cybersecurity Framework (CSF) 2.0
                        </a><br>
                        <span class="sb-ref-meta">National Institute of Standards and Technology (2024)</span>
                      </div>

                      <div class="sb-ref-item">
                        <a href="https://doi.org/10.1016/j.cose.2021.102382"
                          target="_blank"
                          title="Learn more about the Principlist Framework for Cybersecurity Ethics"
                          style="
                            font-weight:800;
                            color: white;
                            text-decoration: none;
                          ">
                          Principlist Framework for Cybersecurity Ethics (PFCE)
                        </a><br>
                        <span class="sb-ref-meta">Formosa, Paul; Michael Wilson; Deborah Richards (2021)</span>
                      </div>

                    </div>
                
                  </div>
                </details>
                """
            ),
            unsafe_allow_html=True,
        )

        sidebar_divider()


    # ---------- HEADER ----------
    in_walkthrough = st.session_state.get("oe_step", 0) > 0
    render_app_header(show_banner=not in_walkthrough)


    # Divider rules:
    # - Always show divider on select pages (under banner)
    # - On Open-Ended walkthrough, main.py must show divider under the step title (which will be in open_ended.py or main)
    if not in_walkthrough:
        render_divider()


    # ---------- LANDING GATE ----------
    if not st.session_state.get("landing_complete", False):
        _render_landing_page()
        render_disclaimer_footer()
        return
    
    # ---------- ACTIVE WORKFLOW ----------
    open_ended.render_open_ended()


if __name__ == "__main__":
    main()
