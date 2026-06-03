# DB2 JDBC Migration Guide

## Overview

The DB2 connection layer has been migrated from `ibm_db` (IBM CLI driver) to `jaydebeapi` (JDBC driver) to resolve connectivity issues and align with the working DBeaver JDBC setup.

## What Changed

### Dependencies
- **Removed**: `ibm_db`, `ibm_db_dbi`
- **Added**: `jaydebeapi`, `JPype1`

### Connection Approach
- **Before**: Used IBM CLI driver with connection strings
- **After**: Uses JDBC driver with connection URLs

### Configuration
New environment variables are required:
- `DB2_JDBC_JAR_PATH`: Path to `db2jcc.jar`
- `DB2_LICENSE_JAR_PATH`: Path to `db2jcc_license_cisuz.jar`
- `DB2_USER`: Renamed from `DB2_USERNAME`
- `DB2_SSL_ENABLED`: Renamed from `DB2_SSL`

## Setup Instructions

### 1. Obtain JDBC Driver Files

Download these files from IBM:
- `db2jcc.jar` - DB2 JDBC driver
- `db2jcc_license_cisuz.jar` - DB2 license file

Place them in a known location, e.g., `/opt/db2/jdbc/` or in your project directory.

### 2. Install Java Runtime

JDBC requires Java. Verify it's installed:

```bash
java -version
```

If not installed, install Java (version 8 or higher):

```bash
# Ubuntu/Debian
sudo apt-get install openjdk-11-jre

# macOS
brew install openjdk@11

# Windows
# Download and install from https://adoptium.net/
```

### 3. Update Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `jaydebeapi` - Python JDBC bridge
- `JPype1` - Java-Python integration

### 4. Configure Environment Variables

Update your `.env` file (copy from `.env.example`):

```bash
DB2_HOST=your-db2-host.example.com
DB2_PORT=50000
DB2_DATABASE=YOURDB
DB2_USER=yourusername
DB2_PASSWORD=yourpassword
DB2_SSL_ENABLED=false
DB2_JDBC_JAR_PATH=/opt/db2/jdbc/db2jcc.jar
DB2_LICENSE_JAR_PATH=/opt/db2/jdbc/db2jcc_license_cisuz.jar
```

### 5. Run the Application

```bash
streamlit run app.py
```

The application will:
1. Load environment variables from `.env`
2. Pre-fill connection fields with values from environment variables
3. Allow you to override values in the UI if needed

## API Changes

### Connection Function

The `test_connection()` function signature remains the same, but now requires JDBC JAR paths:

**Before:**
```python
test_connection({
    "hostname": "localhost",
    "port": 50000,
    "database": "TESTDB",
    "username": "user",
    "password": "pass",
    "ssl_enabled": False,
})
```

**After:**
```python
test_connection({
    "hostname": "localhost",
    "port": 50000,
    "database": "TESTDB",
    "username": "user",
    "password": "pass",
    "ssl_enabled": False,
    "jdbc_jar_path": "/path/to/db2jcc.jar",
    "license_jar_path": "/path/to/db2jcc_license_cisuz.jar",
})
```

### JDBC URL Format

The JDBC URL is constructed as:

```
jdbc:db2://{host}:{port}/{database}
```

With SSL:
```
jdbc:db2://{host}:{port}/{database}:sslConnection=true;
```

### Connection Object

The connection object returned by `jaydebeapi.connect()` is fully compatible with Python DB-API 2.0, so all existing code using `cursor()`, `execute()`, `fetchall()`, etc. works without changes.

## Benefits

1. **Compatibility**: Uses the same JDBC driver as DBeaver
2. **Reliability**: Avoids CLI driver communication errors
3. **Portability**: JDBC drivers work across platforms
4. **Standardization**: Uses standard JDBC connection approach

## Troubleshooting

### "JDBC driver JAR paths not provided"

**Solution**: Set `DB2_JDBC_JAR_PATH` and `DB2_LICENSE_JAR_PATH` in your `.env` file or provide them in the UI.

### "JDBC driver JAR file not found"

**Solution**: Verify the JAR file paths are correct and the files exist.

### "Java gateway process exited before sending..."

**Solution**: Ensure Java is installed and accessible in your PATH:
```bash
java -version
```

### "SQL30081N A communication error has been detected"

This was the original error with the CLI driver. If you still see this with JDBC:
1. Verify the DB2 server address and port are correct
2. Check firewall rules allow connections to the DB2 port
3. Verify SSL settings match the server configuration
4. Try the same connection parameters in DBeaver to confirm they work

## Compatibility

- The migration is **backward compatible** at the API level
- All existing tests pass (32/32)
- The connection object is DB-API 2.0 compliant
- All database operations (queries, metadata, extraction) work unchanged

## Rollback

If you need to rollback to the CLI driver:

1. Checkout the previous commit
2. Update `requirements.txt` to restore `ibm_db` and `ibm_db_dbi`
3. Run `pip install -r requirements.txt`

However, this will bring back the original connection issues.
