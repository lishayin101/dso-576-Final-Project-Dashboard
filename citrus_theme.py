"""Citrus Pop presentation helpers; no data loading or metric calculations."""
from html import escape
from pathlib import Path

import streamlit as st

CREAM = "#f7f5e9"
PAPER = "#fffef8"
INK = "#24392a"
MUTED = "#5d6a58"
BORDER = "#d9dfcb"
GREEN = "#446b31"
LIME = "#c8ee60"
ORANGE = "#d45a32"
REGULAR = "#a3b286"
OTHER_REGION = "#b7b09b"
GROWTH_SCALE = [[0, "#bf5336"], [.25, "#e99f6a"], [.5, PAPER], [.75, "#a3b286"], [1, GREEN]]
COMPANY_COLORS = [GREEN, "#e99f6a", REGULAR, OTHER_REGION, ORANGE, LIME,
                  "#6d8b50", "#f0c49a", "#7c934b", "#d8c7a2", "#ad7449",
                  "#a6c654", "#314f2a", "#cc8a61"]
SWEETENER_COLORS = {"traditional": GREEN, "natural_alternative": "#e99f6a",
                    "artificial_alternative": REGULAR, "fruit_based": OTHER_REGION,
                    "other": ORANGE}


def apply_theme():
    css = (Path(__file__).parent / "assets" / "citrus.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('''<div class="citrus-wordmark"><span class="citrus-bubble" aria-hidden="true"></span>Citrus Pop</div>
<div class="citrus-nav-label">MARKET INTELLIGENCE</div>
<nav class="citrus-nav" aria-label="Dashboard sections">
<a href="#opportunity" target="_self"><span>01</span>Opportunity</a>
<a href="#compare" target="_self"><span>02</span>Region comparison</a>
<a href="#demand" target="_self"><span>03</span>Demand trends</a>
<a href="#competition" target="_self"><span>04</span>Competition</a>
<a href="#sweeteners" target="_self"><span>05</span>Sweetener mix</a></nav>''', unsafe_allow_html=True)


def brand_header():
    st.markdown('''<div class="citrus-brandbar"><div class="citrus-wordmark"><span class="citrus-bubble" aria-hidden="true"></span>Citrus Pop</div><span class="citrus-tagline">Less sugar. More possibility.</span></div>
<div class="citrus-hero"><div class="citrus-hero-copy"><div class="citrus-eyebrow">The expansion edit</div><h1>Big fizz.<br><em>Fresh opportunities.</em></h1><p>Where should reduced-sugar beverages expand next? Explore the markets shaping a lighter kind of soda.</p></div><div class="citrus-can-scene" aria-hidden="true"><span class="citrus-spark">✳</span><div class="citrus-can"><b>good<br>things<br>bubble.</b><small>Reduced sugar soda</small><span class="citrus-orb"></span></div></div></div>''', unsafe_allow_html=True)


def section_header(number, anchor, title, subtitle):
    st.markdown(f'<div class="citrus-section" id="{escape(anchor, quote=True)}"><span class="citrus-number">{number:02d}</span><div><h2>{escape(title)}</h2><p>{escape(subtitle)}</p></div></div>', unsafe_allow_html=True)


def render_chart(fig, **kwargs):
    """Apply visual defaults without touching trace values or control scope."""
    fig.update_layout(
        paper_bgcolor=PAPER, plot_bgcolor=PAPER,
        font=dict(family="Arial, Helvetica, sans-serif", color=INK, size=12),
        title_font=dict(family="Arial, Helvetica, sans-serif", color=INK, size=16),
        legend=dict(font=dict(color=MUTED, size=11), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=PAPER, bordercolor=BORDER, font=dict(color=INK)),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=MUTED, activecolor=GREEN),
    )
    fig.update_xaxes(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER)
    fig.update_yaxes(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER)
    st.plotly_chart(fig, theme=None, **kwargs)


def footer():
    st.markdown('<div class="citrus-footer"><span>Citrus Pop / The expansion edit</span><span>Synthetic demo data · Off-trade market scan</span></div>', unsafe_allow_html=True)
