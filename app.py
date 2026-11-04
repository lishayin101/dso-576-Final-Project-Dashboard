from html import escape
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from carbonates.load import load_tables
from carbonates.metrics import (REGIONS, company_share_change_pp, company_share_pie_data,
                                 region_summary, sweetener_mix, top_company)

st.set_page_config(page_title="Reduced-Sugar Expansion", page_icon="◒", layout="wide")
st.markdown("""<style>
.block-container{max-width:1440px;padding-top:1.4rem}.control-card{background:#f5f8fc;border:1px solid #dbe3ee;
border-radius:14px;padding:10px 16px;margin:4px 0 22px}.formula{background:#f8fafc;border-left:4px solid #0d366b;
padding:9px 12px;border-radius:3px;color:#334155;font-size:.88rem}.small{color:#64748b;font-size:.84rem}
[data-testid=stMetric]{background:#f6f8fb;border:1px solid #e5eaf1;border-radius:12px;padding:14px}
h1,h2,h3{letter-spacing:-.025em}</style>""", unsafe_allow_html=True)


@st.cache_data
def tables():
    return load_tables()


def formula(text):
    st.markdown(f'<div class="formula"><b>Formula:</b> {escape(text)}</div>', unsafe_allow_html=True)


T = tables()
market, companies = T["fact_market_size"], T["fact_company_share"]
region_market = market[(market.geo_level == "region") & market.geography.isin(REGIONS)]
years = sorted(region_market.year.dropna().astype(int).unique())

st.title("Where should reduced-sugar beverages expand next?")
st.caption("Executive market scan · Synthetic demo data · Off-trade volume (million litres)")
st.markdown('<div class="control-card"><b>Dashboard-wide filters</b><br><span class="small">Year updates every view. Region updates the demand-trend focus and the left sweetener pie. Controls that apply to only one analysis are placed directly above that analysis.</span></div>', unsafe_allow_html=True)
f1, f2, _ = st.columns([1, 1, 2])
with f1:
    year = st.slider("Year · applies dashboard-wide", min(years), max(years), max(years))
with f2:
    region = st.selectbox("Region · trend and regional sweetener focus", REGIONS, index=REGIONS.index("North America"))

# V1 — the display grouping is illustrative; analytical values come from region rows.
region_red = region_market[region_market.category == "Reduced Sugar Carbonates"].pivot(
    index="year", columns="geography", values="volume_million_litres")
growth_all = region_red.pct_change(fill_method=None) * 100
finite = growth_all.to_numpy()[np.isfinite(growth_all.to_numpy())]
limit = max(5, int(np.ceil(np.max(np.abs(finite)) / 5) * 5))
growth = growth_all.loc[year] if year in growth_all.index else pd.Series(index=REGIONS, dtype=float)
display = T["country_display_regions"].copy()
display["growth"] = display.display_region.map(growth)

st.header("1. Year-over-year reduced-sugar growth by region")
st.caption("Colour applies each synthetic regional total to an illustrative country grouping. Country values are never aggregated to calculate the regional metric.")
fig = go.Figure(go.Choropleth(
    locations=display.iso3, locationmode="ISO-3", z=display.growth,
    customdata=display[["geography", "display_region"]],
    hovertemplate="<b>%{customdata[0]}</b><br>Display region: %{customdata[1]}<br>Regional YoY growth: %{z:+.1f}%<extra></extra>",
    colorscale=[[0,"#b2182b"],[.25,"#ef8a62"],[.5,"#f7f7f7"],[.75,"#6da7ec"],[1,"#0d366b"]],
    zmin=-limit, zmax=limit, zmid=0, marker_line_color="white", marker_line_width=.35,
    colorbar=dict(title="YoY volume<br>growth (%)", tickvals=[-limit,-limit/2,0,limit/2,limit],
                  ticktext=[f"-{limit}",f"-{limit/2:g}","0",f"+{limit/2:g}",f"+{limit}"])))
