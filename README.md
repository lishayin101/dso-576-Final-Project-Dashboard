# Reduced-Sugar Expansion Dashboard

Run locally:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then open the local URL printed by Streamlit (normally `http://localhost:8501`).

Run acceptance tests with:

```bash
pytest
```

The dashboard uses the generated, synthetic CSVs in `demo_data/`. These files preserve the input schemas and approximate the analysis patterns, but contain no source observations and must not be used as real market data. The repository intentionally contains only these synthetic datasets.
