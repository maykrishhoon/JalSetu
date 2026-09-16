"""
JalSetu Command Console — Streamlit Prototype
------------------------------------------------
A Python-based interactive prototype of the JalSetu dashboard: the JE-level
control view for the conjunctive canal-groundwater management system on the
Lower Ganga Canal tail-end, Prayagraj.

Run locally with:  streamlit run jalsetu_app.py
"""

import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page config + palette
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="JalSetu Command Console",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PRIMARY = "#1B4965"
SECONDARY = "#5FA8C4"
ACCENT = "#E0923D"
CRITICAL = "#D9603B"
TEXT_DARK = "#16303F"
TEXT_MUTED = "#5B7686"
BG_CARD = "#FFFFFF"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'IBM Plex Sans', sans-serif;
}}
.jt-mono {{ font-family: 'JetBrains Mono', monospace; }}

.block-container {{ padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1200px; }}

.jt-header {{
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 0.4rem;
}}
.jt-title {{ font-size: 1.7rem; font-weight: 700; color: {PRIMARY}; }}
.jt-badge {{
    background: #EAF2F5; color: {PRIMARY}; font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; font-weight: 600; padding: 3px 10px; border-radius: 5px;
    letter-spacing: 0.04em; margin-left: 10px;
}}
.jt-sub {{ color: {TEXT_MUTED}; font-size: 0.92rem; }}

div[data-testid="stMetric"] {{
    background: {BG_CARD}; border: 1px solid #E3EDF1; border-radius: 10px;
    padding: 14px 16px 10px 16px; box-shadow: 0 1px 3px rgba(20,50,70,0.06);
}}
div[data-testid="stMetricLabel"] {{ color: {TEXT_MUTED} !important; font-size: 0.78rem !important; }}
div[data-testid="stMetricValue"] {{ font-family: 'JetBrains Mono', monospace; color: {PRIMARY}; }}

.jt-alert-ok {{ color: {TEXT_DARK}; font-size: 0.86rem; padding: 3px 0; }}
.jt-alert-warn {{ color: {CRITICAL}; font-size: 0.86rem; padding: 3px 0; font-weight: 600; }}
.jt-alert-time {{ font-family: 'JetBrains Mono', monospace; color: {TEXT_MUTED}; font-size: 0.74rem; margin-right: 8px; }}

