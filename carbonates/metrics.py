from dataclasses import dataclass
import numpy as np
import pandas as pd

REGIONS = ["North America", "Latin America", "Western Europe", "Eastern Europe",
           "Asia Pacific", "Australasia", "Middle East and Africa"]


@dataclass
class MetricResult:
    data: pd.DataFrame
    n: int
    note: str = ""


def _regions(market: pd.DataFrame) -> pd.DataFrame:
    return market[(market["geo_level"] == "region") & market["geography"].isin(REGIONS)].copy()


def reduced_share(market: pd.DataFrame) -> MetricResult:
    """Contract: region/category/year volumes -> region/year/reduced_share_pct."""
    p = _regions(market).pivot_table(index=["geography", "year"], columns="category",
                                     values="volume_million_litres", aggfunc="first").reset_index()
    denominator = p.get("Carbonates", pd.Series(index=p.index, dtype=float)).where(lambda x: x > 0)
    p["reduced_share_pct"] = p.get("Reduced Sugar Carbonates") / denominator * 100
    out = p[["geography", "year", "reduced_share_pct"]]
    return MetricResult(out, int(out.reduced_share_pct.notna().sum()), "Reduced / Carbonates × 100")


def volume_cagr(market: pd.DataFrame, start_year: int, end_year: int) -> MetricResult:
    """Contract: positive endpoint volumes -> geography/category CAGR percentage."""
    if end_year <= start_year:
        return MetricResult(pd.DataFrame(columns=["geography", "category", "volume_cagr_pct"]), 0,
                            "end year must be after start year")
    d = _regions(market)
    p = d[d.year.isin([start_year, end_year])].pivot_table(
        index=["geography", "category"], columns="year", values="volume_million_litres", aggfunc="first")
    p["volume_cagr_pct"] = np.nan
    if start_year in p and end_year in p:
        ok = p[start_year].gt(0) & p[end_year].notna()
        p.loc[ok, "volume_cagr_pct"] = ((p.loc[ok, end_year] / p.loc[ok, start_year]) **
                                         (1 / (end_year - start_year)) - 1) * 100
    out = p.reset_index()[["geography", "category", "volume_cagr_pct"]]
    return MetricResult(out, int(out.volume_cagr_pct.notna().sum()), f"{start_year}–{end_year}")


def share_change_pp(market: pd.DataFrame, start_year: int, end_year: int) -> MetricResult:
    s = reduced_share(market).data
    p = s[s.year.isin([start_year, end_year])].pivot(index="geography", columns="year", values="reduced_share_pct")
    p["share_change_pp"] = np.nan
    if start_year in p and end_year in p:
        p["share_change_pp"] = p[end_year] - p[start_year]
    out = p.reset_index()[["geography", "share_change_pp"]]
    return MetricResult(out, int(out.share_change_pp.notna().sum()), "end share − start share")


def region_summary(market: pd.DataFrame, year: int, start_year: int) -> MetricResult:
    d = _regions(market)
    p = d[d.year == year].pivot_table(index="geography", columns="category",
                                      values="volume_million_litres", aggfunc="first")
    out = pd.DataFrame(index=REGIONS)
    out["reduced_volume_ml"] = p.get("Reduced Sugar Carbonates")
    out["regular_volume_ml"] = p.get("Regular Carbonates")
    out["carbonates_volume_ml"] = p.get("Carbonates")
    out["reduced_share_pct"] = out.reduced_volume_ml / out.carbonates_volume_ml.where(out.carbonates_volume_ml > 0) * 100
    c = volume_cagr(market, start_year, year).data
    for category, column in [("Reduced Sugar Carbonates", "reduced_cagr_pct"),
                             ("Regular Carbonates", "regular_cagr_pct")]:
        q = c[c.category == category].set_index("geography").volume_cagr_pct
        out[column] = q
    out["share_change_pp"] = share_change_pp(market, start_year, year).data.set_index("geography").share_change_pp
    out = out.rename_axis("geography").reset_index()
    return MetricResult(out, int(out.reduced_share_pct.notna().sum()), f"selected year {year}; baseline {start_year}")


def company_share_pie_data(companies: pd.DataFrame, geography: str, category: str, year: int) -> MetricResult:
    d = companies[(companies.geography == geography) & (companies.category == category) &
                  (companies.year == year) & (~companies.is_total.astype(bool))].copy()
    missing = d[d.volume_share_pct.isna()].company.tolist()
    out = d[d.volume_share_pct.notna()][["company", "volume_share_pct"]].sort_values("volume_share_pct", ascending=False)
    return MetricResult(out, len(out), "Not reported: " + (", ".join(missing) if missing else "none"))


def top_company(companies: pd.DataFrame, geography: str, category: str, year: int) -> MetricResult:
    d = companies[(companies.geography == geography) & (companies.category == category) &
                  (companies.year == year) & (~companies.is_total.astype(bool)) &
                  (~companies.company.isin(["Others", "Private Label"])) & companies.volume_share_pct.notna()]
    out = d.nlargest(1, "volume_share_pct")[["company", "volume_share_pct"]]
    return MetricResult(out, len(out), "aggregate companies excluded")


def company_share_change_pp(companies: pd.DataFrame, geography: str, category: str,
                            start_year: int, end_year: int) -> MetricResult:
    d = companies[(companies.geography == geography) & (companies.category == category) &
                  (companies.year.isin([start_year, end_year])) & (~companies.is_total.astype(bool))]
    p = d.pivot_table(index="company", columns="year", values="volume_share_pct", aggfunc="first")
    if start_year not in p or end_year not in p:
        return MetricResult(pd.DataFrame(columns=["company", "share_change_pp"]), 0, "both years required")
    p = p[p[start_year].notna() & p[end_year].notna()].copy()
    p["share_change_pp"] = p[end_year] - p[start_year]
    out = p.reset_index()[["company", "share_change_pp"]].sort_values("share_change_pp")
    return MetricResult(out, len(out), f"{len(out)} companies reported in both years")


def sweetener_mix(ingredients: pd.DataFrame, geography: str, year: int,
                  include_fruit: bool = False) -> MetricResult:
    d = ingredients[(ingredients.geography == geography) & (ingredients.year == year) & ingredients.tonnes.notna()].copy()
    if not include_fruit:
        d = d[d.sweetener_group != "fruit_based"]
    g = d.groupby("sweetener_group", as_index=False).tonnes.sum()
    total = g.tonnes.sum()
    g["tonnage_share_pct"] = g.tonnes / total * 100 if total > 0 else np.nan
    return MetricResult(g, len(d), f"{geography}, {year}")
