import math
from carbonates.load import load_tables
from carbonates.metrics import reduced_share, volume_cagr


T = load_tables()
M = T["fact_market_size"]


def test_no_duplicate_market_keys():
    assert not M.duplicated(["geography", "category", "year"]).any()


def test_market_year_cap():
    assert M.year.max() == 2025


def test_north_america_2025_share():
    d = reduced_share(M).data
    value = d[(d.geography == "North America") & (d.year == 2025)].iloc[0].reduced_share_pct
    assert math.isclose(value, 32.6, abs_tol=.1)


def test_asia_pacific_cagr():
    d = volume_cagr(M, 2020, 2025).data
    value = d[(d.geography == "Asia Pacific") & (d.category == "Reduced Sugar Carbonates")].iloc[0].volume_cagr_pct
    assert math.isclose(value, 16.7, abs_tol=.1)


def test_components_equal_total_within_rounding():
    p = M[(M.geo_level == "region")].pivot_table(index=["geography", "year"], columns="category", values="volume_million_litres")
    delta = (p["Regular Carbonates"] + p["Reduced Sugar Carbonates"] - p["Carbonates"]).abs()
    assert delta.max() <= .11
