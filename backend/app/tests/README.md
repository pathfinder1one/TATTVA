# Test layout

Run deterministic local unit and security checks with `python -m pytest app/tests/unit -q` from `backend/` after installing `requirements-dev.txt`.

The `integration/` and `evaluation/` suites need local MongoDB/Qdrant services and synthetic fixtures; add those when exercising the full pipeline. Keep all fixtures synthetic.
