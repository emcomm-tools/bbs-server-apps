#!/usr/bin/env python3
"""
Database module for BBS Blog Engine - PostgreSQL Version
Handles PostgreSQL connection and schema management
"""

import psycopg2
from psycopg2 import Error
from psycopg2.extras import RealDictCursor
import json
import os
from typing import Optional, Dict, Any

class BlogDatabase:
    """PostgreSQL database connection and schema management"""
    
    def __init__(self, config_path: str = "blog_config.json"):
        self.config = self._load_config(config_path)
        self.connection = None
        self.cursor = None
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load database configuration from JSON file"""
        # Try relative to script location first
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_locations = [
            os.path.join(script_dir, '..', config_path),
            config_path,
            os.path.join(os.path.dirname(script_dir), config_path)
        ]
        
        for path in config_locations:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            db_config = self.config['database']
            self.connection = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            
            # Use RealDictCursor to get results as dictionaries
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            return True
            
        except Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute(self, query: str, params: tuple = None, fetch: bool = True):
        """Execute a query and return results"""
        try:
            if not self.connection or self.connection.closed:
                if not self.connect():
                    return None
            
            self.cursor.execute(query, params or ())
            
            if fetch:
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                # Try to get lastrowid for INSERT statements
                try:
                    return self.cursor.fetchone()['id'] if self.cursor.description else True
                except:
                    return True
                
        except Error as e:
            print(f"Query error: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def execute_one(self, query: str, params: tuple = None):
        """Execute query and return single result"""
        try:
            if not self.connection or self.connection.closed:
                if not self.connect():
                    return None
            
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
            
        except Error as e:
            print(f"Query error: {e}")
            return None
    
    def create_schema(self) -> bool:
        """Create database schema (tables)"""
        schema_queries = [
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users (
                callsign VARCHAR(10) PRIMARY KEY,
                name VARCHAR(100),
                role VARCHAR(10) DEFAULT 'reader' CHECK (role IN ('admin', 'author', 'reader')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Posts table
            """
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                author_callsign VARCHAR(10) NOT NULL REFERENCES users(callsign) ON DELETE CASCADE,
                category VARCHAR(50),
                tags TEXT,
                status VARCHAR(10) DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Comments table
            """
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
                author_callsign VARCHAR(10) NOT NULL REFERENCES users(callsign) ON DELETE CASCADE,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Create indexes (IF NOT EXISTS for indexes requires PostgreSQL 9.5+)
            """
            CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_callsign)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_comments_author ON comments(author_callsign)
            """
        ]
        
        # Create function for auto-updating updated_at timestamp
        update_trigger = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
        """
        
        # Create trigger for posts table
        posts_trigger = """
        DROP TRIGGER IF EXISTS update_posts_updated_at ON posts;
        CREATE TRIGGER update_posts_updated_at
            BEFORE UPDATE ON posts
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
        """
        
        try:
            for query in schema_queries:
                self.cursor.execute(query)
            
            # Create update trigger
            self.cursor.execute(update_trigger)
            self.cursor.execute(posts_trigger)
            
            self.connection.commit()
            print("✓ Database schema created successfully")
            return True
        except Exception as e:
            print(f"✗ Schema creation error: {e}")
            self.connection.rollback()
            return False
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