.jt-footer {{ color: {TEXT_MUTED}; font-size: 0.75rem; text-align: center; margin-top: 1.2rem; }}
.jt-recbox {{
    background: #FCF1E3; border: 1px solid {ACCENT}; border-radius: 8px;
    padding: 10px 14px; font-family: 'JetBrains Mono', monospace; font-size: 0.86rem;
    color: #8A5A1E; margin-top: 6px;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Baseline "telemetry" — illustrative, for demonstration purposes
# ---------------------------------------------------------------------------
HOURS = ["00:00", "02:00", "04:00", "06:00", "08:00", "10:00", "12:00",
         "14:00", "16:00", "18:00", "20:00", "22:00"]
BASE_HEAD = [39.2, 40.1, 38.7, 41.3, 42.0, 40.8, 39.6, 40.4, 41.7, 40.9, 39.8, 40.2]
BASE_TAIL = [34.1, 34.6, 33.9, 35.8, 36.4, 35.9, 34.7, 35.2, 36.1, 35.6, 34.9, 35.3]

GW_DAYS = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
BASE_GW = [14.18, 14.21, 14.19, 14.24, 14.22, 14.27, 14.25]
CRISIS_GW = [14.18, 14.21, 14.19, 14.24, 14.30, 14.41, 14.52]

GATES = [
    {"id": "head", "name": "Head Regulator", "loc": "Narora\u2013Bulandshahr Offtake", "base_pos": 62},
    {"id": "mid1", "name": "Mid Regulator", "loc": "Fatehpur Reach", "base_pos": 55},
    {"id": "mid2", "name": "Mid Regulator", "loc": "Kaushambi Reach", "base_pos": 58},
    {"id": "tail", "name": "Tail Chak Regulator", "loc": "Soraon\u2013Handia, Prayagraj", "base_pos": 41},
]

BASE_ALERTS = [
    ("06:02", "Routine telemetry sync completed \u2014 0% data loss", "ok"),
    ("03:15", "Sensor heartbeat check \u2014 all nodes nominal", "ok"),
    ("Yesterday 22:40", "Gate position verified \u2014 Tail Chak Regulator", "ok"),
]
CRISIS_ALERTS = [
    ("LIVE", "Tail Chak Regulator auto-adjusted to 68% \u2014 ratio recovering toward 1:1.16", "ok"),
    ("LIVE", "LSTM forecast: 68% deficit probability within 36h \u2014 recommending gate adjustment", "warn"),
    ("LIVE", "Groundwater stress detected \u2014 Tail Chak piezometer trending down", "warn"),
] + BASE_ALERTS

RECOMMENDATION = "Recommend +14% opening at Tail Chak Regulator \u2014 forecast window 36h"

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "crisis" not in st.session_state:
    st.session_state.crisis = False
if "gate_modes" not in st.session_state:
    st.session_state.gate_modes = {g["id"]: "Auto" for g in GATES}
if "manual_pos" not in st.session_state:
    st.session_state.manual_pos = {g["id"]: g["base_pos"] for g in GATES}

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
left, right = st.columns([3, 1])
with left:
    st.markdown(
        f"""<div class="jt-header">
                <span class="jt-title">💧 JALSETU <span style="font-weight:400;font-size:1.1rem;">Command Console</span></span>
                <span class="jt-badge">PHASE 1 &middot; PILOT</span>
            </div>
            <div class="jt-sub">LGC Tail-End Command &middot; Prayagraj, Uttar Pradesh</div>""",
        unsafe_allow_html=True,
    )
with right:
    st.markdown(
        f"""<div style="text-align:right; padding-top:6px;">
                <span class="jt-mono" style="color:{TEXT_MUTED}; font-size:0.85rem;">
                {datetime.now().strftime('%H:%M:%S')} &middot; {'ATTENTION' if st.session_state.crisis else 'NOMINAL'}
                </span>
            </div>""",
        unsafe_allow_html=True,
    )

st.write("")

# ---------------------------------------------------------------------------
# Top metrics
# ---------------------------------------------------------------------------
ratio = 1.58 if st.session_state.crisis else 1.14
gw_now = CRISIS_GW[-1] if st.session_state.crisis else BASE_GW[-1]
risk = 68 if st.session_state.crisis else 12

m1, m2, m3 = st.columns(3)
m1.metric("Head-to-Tail Ratio (target 1:1.10\u20131.20)", f"1 : {ratio:.2f}",
          delta=None if not st.session_state.crisis else "worsened from 1:1.14", delta_color="inverse")
m2.metric("Groundwater Table \u2014 Tail Chak Piezometer", f"{gw_now:.2f} mbgl",
          delta=None if not st.session_state.crisis else f"+{gw_now - BASE_GW[-1]:.2f} m", delta_color="inverse")
m3.metric("AI Deficit Forecast \u2014 Next 48h", f"{risk}%",
          delta=None if not st.session_state.crisis else "Elevated \u2014 was 12%", delta_color="inverse")

if st.session_state.crisis:
    st.markdown(f'<div class="jt-recbox">🤖 {RECOMMENDATION}</div>', unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
c1, c2 = st.columns([3, 2])

with c1:
    with st.container(border=True):
        st.markdown("**Canal Discharge \u2014 Head vs Tail (m\u00b3/s)**")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=HOURS, y=BASE_HEAD, name="Head", line=dict(color=PRIMARY, width=2.5)))
        fig.add_trace(go.Scatter(x=HOURS, y=BASE_TAIL, name="Tail", line=dict(color=ACCENT, width=2.5)))
        fig.update_layout(
            height=230, margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#EEF3F5"),
            font=dict(family="IBM Plex Sans", color=TEXT_MUTED, size=11),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    with st.container(border=True):
        st.markdown("**Groundwater Trend (mbgl)**")
        gw_series = CRISIS_GW if st.session_state.crisis else BASE_GW
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=GW_DAYS, y=gw_series, fill="tozeroy",
            line=dict(color=SECONDARY, width=2.5),
            fillcolor="rgba(95,168,196,0.18)",
        ))
        fig2.update_layout(
            height=230, margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#EEF3F5", range=[min(BASE_GW + CRISIS_GW) - 0.05, max(BASE_GW + CRISIS_GW) + 0.05]),
            font=dict(family="IBM Plex Sans", color=TEXT_MUTED, size=11),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

st.write("")

# ---------------------------------------------------------------------------
# Gate control row
# ---------------------------------------------------------------------------
st.markdown("**Gate Control**")
gate_cols = st.columns(4)
for col, g in zip(gate_cols, GATES):
    with col:
        with st.container(border=True):
            st.markdown(f"<span style='font-weight:600; font-size:0.88rem;'>{g['name']}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:{TEXT_MUTED}; font-size:0.76rem;'>{g['loc']}</span>", unsafe_allow_html=True)

            auto_adjusted = st.session_state.crisis and g["id"] == "tail"
            position = g["base_pos"]
            if auto_adjusted:
                position = 68

            mode = st.toggle("Manual override", key=f"mode_{g['id']}",
                              value=(st.session_state.gate_modes[g["id"]] == "Manual"))
            st.session_state.gate_modes[g["id"]] = "Manual" if mode else "Auto"

            if mode:
                position = st.slider("Position %", 0, 100, st.session_state.manual_pos[g["id"]],
                                      key=f"slider_{g['id']}", label_visibility="collapsed")
                st.session_state.manual_pos[g["id"]] = position
                st.markdown(f"<span class='jt-mono' style='color:{ACCENT}; font-size:0.8rem;'>MANUAL \u00b7 {position}%</span>", unsafe_allow_html=True)
            else:
                st.progress(position / 100)
                tag = " \u2699\ufe0f auto-adjusted" if auto_adjusted else ""
                st.markdown(f"<span class='jt-mono' style='color:{PRIMARY}; font-size:0.8rem;'>AUTO \u00b7 {position}%{tag}</span>", unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------------------------
# Alert log + action buttons
# ---------------------------------------------------------------------------
log_col, action_col = st.columns([2, 1])

with log_col:
    with st.container(border=True):
        st.markdown("**Alert Log**")
        alerts = CRISIS_ALERTS if st.session_state.crisis else BASE_ALERTS
        for t, text, level in alerts[:5]:
            css_class = "jt-alert-warn" if level == "warn" else "jt-alert-ok"
            icon = "\u26a0\ufe0f" if level == "warn" else "\u2705"
            st.markdown(
                f'<div class="{css_class}"><span class="jt-alert-time">{t}</span>{icon} {text}</div>',
                unsafe_allow_html=True,
            )

with action_col:
    with st.container(border=True):
        st.markdown("**Controls**")
        if st.button("🚨 Simulate Dry-Spell Event", use_container_width=True, disabled=st.session_state.crisis):
            with st.spinner("Running LSTM forecast..."):
                time.sleep(1.3)
            st.session_state.crisis = True
            st.rerun()
        if st.button("🔄 Reset to Normal", use_container_width=True):
            st.session_state.crisis = False
            st.session_state.gate_modes = {g["id"]: "Auto" for g in GATES}
            st.rerun()

st.markdown(
    '<div class="jt-footer">Demonstrator uses simulated telemetry for presentation purposes '
    '&middot; JalSetu Phase 1 Pilot, Prayagraj &middot; Built with Python + Streamlit</div>',
    unsafe_allow_html=True,
)

