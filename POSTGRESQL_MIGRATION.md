# PostgreSQL Migration Plan

## Overview
This document outlines the plan to migrate TidyMe from SQLite to PostgreSQL for better scalability and performance.

## Current SQLite Schema

### Tables
1. **scans**
   - id (INTEGER PRIMARY KEY)
   - scan_date (DATETIME)
   - scan_type (TEXT)
   - files_found (INTEGER)
   - total_size (INTEGER)
   - status (TEXT)

2. **files**
   - id (INTEGER PRIMARY KEY)
   - path (TEXT UNIQUE)
   - size (INTEGER)
   - hash (TEXT)
   - file_type (TEXT)
   - last_access (DATETIME)
   - last_modified (DATETIME)
   - is_duplicate (INTEGER)
   - duplicate_group (TEXT)
   - confidence_score (REAL)
   - scan_id (INTEGER, FOREIGN KEY)

3. **duplicates**
   - id (INTEGER PRIMARY KEY)
   - group_id (TEXT)
   - file_path (TEXT)
   - file_size (INTEGER)
   - file_hash (TEXT)
   - similarity_score (REAL)
   - recommended_action (TEXT)
   - scan_date (DATETIME)

4. **cleanup_log**
   - id (INTEGER PRIMARY KEY)
   - action_date (DATETIME)
   - action_type (TEXT)
   - file_path (TEXT)
   - file_size (INTEGER)
   - success (INTEGER)
   - error_message (TEXT)

## PostgreSQL Schema Improvements

### Enhanced Data Types
```sql
-- scans table
CREATE TABLE scans (
    id SERIAL PRIMARY KEY,
    scan_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    scan_type VARCHAR(50) NOT NULL,
    files_found INTEGER DEFAULT 0,
    total_size BIGINT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- files table
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    size BIGINT NOT NULL,
    hash VARCHAR(128),
    file_type VARCHAR(100),
    last_access TIMESTAMP WITH TIME ZONE,
    last_modified TIMESTAMP WITH TIME ZONE,
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_group VARCHAR(100),
    confidence_score DECIMAL(3,2),
    scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- duplicates table
CREATE TABLE duplicates (
    id SERIAL PRIMARY KEY,
    group_id VARCHAR(100) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash VARCHAR(128),
    similarity_score DECIMAL(3,2),
    recommended_action VARCHAR(50),
    scan_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- cleanup_log table
CREATE TABLE cleanup_log (
    id SERIAL PRIMARY KEY,
    action_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(50) NOT NULL,
    file_path TEXT,
    file_size BIGINT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    duration_ms INTEGER,  -- New field for performance tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI analysis results table (new)
CREATE TABLE ai_analysis (
    id SERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    result JSONB,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_scans_date ON scans(scan_date);
CREATE INDEX idx_scans_type ON scans(scan_type);
CREATE INDEX idx_files_path ON files(path);
CREATE INDEX idx_files_hash ON files(hash);
CREATE INDEX idx_files_scan_id ON files(scan_id);
CREATE INDEX idx_duplicates_group ON duplicates(group_id);
CREATE INDEX idx_cleanup_log_date ON cleanup_log(action_date);
CREATE INDEX idx_cleanup_log_type ON cleanup_log(action_type);
CREATE INDEX idx_ai_analysis_path ON ai_analysis(file_path);
```

## Migration Steps

### 1. Environment Setup
```bash
# Install PostgreSQL
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Create database and user
createdb tidyme
createuser tidyme_user
psql -c "ALTER USER tidyme_user PASSWORD 'secure_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE tidyme TO tidyme_user;"
```

### 2. Python Dependencies
```bash
pip install psycopg2-binary SQLAlchemy alembic
```

### 3. Database Connection Update
```python
# In app.py, replace SQLite connection with PostgreSQL
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://tidyme_user:secure_password@localhost:5432/tidyme"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
```

### 4. Schema Migration
```python
def init_postgres_db():
    """Initialize PostgreSQL database with new schema"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute schema creation SQL
    with open('schema/postgres_schema.sql', 'r') as f:
        schema_sql = f.read()
        cursor.execute(schema_sql)

    conn.commit()
    conn.close()
```

### 5. Data Migration Script
```python
def migrate_sqlite_to_postgres():
    """Migrate data from SQLite to PostgreSQL"""
    import sqlite3

    # Connect to both databases
    sqlite_conn = sqlite3.connect('data/cleanup.db')
    postgres_conn = get_db_connection()

    # Migrate each table
    tables = ['scans', 'files', 'duplicates', 'cleanup_log']

    for table in tables:
        # Get data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()

        # Insert into PostgreSQL
        postgres_cursor = postgres_conn.cursor()
        for row in rows:
            # Handle data type conversions
            # Insert logic here

    postgres_conn.commit()
    sqlite_conn.close()
    postgres_conn.close()
```

## Benefits of PostgreSQL Migration

### Performance Improvements
- Better concurrent access handling
- Advanced indexing options
- Query optimization
- Connection pooling support

### Scalability Features
- JSONB for flexible AI analysis storage
- Partitioning for large tables
- Advanced replication options
- Better handling of large datasets

### Reliability
- ACID compliance
- Point-in-time recovery
- Advanced backup options
- Better error handling

### New Features Enabled
- Full-text search capabilities
- Advanced analytics queries
- Time-series data handling
- Geospatial data support (if needed)

## Implementation Timeline

### Phase 1: Setup (Week 1)
- Install PostgreSQL
- Create database schema
- Set up connection handling

### Phase 2: Migration (Week 2)
- Create migration scripts
- Test data migration
- Update application code

### Phase 3: Testing (Week 3)
- Comprehensive testing
- Performance benchmarking
- Rollback procedures

### Phase 4: Deployment (Week 4)
- Production deployment
- Monitoring setup
- Documentation updates

## Rollback Plan
- Keep SQLite database as backup
- Maintain dual connection capability during transition
- Automated rollback scripts
- Data validation checks

## Monitoring and Maintenance
- Set up PostgreSQL monitoring
- Configure automated backups
- Performance tuning
- Regular maintenance tasks