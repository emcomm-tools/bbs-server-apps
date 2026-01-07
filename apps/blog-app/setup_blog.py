#!/usr/bin/env python3
"""
BBS Blog Database Setup Script - PostgreSQL Version
Creates database schema and initial admin user
"""

import sys
import os
import json

# CRITICAL: When run from different directory, need to find our modules
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
os.chdir(script_dir)

def load_config(config_path="blog_config.json"):
    """Load configuration"""
    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}")
        return None
    
    with open(config_path, 'r') as f:
        return json.load(f)

def test_connection(config):
    """Test PostgreSQL connection"""
    try:
        import psycopg2
        
        db_config = config['database']
        connection = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        connection.close()
        print(f"✓ Connected to PostgreSQL database '{db_config['database']}'")
        return True
        
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def setup_schema(config):
    """Create database schema"""
    from lib.database import BlogDatabase
    
    try:
        db = BlogDatabase()
        if db.connect():
            print("✓ Connected to database")
            if db.create_schema():
                print("✓ Schema created successfully")
                db.disconnect()
                return True
        else:
            print("✗ Failed to connect to database")
            return False
    except Exception as e:
        print(f"✗ Schema setup error: {e}")
        return False

def create_admin_user(config):
    """Create initial admin user"""
    from lib.database import BlogDatabase
    from lib.user_manager import UserManager
    
    try:
        db = BlogDatabase()
        if db.connect():
            user_mgr = UserManager(db)
            
            admin_callsign = config.get('admin_callsign', 'VA2OPS')
            
            # Check if admin already exists
            existing = user_mgr.get_user(admin_callsign)
            if existing:
                print(f"✓ Admin user {admin_callsign} already exists")
                
                # Update to admin role if not already
                if existing['role'] != 'admin':
                    user_mgr.update_role(admin_callsign, 'admin')
                    print(f"✓ Updated {admin_callsign} to admin role")
            else:
                # Create new admin user
                if user_mgr.add_user(admin_callsign, role='admin'):
                    print(f"✓ Admin user {admin_callsign} created")
            
            db.disconnect()
            return True
        else:
            print("✗ Failed to connect to database")
            return False
            
    except Exception as e:
        print(f"✗ Admin user creation error: {e}")
        return False

def main():
    """Main setup process"""
    print("=" * 60)
    print("BBS BLOG ENGINE - POSTGRESQL DATABASE SETUP")
    print("=" * 60)
    print()
    
    # Check for psycopg2
    try:
        import psycopg2
        print("✓ psycopg2 module found")
    except ImportError:
        print("✗ psycopg2 not installed!")
        print("  Install with: pip3 install psycopg2-binary")
        return 1
    
    # Load configuration
    config_path = "blog_config.json"
    config = load_config(config_path)
    
    if not config:
        print("\nPlease create blog_config.json with PostgreSQL settings:")
        print("""
{
    "database": {
        "host": "localhost",
        "port": 5432,
        "user": "bbs_user",
        "password": "your_password",
        "database": "bbs_emcomm"
    },
    "admin_callsign": "YOUR_CALLSIGN"
}
        """)
        return 1
    
    print(f"\nStep 1: Test connection to PostgreSQL...")
    if not test_connection(config):
        print("\n✗ Setup failed - cannot connect to database")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running: sudo systemctl status postgresql")
        print("2. Database exists: sudo -u postgres psql -c '\\l'")
        print("3. User has access: psql -h localhost -U bbs_user -d bbs_emcomm")
        print("4. Credentials in blog_config.json are correct")
        return 1
    
    print("\nStep 2: Create schema...")
    if not setup_schema(config):
        print("\n✗ Setup failed at schema creation")
        return 1
    
    print("\nStep 3: Create admin user...")
    if not create_admin_user(config):
        print("\n✗ Setup failed at admin user creation")
        return 1
    
    print("\n" + "=" * 60)
    print("✓ BBS BLOG ENGINE SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("You can now run: python3 blog.py")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