coords={"North America":(-102,49),"Latin America":(-61,-17),"Western Europe":(2,51),
        "Eastern Europe":(26,56),"Asia Pacific":(105,35),"Australasia":(135,-25),
        "Middle East and Africa":(31,11)}
labels=["N/A" if pd.isna(growth.get(r)) else f"{growth.get(r):+.1f}%" for r in REGIONS]
fig.add_trace(go.Scattergeo(lon=[coords[r][0] for r in REGIONS], lat=[coords[r][1] for r in REGIONS],
    mode="text", text=[f"<b>{r}</b><br><b>{v}</b>" for r,v in zip(REGIONS,labels)],
    textfont=dict(size=11,color="#172235",shadow="1px 1px 1px white"), hoverinfo="skip"))
fig.update_geos(showframe=False, showcoastlines=True, coastlinecolor="#b9c1cc", projection_type="natural earth",
                 showland=True, landcolor="#edf0f3")
fig.update_layout(height=520, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)
formula("Year-over-year growth (%) = (Reduced-sugar volume in selected year ÷ Reduced-sugar volume in prior year − 1) × 100")
if year == min(years):
    st.info(f"{year} has no {year-1} baseline. Growth is N/A, never zero; n = 0 regions.")
else:
    st.caption(f"n = {growth.notna().sum()} regions · Fixed symmetric legend is calculated once from the largest absolute regional YoY change across 2011–2025.")

# V3 — graph-specific baseline lives here, not in global navigation.
st.header("2. Region comparison")
valid_starts = [y for y in years if y < year]
start = st.selectbox("Comparison start year · affects this table only", valid_starts or [year],
                     index=(valid_starts.index(2020) if 2020 in valid_starts else max(0, len(valid_starts)-1)))
summary = region_summary(market, year, start)
d = summary.data[["geography","reduced_share_pct","reduced_volume_ml","regular_volume_ml",
                  "reduced_cagr_pct","regular_cagr_pct","share_change_pp"]].copy()
d.columns=["Region","Reduced share (%)","Reduced volume (M L)","Regular volume (M L)",
           f"Reduced CAGR {start}–{year} (%)",f"Regular CAGR {start}–{year} (%)","Share change (pp)"]
st.dataframe(d.sort_values("Reduced share (%)", ascending=False), hide_index=True, use_container_width=True,
             column_config={c:st.column_config.NumberColumn(format="%.1f") for c in d.columns[1:]})
formula(f"Reduced share = Reduced ÷ Carbonates × 100; CAGR = (V{year} ÷ V{start})^(1 ÷ ({year} − {start})) − 1; share change (pp) = share{year} − share{start}")
st.caption(f"n = {summary.n} regions · Units: million litres; growth percentages and percentage-point changes are distinct metrics.")

# V4
st.header("3. Demand trends")
c1,c2=st.columns(2)
with c1:
    trend=region_market[(region_market.geography==region)&region_market.category.isin(["Regular Carbonates","Reduced Sugar Carbonates"])]
    f=px.line(trend,x="year",y="volume_million_litres",color="category",markers=True,
              labels={"year":"Year","volume_million_litres":"Volume (million litres)","category":""},
              title=f"Regular vs reduced · {region}", color_discrete_map={"Regular Carbonates":"#94a3b8","Reduced Sugar Carbonates":"#1769aa"})
    f.add_vline(x=year,line_dash="dot",line_color="#172235"); f.update_layout(height=430,hovermode="x unified",legend=dict(orientation="h",y=-.2))
    st.plotly_chart(f,use_container_width=True)
    st.markdown('<div class="formula"><b>Measure:</b> Generated demo volume in million litres; missing years remain gaps.</div>',unsafe_allow_html=True)
    st.caption(f"n = {trend.volume_million_litres.notna().sum()} reported observations")
