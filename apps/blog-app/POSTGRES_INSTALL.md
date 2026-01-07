# PostgreSQL Installation & Setup for BBS Blog Engine

## Ubuntu 22.04/22.10 Installation

### Step 1: Install PostgreSQL

```bash
# Update package list
sudo apt update

# Install PostgreSQL and contrib modules
sudo apt install postgresql postgresql-contrib

# Install Python PostgreSQL adapter
pip3 install psycopg2-binary
```

### Step 2: Verify Installation

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Should show "active (running)"

# Check version
psql --version
```

### Step 3: Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql
```

Then in the PostgreSQL prompt:

```sql
-- Create the database
CREATE DATABASE bbs_emcomm;

-- Create the user with password
CREATE USER bbs_user WITH ENCRYPTED PASSWORD 'YourSecurePassword123!';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE bbs_emcomm TO bbs_user;

-- Connect to the database to set schema privileges
\c bbs_emcomm

-- Grant schema privileges (required for PostgreSQL 15+)
GRANT ALL ON SCHEMA public TO bbs_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bbs_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bbs_user;

-- Exit
\q
```

### Step 4: Test Connection

```bash
# Test connection with the new user
psql -h localhost -U bbs_user -d bbs_emcomm

# Enter your password when prompted
# If you get a prompt like "bbs_emcomm=>", it works!

# Exit with:
\q
```

### Step 5: Configure PostgreSQL for Local Connections (if needed)

If you get authentication errors, edit pg_hba.conf:

```bash
# Find the config file
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

Find the line for local IPv4 connections and ensure it says:
```
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
```

Then restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

## Quick Reference Commands

### PostgreSQL Service
```bash
sudo systemctl start postgresql    # Start
sudo systemctl stop postgresql     # Stop
sudo systemctl restart postgresql  # Restart
sudo systemctl status postgresql   # Check status
sudo systemctl enable postgresql   # Start on boot
```

### Connect to Database
```bash
# As postgres superuser
sudo -u postgres psql

# As bbs_user to bbs_emcomm database
psql -h localhost -U bbs_user -d bbs_emcomm
```

### Useful psql Commands
```
\l              -- List databases
\c dbname       -- Connect to database
\dt             -- List tables
\d tablename    -- Describe table structure
\du             -- List users
\q              -- Quit
```

### Backup & Restore
```bash
# Backup
pg_dump -h localhost -U bbs_user bbs_emcomm > backup.sql

# Restore
psql -h localhost -U bbs_user -d bbs_emcomm < backup.sql
```

## For Your APRS App (Future)

If you need PostGIS for spatial data:

```bash
# Install PostGIS
sudo apt install postgis postgresql-14-postgis-3

# Enable in database
sudo -u postgres psql -d bbs_emcomm -c "CREATE EXTENSION postgis;"
```

This gives you spatial queries for APRS positions!

## Next Steps

After PostgreSQL is installed and configured:

1. Edit `blog_config.json` with your PostgreSQL credentials
2. Run `python3 setup_blog.py` to create tables
3. Run `python3 blog.py` to start blogging!

73!
