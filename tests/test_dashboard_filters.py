import json
from pathlib import Path

from streamlit.testing.v1 import AppTest


def _chart_spec(app, index):
    return json.loads(app.get("plotly_chart")[index].proto.spec)


def test_shared_filters_update_the_intended_dashboard_views():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path).run(timeout=60)
    assert not app.exception

    region_filter = app.selectbox(key="dashboard_region")
    year_filter = app.slider(key="dashboard_year")
    assert [item.label for item in app.selectbox].count("Region") == 1

    initial_regional_sweetener = _chart_spec(app, 6)
    initial_global_sweetener = _chart_spec(app, 7)
    initial_regular_company = _chart_spec(app, 3)
    initial_reduced_company = _chart_spec(app, 4)
    initial_company_movement = _chart_spec(app, 5)

    region_filter.set_value("Latin America").run(timeout=60)
    assert _chart_spec(app, 6) != initial_regional_sweetener
    assert _chart_spec(app, 7) == initial_global_sweetener
    assert _chart_spec(app, 3) != initial_regular_company
    assert _chart_spec(app, 4) != initial_reduced_company
    assert _chart_spec(app, 5) != initial_company_movement
    assert [item.value for item in app.subheader] == [
        "Regular Carbonates in Latin America",
        "Reduced-sugar Carbonates in Latin America",
        "Company Share Movement in Latin America",
    ]

    regional_sweetener_after_region = _chart_spec(app, 6)
    global_sweetener_after_region = _chart_spec(app, 7)
    regular_company_after_region = _chart_spec(app, 3)
    reduced_company_after_region = _chart_spec(app, 4)
    year_filter.set_value(2020).run(timeout=60)
    assert _chart_spec(app, 6) != regional_sweetener_after_region
    assert _chart_spec(app, 7) != global_sweetener_after_region
    assert _chart_spec(app, 3) != regular_company_after_region
    assert _chart_spec(app, 4) != reduced_company_after_region