with c2:
    p=region_market.pivot_table(index=["geography","year"],columns="category",values="volume_million_litres",aggfunc="first").reset_index()
    p["share"]=p["Reduced Sugar Carbonates"]/p["Carbonates"].where(p["Carbonates"]>0)*100
    f=go.Figure()
    for r in REGIONS:
        q=p[p.geography==r]; f.add_trace(go.Scatter(x=q.year,y=q.share,name=r,mode="lines",
            line=dict(width=4 if r==region else 1.3,color="#1769aa" if r==region else "#c3cad3"),connectgaps=False))
    f.add_vline(x=year,line_dash="dot",line_color="#172235"); f.update_layout(title="Reduced-sugar share across regions",
        xaxis_title="Year",yaxis_title="Reduced share (%)",height=430,hovermode="x unified",legend=dict(orientation="h",y=-.2))
    st.plotly_chart(f,use_container_width=True)
    formula("Reduced-sugar share (%) = Reduced-sugar volume ÷ Total carbonates volume × 100")
    st.caption(f"n = {p.share.notna().sum()} region-years")

# V2 — graph-specific controls only.
st.header("4. Company share: regular vs reduced sugar")
share_years=sorted(companies.year.dropna().astype(int).unique())
share_year=max([y for y in share_years if y<=year],default=min(share_years))
if share_year != year: st.info(f"Company-share data has no {year} row; showing the latest available year not after it: {share_year}.")

def company_panel(container, title, category, key):
    with container:
        st.subheader(title)
        geo=st.selectbox("Region · this pie only",REGIONS,index=REGIONS.index(region),key=key)
        result=company_share_pie_data(companies,geo,category,share_year)
        if result.data.empty:
            st.info("No company data for this selection in the current dataset")
            return
        f=px.pie(result.data,names="company",values="volume_share_pct",hole=.48,color_discrete_sequence=px.colors.qualitative.Safe)
        f.update_traces(textposition="inside",textinfo="percent",hovertemplate="%{label}<br>%{value:.1f}%<extra></extra>")
        f.update_layout(height=390,margin=dict(t=10,b=10,l=5,r=5),legend=dict(orientation="h"))
        st.plotly_chart(f,use_container_width=True)
        formula("Company share (%) = company retail volume ÷ category retail volume × 100 (synthetic demo estimate); Total row excluded")
        top=top_company(companies,geo,category,share_year).data
        st.caption(f"n = {result.n} reported companies · Top non-aggregate company: {top.iloc[0].company if not top.empty else 'N/A'} · {result.note}")

left,right=st.columns(2)
company_panel(left,"Regular carbonates","Regular Carbonates","regular_geo")
company_panel(right,"Reduced-sugar carbonates","Reduced Sugar Carbonates","reduced_geo")

st.subheader("Company-share movement")
m1,m2,m3,m4=st.columns(4)
with m1: move_geo=st.selectbox("Region · movement only",REGIONS,index=REGIONS.index(region),key="move_geo")
with m2: move_cat=st.selectbox("Category · movement only",["Regular Carbonates","Reduced Sugar Carbonates"],index=1)
move_years=sorted(companies[(companies.geography==move_geo)&(companies.category==move_cat)].year.dropna().astype(int).unique())
with m3: move_start=st.selectbox("Start year",move_years[:-1],index=0)
with m4:
    end_options=[y for y in move_years if y>move_start]
    move_end=st.selectbox("End year",end_options,index=(end_options.index(2025) if 2025 in end_options else len(end_options)-1))
change=company_share_change_pp(companies,move_geo,move_cat,move_start,move_end)
if change.data.empty: st.info("No companies are reported in both selected years.")
else:
    f=px.bar(change.data,x="share_change_pp",y="company",orientation="h",color="share_change_pp",
             color_continuous_scale=["#b2182b","#f7f7f7","#0d366b"],color_continuous_midpoint=0,
             text=change.data.share_change_pp.map(lambda v:f"{v:+.1f} pp"),labels={"share_change_pp":"Change (pp)","company":""})
    f.update_layout(height=410,coloraxis_showscale=False); f.update_traces(textposition="outside",cliponaxis=False)
    st.plotly_chart(f,use_container_width=True)
    formula(f"Company share change (percentage points) = share in {move_end} − share in {move_start}; only companies reported in both years")
    st.caption(f"n = {change.n} companies · {change.note}")

