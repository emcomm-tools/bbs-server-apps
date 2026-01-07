# BBS Blog Engine - PostgreSQL Version

Complete blog system for LinBPQ/Telnet integration with **PostgreSQL** backend.

This version uses the same database as your APRS/QGIS application for unified EmComm infrastructure.

## Features

- **PostgreSQL Database** - Shared with APRS/QGIS for unified EmComm stack
- **Role-Based Permissions** - Admin, Author, Reader roles
- **Full CRUD Operations** - Create, Read, Update, Delete posts
- **Comment System** - Users can comment on posts
- **Draft/Published Status** - Write drafts before publishing
- **Categories & Tags** - Organize content
- **Search Functionality** - Case-insensitive search with ILIKE
- **RF-Optimized** - 79 char line wrapping for packet radio
- **User Management** - Admin can manage users and roles

## Quick Installation

### 1. Install PostgreSQL (if not already installed)

See `POSTGRES_INSTALL.md` for detailed instructions.

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
pip3 install psycopg2-binary
```

### 2. Create Database and User

```bash
sudo -u postgres psql

CREATE DATABASE bbs_emcomm;
CREATE USER bbs_user WITH ENCRYPTED PASSWORD 'YourSecurePassword';
GRANT ALL PRIVILEGES ON DATABASE bbs_emcomm TO bbs_user;
\c bbs_emcomm
GRANT ALL ON SCHEMA public TO bbs_user;
\q
```

### 3. Configure

Edit `blog_config.json`:

```json
{
    "database": {
        "host": "localhost",
        "port": 5432,
        "user": "bbs_user",
        "password": "YourSecurePassword",
        "database": "bbs_emcomm"
    },
    "admin_callsign": "VA2OPS"
}
```

### 4. Setup Database Tables

```bash
python3 setup_blog.py
```

### 5. Run

```bash
python3 blog.py
```

## Database Schema

### users
```sql
callsign VARCHAR(10) PRIMARY KEY
name VARCHAR(100)
role VARCHAR(10) CHECK (role IN ('admin', 'author', 'reader'))
created_at TIMESTAMP
```

### posts
```sql
id SERIAL PRIMARY KEY
title VARCHAR(255)
content TEXT
author_callsign VARCHAR(10) REFERENCES users(callsign)
category VARCHAR(50)
tags TEXT
status VARCHAR(10) CHECK (status IN ('draft', 'published'))
created_at TIMESTAMP
updated_at TIMESTAMP
```

### comments
```sql
id SERIAL PRIMARY KEY
post_id INTEGER REFERENCES posts(id)
author_callsign VARCHAR(10) REFERENCES users(callsign)
content TEXT
created_at TIMESTAMP
```

## Differences from MySQL Version

| Feature | MySQL | PostgreSQL |
|---------|-------|------------|
| Auto ID | `AUTO_INCREMENT` | `SERIAL` |
| Upsert | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` |
| Case-insensitive search | `LIKE` | `ILIKE` |
| Port | 3306 | 5432 |
| Driver | `mysql-connector-python` | `psycopg2` |

## Shared Database Benefits

Your EmComm stack can now share one database:

```
PostgreSQL (bbs_emcomm)
├── Blog tables (users, posts, comments)
├── APRS tables (your QGIS app)
└── Future apps...
```

Benefits:
- One backup strategy
- One service to maintain  
- Shared user authentication possible
- PostGIS for spatial APRS data

## Commands

Same as MySQL version - see `QUICKREF.md`

```
list              - List posts
read <id>         - Read a post
new               - Create post (authors)
edit <id>         - Edit post
delete <id>       - Delete post
comment <id>      - Add comment
search <term>     - Search posts
user list         - List users (admin)
user add <c> <r>  - Add user (admin)
help              - Show all commands
quit              - Exit
```

## Migration from MySQL

If you have existing data in MySQL:

1. Export from MySQL: `mysqldump bbs_blog > mysql_backup.sql`
2. The SQL syntax is slightly different, so manual migration may be needed
3. Or just start fresh with PostgreSQL

## File Structure

```
blog-postgres/
├── blog.py                 # Main program
├── setup_blog.py           # Database setup
├── blog_config.json        # Configuration
├── blog_debug.py           # Debug tool
├── POSTGRES_INSTALL.md     # PostgreSQL setup guide
├── README.md               # This file
├── QUICKREF.md             # Command reference
└── lib/
    ├── __init__.py
    ├── database.py         # PostgreSQL connection
    ├── user_manager.py     # User handling
    ├── post_manager.py     # Post CRUD
    ├── comment_manager.py  # Comments
    └── formatter.py        # RF formatting
```

## Troubleshooting

### "Connection refused"
```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

### "Authentication failed"
Check password in `blog_config.json` matches PostgreSQL user password.

### "Database does not exist"
```bash
sudo -u postgres createdb bbs_emcomm
```

### "Permission denied"
```bash
sudo -u postgres psql -d bbs_emcomm -c "GRANT ALL ON SCHEMA public TO bbs_user;"
```

## Backup

```bash
# Backup
pg_dump -h localhost -U bbs_user bbs_emcomm > backup.sql

# Restore
psql -h localhost -U bbs_user -d bbs_emcomm < backup.sql
```

## License

Free for amateur radio use.

73! 📻
