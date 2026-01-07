#!/usr/bin/env python3
"""
Post Manager for BBS Blog Engine - PostgreSQL Version
Handles blog post CRUD operations
"""

from typing import Optional, List, Dict
from datetime import datetime
from .database import BlogDatabase

class PostManager:
    """Manage blog posts"""
    
    def __init__(self, db: BlogDatabase):
        self.db = db
    
    def create_post(self, title: str, content: str, author_callsign: str, 
                   category: str = None, tags: str = None, 
                   status: str = 'draft') -> Optional[int]:
        """Create a new blog post"""
        
        if not title or not content:
            print("Error: Title and content are required")
            return None
        
        if status not in ['draft', 'published']:
            print(f"Error: Invalid status '{status}'. Must be draft or published")
            return None
        
        author_callsign = author_callsign.upper().strip()
        
        # PostgreSQL uses RETURNING to get the inserted ID
        query = """
            INSERT INTO posts (title, content, author_callsign, category, tags, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        try:
            self.db.cursor.execute(query, 
                (title, content, author_callsign, category, tags, status))
            result = self.db.cursor.fetchone()
            self.db.connection.commit()
            
            if result:
                post_id = result['id']
                print(f"✓ Post created with ID: {post_id}")
                return post_id
            else:
                print("✗ Failed to create post")
                return None
        except Exception as e:
            print(f"✗ Failed to create post: {e}")
            self.db.connection.rollback()
            return None
    
    def get_post(self, post_id: int) -> Optional[Dict]:
        """Get a single post by ID"""
        query = """
            SELECT p.*, u.name as author_name
            FROM posts p
            LEFT JOIN users u ON p.author_callsign = u.callsign
            WHERE p.id = %s
        """
        return self.db.execute_one(query, (post_id,))
    
    def update_post(self, post_id: int, title: str = None, content: str = None,
                   category: str = None, tags: str = None) -> bool:
        """Update an existing post"""
        
        # Build dynamic update query
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = %s")
            params.append(title)
        
        if content is not None:
            updates.append("content = %s")
            params.append(content)
        
        if category is not None:
            updates.append("category = %s")
            params.append(category)
        
        if tags is not None:
            updates.append("tags = %s")
            params.append(tags)
        
        if not updates:
            print("Error: No fields to update")
            return False
        
        params.append(post_id)
        query = f"UPDATE posts SET {', '.join(updates)} WHERE id = %s"
        
        result = self.db.execute(query, tuple(params), fetch=False)
        
        if result is not None:
            print(f"✓ Post {post_id} updated")
            return True
        else:
            print(f"✗ Failed to update post {post_id}")
            return False
    
    def delete_post(self, post_id: int) -> bool:
        """Delete a post (will cascade delete comments)"""
        query = "DELETE FROM posts WHERE id = %s"
        result = self.db.execute(query, (post_id,), fetch=False)
        
        if result is not None:
            print(f"✓ Post {post_id} deleted")
            return True
        else:
            print(f"✗ Failed to delete post {post_id}")
            return False
    
    def publish_post(self, post_id: int) -> bool:
        """Publish a draft post"""
        query = "UPDATE posts SET status = 'published' WHERE id = %s"
        result = self.db.execute(query, (post_id,), fetch=False)
        
        if result is not None:
            print(f"✓ Post {post_id} published")
            return True
        else:
            print(f"✗ Failed to publish post {post_id}")
            return False
    
    def unpublish_post(self, post_id: int) -> bool:
        """Unpublish a post (back to draft)"""
        query = "UPDATE posts SET status = 'draft' WHERE id = %s"
        result = self.db.execute(query, (post_id,), fetch=False)
        
        if result is not None:
            print(f"✓ Post {post_id} unpublished")
            return True
        else:
            print(f"✗ Failed to unpublish post {post_id}")
            return False
    
    def list_posts(self, status: str = 'published', limit: int = 10, 
                  offset: int = 0, author: str = None, 
                  category: str = None) -> List[Dict]:
        """List posts with filtering and pagination"""
        
        query = """
            SELECT p.id, p.title, p.author_callsign, p.category, p.status,
                   p.created_at, p.updated_at, u.name as author_name,
                   (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) as comment_count
            FROM posts p
            LEFT JOIN users u ON p.author_callsign = u.callsign
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND p.status = %s"
            params.append(status)
        
        if author:
            query += " AND p.author_callsign = %s"
            params.append(author.upper())
        
        if category:
            query += " AND p.category = %s"
            params.append(category)
        
        query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.db.execute(query, tuple(params)) or []
    
    def search_posts(self, search_term: str, status: str = 'published', 
                    limit: int = 10) -> List[Dict]:
        """Search posts by title or content (case-insensitive)"""
        # PostgreSQL uses ILIKE for case-insensitive search
        query = """
            SELECT p.id, p.title, p.author_callsign, p.category, p.status,
                   p.created_at, u.name as author_name,
                   (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) as comment_count
            FROM posts p
            LEFT JOIN users u ON p.author_callsign = u.callsign
            WHERE (p.title ILIKE %s OR p.content ILIKE %s)
        """
        params = [f"%{search_term}%", f"%{search_term}%"]
        
        if status:
            query += " AND p.status = %s"
            params.append(status)
        
        query += " ORDER BY p.created_at DESC LIMIT %s"
        params.append(limit)
        
        return self.db.execute(query, tuple(params)) or []
    
    def get_categories(self) -> List[str]:
        """Get list of all categories"""
        query = """
            SELECT DISTINCT category 
            FROM posts 
            WHERE category IS NOT NULL AND category != ''
            ORDER BY category
        """
        results = self.db.execute(query) or []
        return [r['category'] for r in results if r['category']]
    
    def count_posts(self, status: str = None, author: str = None, 
                   category: str = None) -> int:
        """Count posts with filters"""
        query = "SELECT COUNT(*) as count FROM posts WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if author:
            query += " AND author_callsign = %s"
            params.append(author.upper())
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        result = self.db.execute_one(query, tuple(params) if params else None)
        return result['count'] if result else 0
