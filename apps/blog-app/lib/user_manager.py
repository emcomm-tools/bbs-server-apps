#!/usr/bin/env python3
"""
User Manager for BBS Blog Engine - PostgreSQL Version
Handles user authentication, roles, and permissions
"""

from typing import Optional, List, Dict
from .database import BlogDatabase

class UserManager:
    """Manage blog users and permissions"""
    
    def __init__(self, db: BlogDatabase):
        self.db = db
    
    def add_user(self, callsign: str, name: str = None, role: str = 'reader') -> bool:
        """Add a new user"""
        callsign = callsign.upper().strip()
        
        if not callsign:
            print("Error: Callsign cannot be empty")
            return False
        
        if role not in ['admin', 'author', 'reader']:
            print(f"Error: Invalid role '{role}'. Must be admin, author, or reader")
            return False
        
        # PostgreSQL uses ON CONFLICT for upsert
        query = """
            INSERT INTO users (callsign, name, role)
            VALUES (%s, %s, %s)
            ON CONFLICT (callsign) 
            DO UPDATE SET name = EXCLUDED.name, role = EXCLUDED.role
        """
        
        result = self.db.execute(query, (callsign, name, role), fetch=False)
        
        if result is not None:
            print(f"✓ User {callsign} added/updated as {role}")
            return True
        else:
            print(f"✗ Failed to add user {callsign}")
            return False
    
    def get_user(self, callsign: str) -> Optional[Dict]:
        """Get user information"""
        callsign = callsign.upper().strip()
        
        query = "SELECT * FROM users WHERE callsign = %s"
        return self.db.execute_one(query, (callsign,))
    
    def get_or_create_user(self, callsign: str, default_role: str = 'reader') -> Optional[Dict]:
        """Get user or create with default role"""
        user = self.get_user(callsign)
        
        if not user:
            # Auto-create user with default role
            self.add_user(callsign, role=default_role)
            user = self.get_user(callsign)
        
        return user
    
    def list_users(self) -> List[Dict]:
        """List all users"""
        query = "SELECT * FROM users ORDER BY created_at DESC"
        return self.db.execute(query) or []
    
    def delete_user(self, callsign: str) -> bool:
        """Delete a user (will cascade delete their posts/comments)"""
        callsign = callsign.upper().strip()
        
        query = "DELETE FROM users WHERE callsign = %s"
        result = self.db.execute(query, (callsign,), fetch=False)
        
        if result is not None:
            print(f"✓ User {callsign} deleted")
            return True
        else:
            print(f"✗ Failed to delete user {callsign}")
            return False
    
    def update_role(self, callsign: str, new_role: str) -> bool:
        """Update user role"""
        callsign = callsign.upper().strip()
        
        if new_role not in ['admin', 'author', 'reader']:
            print(f"Error: Invalid role '{new_role}'")
            return False
        
        query = "UPDATE users SET role = %s WHERE callsign = %s"
        result = self.db.execute(query, (new_role, callsign), fetch=False)
        
        if result is not None:
            print(f"✓ User {callsign} role updated to {new_role}")
            return True
        else:
            print(f"✗ Failed to update role for {callsign}")
            return False
    
    def can_edit_post(self, user_callsign: str, post_author: str) -> bool:
        """Check if user can edit a post"""
        user = self.get_user(user_callsign)
        
        if not user:
            return False
        
        # Admin can edit anything
        if user['role'] == 'admin':
            return True
        
        # Authors can edit their own posts
        if user['role'] == 'author' and user_callsign.upper() == post_author.upper():
            return True
        
        return False
    
    def can_delete_post(self, user_callsign: str, post_author: str) -> bool:
        """Check if user can delete a post"""
        # Same rules as editing
        return self.can_edit_post(user_callsign, post_author)
    
    def can_create_post(self, user_callsign: str) -> bool:
        """Check if user can create posts"""
        user = self.get_user(user_callsign)
        
        if not user:
            return False
        
        # Authors and admins can create posts
        return user['role'] in ['admin', 'author']
    
    def can_delete_comment(self, user_callsign: str, comment_author: str) -> bool:
        """Check if user can delete a comment"""
        user = self.get_user(user_callsign)
        
        if not user:
            return False
        
        # Admin can delete any comment
        if user['role'] == 'admin':
            return True
        
        # Users can delete their own comments
        if user_callsign.upper() == comment_author.upper():
            return True
        
        return False
    
    def is_admin(self, user_callsign: str) -> bool:
        """Check if user is admin"""
        user = self.get_user(user_callsign)
        return user and user['role'] == 'admin'
