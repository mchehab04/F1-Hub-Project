# TODO: orchestration entrypoint — runs fetch_jolpica + fetch_fastf1 and
# writes the combined, cleaned data into the SQLite tables. Intended to be
# run as a one-off/incremental batch job (e.g. `python -m etl.build_db`),
# never invoked from the FastAPI request path.
