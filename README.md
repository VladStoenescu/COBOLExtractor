# COBOL Extractor

Python Streamlit MVP for extracting DB2 table data using COBOL copybook metadata and exporting CSV.

## Features

- DB2 connection test and schema/table browsing
- Table metadata and preview
- Copybook upload/paste/folder selection
- Copybook parsing with warnings for unsupported syntax
- Auto mapping DB2 columns to copybook fields
- Read-only extraction with WHERE clause validation
- CSV generation and download options
- Logging with masked credentials

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Configuration

1. Copy `.env.example` to `.env` and fill DB2 values.
2. Optional app settings in `config/settings.yaml`.
3. Place reusable copybooks in `sample/copybooks/`.

## Testing

```bash
pytest -q
```

## Project Structure

See `src/` modules for DB2, copybook parsing, mapping, security validation, and CSV export.