# Revised V5 — side-by-side regional/global pies; year affects both, region only the left.
if "fact_ingredient" in T:
    st.header("5. Sweetener breakdown: selected region vs world")
    st.caption("The paired pies make the regional composition comparable with the global benchmark. The dashboard year affects both; the global pie is never affected by the region filter.")
    ingredients=T["fact_ingredient"]
    sweet_year=min(max(year,2020),2025)
    if sweet_year!=year: st.info(f"Sweetener coverage is 2020–2025; showing {sweet_year} for this section.")
    include=st.toggle("Include Fruit Juice and Coconut Water",False,help="Excluded by default because fruit ingredients dominate tonnage and can obscure high-intensity sweeteners.")
    regional=sweetener_mix(ingredients,region,sweet_year,include)
    world=sweetener_mix(ingredients,"World",sweet_year,include)
    palette={"traditional":"#0d366b","natural_alternative":"#6da7ec","artificial_alternative":"#ef8a62","fruit_based":"#79a86b","other":"#b8a6cf"}
    a,b=st.columns(2)
    for container,title,result in [(a,f"{region} · {sweet_year}",regional),(b,f"Global · {sweet_year}",world)]:
        with container:
            q=result.data.copy(); q["label"]=q.sweetener_group.str.replace("_"," ").str.title()
            f=px.pie(q,names="label",values="tonnage_share_pct",hole=.43,title=title,
                     color="sweetener_group",color_discrete_map=palette)
            f.update_traces(textposition="inside",textinfo="percent",hovertemplate="%{label}<br>%{value:.1f}%<extra></extra>")
            f.update_layout(height=420,legend=dict(orientation="h"),margin=dict(t=50,b=10,l=5,r=5))
            st.plotly_chart(f,use_container_width=True)
            st.caption(f"n = {result.n} reported ingredient rows")
    formula("Sweetener-group tonnage share (%) = tonnes for a sweetener group ÷ total reported sweetener tonnes in the same geography and year × 100")
    st.warning("Tonnage is not sweetness-equivalent: high-intensity sweeteners can be hundreds of times sweeter than sugar. Fruit-based ingredients are excluded by default and should not be interpreted as equivalent sweetness.")

with st.expander("About the data, contracts, and acceptance rules"):
    st.markdown("""
**Files and units.** These tables are generated synthetic demo data. `fact_market_size.csv` is geography × category × year in **million litres** (2011–2025). `fact_company_share.csv` is geography × category × company × year in **retail-volume percentage share** (2017–2026). `fact_ingredient.csv` is geography × ingredient × year in **tonnes** and `% Breakdown` (2020–2025).

**Country scope.** Analytical market-selection views use exactly seven synthetic region rows. Country-to-display-region mappings are illustrative map metadata only; country values are never summed to reproduce a region.

**Reusable contracts.** Loaders return tidy DataFrames. Metric functions accept DataFrames rather than reading files and return `MetricResult(data, n, note)`. Required keys are geography/category/year for market size, geography/category/company/year for company share, and geography/ingredient/year for ingredients. Missing values propagate as `NaN`, never zero.

**Acceptance checks.** No duplicate metric keys; no market-size year after 2025; Regular + Reduced matches Carbonates within rounding tolerance; North America 2025 reduced share is approximately 32.6%; Asia Pacific 2020–2025 reduced CAGR is approximately 16.7%; every on-screen calculation shows its formula and record count; the global sweetener pie responds to year but not region.

**Caveats.** All values are synthetic and intended only to demonstrate the dashboard; they are not actual market measurements and should not be used for business decisions. Ingredient `% Breakdown` is a share of all ingredients including water and does not sum to 100 across sweeteners. Company shares are rounded to 0.1%.
""")
