# COBOL Extractor

Python Streamlit MVP for extracting DB2 table data using COBOL copybook metadata and exporting CSV.

## Features

- DB2 connection test and schema/table browsing via JDBC
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

### DB2 JDBC Connection

This application uses JDBC via JayDeBeApi to connect to DB2 databases. You'll need:

1. **DB2 JDBC Driver JARs**: Download these files from IBM:
   - `db2jcc.jar`
   - `db2jcc_license_cisuz.jar`

2. **Environment Variables**: Copy `.env.example` to `.env` and configure:
   ```bash
   DB2_HOST=your-db2-host
   DB2_PORT=50000
   DB2_DATABASE=your-database
   DB2_USER=your-username
   DB2_PASSWORD=your-password
   DB2_SSL_ENABLED=false
   DB2_JDBC_JAR_PATH=/path/to/db2jcc.jar
   DB2_LICENSE_JAR_PATH=/path/to/db2jcc_license_cisuz.jar
   ```

3. **Java Runtime**: Ensure Java is installed (required by JPype1 for JDBC):
   ```bash
   java -version
   ```

### Other Configuration

1. Optional app settings in `config/settings.yaml`.
2. Place reusable copybooks in `sample/copybooks/`.

## Testing

```bash
pytest -q
```

## Project Structure

See `src/` modules for DB2, copybook parsing, mapping, security validation, and CSV export.
