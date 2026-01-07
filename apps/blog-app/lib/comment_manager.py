#!/usr/bin/env python3
"""
Comment Manager for BBS Blog Engine - PostgreSQL Version
Handles comments on blog posts
"""

from typing import Optional, List, Dict
from .database import BlogDatabase

class CommentManager:
    """Manage blog post comments"""
    
    def __init__(self, db: BlogDatabase):
        self.db = db
    
    def add_comment(self, post_id: int, author_callsign: str, content: str) -> Optional[int]:
        """Add a comment to a post"""
        
        if not content or not content.strip():
            print("Error: Comment content cannot be empty")
            return None
        
        author_callsign = author_callsign.upper().strip()
        
        # Verify post exists
        post_check = self.db.execute_one("SELECT id FROM posts WHERE id = %s", (post_id,))
        if not post_check:
            print(f"Error: Post {post_id} not found")
            return None
        
        # PostgreSQL uses RETURNING to get the inserted ID
        query = """
            INSERT INTO comments (post_id, author_callsign, content)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        
        try:
            self.db.cursor.execute(query, (post_id, author_callsign, content))
            result = self.db.cursor.fetchone()
            self.db.connection.commit()
            
            if result:
                comment_id = result['id']
                print(f"✓ Comment added with ID: {comment_id}")
                return comment_id
            else:
                print("✗ Failed to add comment")
                return None
        except Exception as e:
            print(f"✗ Failed to add comment: {e}")
            self.db.connection.rollback()
            return None
    
    def get_comment(self, comment_id: int) -> Optional[Dict]:
        """Get a single comment by ID"""
        query = """
            SELECT c.*, u.name as author_name
            FROM comments c
            LEFT JOIN users u ON c.author_callsign = u.callsign
            WHERE c.id = %s
        """
        return self.db.execute_one(query, (comment_id,))
    
    def get_post_comments(self, post_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get all comments for a post"""
        query = """
            SELECT c.*, u.name as author_name
            FROM comments c
            LEFT JOIN users u ON c.author_callsign = u.callsign
            WHERE c.post_id = %s
            ORDER BY c.created_at ASC
            LIMIT %s OFFSET %s
        """
        return self.db.execute(query, (post_id, limit, offset)) or []
    
    def count_post_comments(self, post_id: int) -> int:
        """Count comments for a post"""
        query = "SELECT COUNT(*) as count FROM comments WHERE post_id = %s"
        result = self.db.execute_one(query, (post_id,))
        return result['count'] if result else 0
    
    def delete_comment(self, comment_id: int) -> bool:
        """Delete a comment"""
        query = "DELETE FROM comments WHERE id = %s"
        result = self.db.execute(query, (comment_id,), fetch=False)
        
        if result is not None:
            print(f"✓ Comment {comment_id} deleted")
            return True
        else:
            print(f"✗ Failed to delete comment {comment_id}")
            return False
    
    def get_user_comments(self, author_callsign: str, limit: int = 20) -> List[Dict]:
        """Get all comments by a user"""
        query = """
            SELECT c.*, u.name as author_name, p.title as post_title
            FROM comments c
            LEFT JOIN users u ON c.author_callsign = u.callsign
            LEFT JOIN posts p ON c.post_id = p.id
            WHERE c.author_callsign = %s
            ORDER BY c.created_at DESC
            LIMIT %s
        """
        return self.db.execute(query, (author_callsign.upper(), limit)) or []
    
    def get_recent_comments(self, limit: int = 10) -> List[Dict]:
        """Get recent comments across all posts"""
        query = """
            SELECT c.*, u.name as author_name, p.title as post_title, p.id as post_id
            FROM comments c
            LEFT JOIN users u ON c.author_callsign = u.callsign
            LEFT JOIN posts p ON c.post_id = p.id
            ORDER BY c.created_at DESC
            LIMIT %s
        """
        return self.db.execute(query, (limit,)) or []
