from pathlib import Path
import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "demo_data"


def load_tables(data_dir: Path | str = DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load demo CSV contracts without changing missing values.

    Required files: fact_market_size.csv, fact_company_share.csv,
    dim_geography.csv and country_display_regions.csv. Ingredient files are
    optional; the UI hides that section when they are absent.
    """
    root = Path(data_dir)
    required = ["fact_market_size", "fact_company_share", "dim_geography", "country_display_regions"]
    tables = {}
    for name in required:
        path = root / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing required demo table: {path}")
        tables[name] = pd.read_csv(path)
    for name in ["fact_ingredient", "dim_ingredient", "validation_checks", "cleaning_audit"]:
        path = root / f"{name}.csv"
        if path.exists():
            tables[name] = pd.read_csv(path)
    for name in ["fact_market_size", "fact_company_share", "fact_ingredient"]:
        if name in tables:
            tables[name]["year"] = pd.to_numeric(tables[name]["year"], errors="coerce").astype("Int64")
    return tables
