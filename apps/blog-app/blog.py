#!/usr/bin/env python3
"""
BBS Blog Engine - Main Console Interface
Complete blog system for LinBPQ/Telnet integration
"""

import sys
import os
import json

# CRITICAL: When run from inetd/BBS, working directory may be different
# Get the absolute path of where THIS script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add script directory to Python path so we can import from lib
sys.path.insert(0, script_dir)

# Change to script directory so config file can be found
os.chdir(script_dir)

# Import from lib package
from lib.database import BlogDatabase
from lib.user_manager import UserManager
from lib.post_manager import PostManager
from lib.comment_manager import CommentManager
from lib.formatter import RFFormatter

class BlogConsole:
    """Console interface for BBS Blog Engine"""
    
    def __init__(self, config_path="blog_config.json"):
        self.config = self._load_config(config_path)
        self.db = BlogDatabase(config_path)
        self.user_mgr = UserManager(self.db)
        self.post_mgr = PostManager(self.db)
        self.comment_mgr = CommentManager(self.db)
        self.formatter = RFFormatter(self.config.get('max_line_length', 79))
        
        self.current_user = None
        self.current_user_data = None
        
    def _load_config(self, config_path):
        """Load configuration"""
        if not os.path.exists(config_path):
            print(f"Error: Config file not found: {config_path}")
            sys.exit(1)
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def start(self):
        """Start the blog console"""
        if not self.db.connect():
            print("Failed to connect to database")
            print("Please run setup_blog.py first")
            return
        
        # Prompt for callsign
        print("=" * self.config.get('max_line_length', 79))
        print("BBS BLOG ENGINE")
        print("=" * self.config.get('max_line_length', 79))
        print()
        
        callsign = input("Enter your callsign: ").strip().upper()
        
        if not callsign:
            print("Callsign required. Exiting.")
            return
        
        # Get or create user
        self.current_user = callsign
        self.current_user_data = self.user_mgr.get_or_create_user(
            callsign, 
            self.config.get('default_role', 'reader')
        )
        
        if not self.current_user_data:
            print("Failed to load user data. Exiting.")
            return
        
        # Show welcome banner
        print()
        print(self.formatter.format_banner(callsign, self.current_user_data['role']))
        print()
        
        # Main command loop
        self.command_loop()
    
    def command_loop(self):
        """Main command loop"""
        while True:
            try:
                command = input(f"\n{self.current_user}> ").strip()
                
                if not command:
                    continue
                
                # Parse command
                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                # Execute command
                if cmd in ['quit', 'exit', 'q']:
                    print("73! Goodbye!")
                    break
                
                elif cmd == 'help':
                    self.cmd_help()
                
                elif cmd == 'list':
                    self.cmd_list(args)
                
                elif cmd == 'read':
                    self.cmd_read(args)
                
                elif cmd == 'new':
                    self.cmd_new()
                
                elif cmd == 'edit':
                    self.cmd_edit(args)
                
                elif cmd == 'delete':
                    self.cmd_delete(args)
                
                elif cmd == 'publish':
                    self.cmd_publish(args)
                
                elif cmd == 'unpublish':
                    self.cmd_unpublish(args)
                
                elif cmd == 'comment':
                    self.cmd_comment(args)
                
                elif cmd == 'delcomment':
                    self.cmd_delete_comment(args)
                
                elif cmd == 'search':
                    self.cmd_search(args)
                
                elif cmd == 'category':
                    self.cmd_category(args)
                
                elif cmd == 'categories':
                    self.cmd_categories()
                
                elif cmd == 'author':
                    self.cmd_author(args)
                
                elif cmd == 'user':
                    self.cmd_user(args)
                
                elif cmd == 'whoami':
                    self.cmd_whoami()
                
                else:
                    print(f"Unknown command: {cmd}. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\n73! Goodbye!")
                break
            except EOFError:
                print("\n73! Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def cmd_help(self):
        """Show help"""
        commands = {
            "list [page]": "List recent posts",
            "read <id>": "Read a post with comments",
            "new": "Create a new post (authors only)",
            "edit <id>": "Edit a post (if you have permission)",
            "delete <id>": "Delete a post (if you have permission)",
            "publish <id>": "Publish a draft post",
            "unpublish <id>": "Unpublish a post to draft",
            "comment <id>": "Add a comment to a post",
            "delcomment <id>": "Delete a comment (if you have permission)",
            "search <term>": "Search posts by title/content",
            "category <name>": "Show posts in a category",
            "categories": "List all categories",
            "author <call>": "Show posts by an author",
            "user list": "List all users (admin only)",
            "user add <call> <role>": "Add user (admin only)",
            "user role <call> <role>": "Change user role (admin only)",
            "whoami": "Show your user info",
            "help": "Show this help",
            "quit": "Exit the blog"
        }
        
        print(self.formatter.format_help(commands))
    
    def cmd_list(self, args):
        """List posts"""
        page = 1
        if args.strip().isdigit():
            page = int(args.strip())
        
        posts_per_page = self.config.get('posts_per_page', 10)
        offset = (page - 1) * posts_per_page
        
        # Show all posts for authors/admins, only published for readers
        status = None if self.current_user_data['role'] in ['admin', 'author'] else 'published'
        
        posts = self.post_mgr.list_posts(status=status, limit=posts_per_page, offset=offset)
        
        if not posts:
            print("No posts found.")
            return
        
        print()
        print(self.formatter.format_separator("="))
        print(f"BLOG POSTS (Page {page})")
        print(self.formatter.format_separator("="))
        print()
        
        for post in posts:
            print(self.formatter.format_post_list_item(post))
            print()
        
        # Show pagination info
        total = self.post_mgr.count_posts(status=status)
        total_pages = (total + posts_per_page - 1) // posts_per_page
        
        if total_pages > 1:
            print(self.formatter.format_separator("-"))
            print(f"Page {page} of {total_pages} ({total} total posts)")
            if page < total_pages:
                print(f"Type 'list {page + 1}' for next page")
    
    def cmd_read(self, args):
        """Read a post"""
        if not args or not args.strip().isdigit():
            print("Usage: read <post_id>")
            return
        
        post_id = int(args.strip())
        post = self.post_mgr.get_post(post_id)
        
        if not post:
            print(f"Post {post_id} not found.")
            return
        
        # Check if user can view this post
        if post['status'] == 'draft':
            if not self.user_mgr.can_edit_post(self.current_user, post['author_callsign']):
                print("This is a draft post. Only the author and admins can view it.")
                return
        
        # Display post
        print()
        print(self.formatter.format_post_full(post))
        print()
        
        # Display comments
        comments = self.comment_mgr.get_post_comments(post_id)
        
        if comments:
            print(self.formatter.format_header("COMMENTS", "-"))
            print()
            
            for i, comment in enumerate(comments, 1):
                print(self.formatter.format_comment(comment, i))
                print()
        else:
            print("No comments yet. Be the first to comment!")
            print()
        
        print(self.formatter.format_separator("="))
        print(f"Commands: comment {post_id} | edit {post_id} | delete {post_id}")
    
    def cmd_new(self):
        """Create a new post"""
        if not self.user_mgr.can_create_post(self.current_user):
            print("Error: You don't have permission to create posts.")
            print("Only authors and admins can create posts.")
            return
        
        print()
        print(self.formatter.format_separator("="))
        print("CREATE NEW POST")
        print(self.formatter.format_separator("="))
        print()
        
        # Get post details
        title = input("Title: ").strip()
        if not title:
            print("Title cannot be empty. Post cancelled.")
            return
        
        category = input("Category (optional): ").strip() or None
        tags = input("Tags (comma-separated, optional): ").strip() or None
        
        print()
        print("Content (type 'END' on a new line when finished):")
        content_lines = []
        while True:
            line = input()
            if line.strip().upper() == 'END':
                break
            content_lines.append(line)
        
        content = '\n'.join(content_lines).strip()
        
        if not content:
            print("Content cannot be empty. Post cancelled.")
            return
        
        # Ask for publish status
        publish = input("\nPublish now? (y/n, default=draft): ").strip().lower()
        status = 'published' if publish == 'y' else 'draft'
        
        # Create post
        post_id = self.post_mgr.create_post(
            title=title,
            content=content,
            author_callsign=self.current_user,
            category=category,
            tags=tags,
            status=status
        )
        
        if post_id:
            print(f"\n✓ Post created successfully (ID: {post_id})")
            if status == 'draft':
                print(f"To publish: publish {post_id}")
    
    def cmd_edit(self, args):
        """Edit a post"""
        if not args or not args.strip().isdigit():
            print("Usage: edit <post_id>")
            return
        
        post_id = int(args.strip())
        post = self.post_mgr.get_post(post_id)
        
        if not post:
            print(f"Post {post_id} not found.")
            return
        
        # Check permission
        if not self.user_mgr.can_edit_post(self.current_user, post['author_callsign']):
            print("Error: You don't have permission to edit this post.")
            return
        
        print()
        print(self.formatter.format_separator("="))
        print(f"EDIT POST {post_id}")
        print(self.formatter.format_separator("="))
        print()
        
        # Show current values and get new ones
        print(f"Current title: {post['title']}")
        new_title = input("New title (press Enter to keep current): ").strip()
        
        print(f"\nCurrent category: {post.get('category') or 'None'}")
        new_category = input("New category (press Enter to keep current): ").strip()
        
        print(f"\nCurrent tags: {post.get('tags') or 'None'}")
        new_tags = input("New tags (press Enter to keep current): ").strip()
        
        print("\nCurrent content:")
        print(self.formatter.format_separator("-"))
        print(post['content'][:200] + "..." if len(post['content']) > 200 else post['content'])
        print(self.formatter.format_separator("-"))
        
        edit_content = input("\nEdit content? (y/n): ").strip().lower()
        new_content = None
        
        if edit_content == 'y':
            print("New content (type 'END' on a new line when finished):")
            content_lines = []
            while True:
                line = input()
                if line.strip().upper() == 'END':
                    break
                content_lines.append(line)
            new_content = '\n'.join(content_lines).strip()
        
        # Update post
        updates = {}
        if new_title:
            updates['title'] = new_title
        if new_category:
            updates['category'] = new_category
        if new_tags:
            updates['tags'] = new_tags
        if new_content:
            updates['content'] = new_content
        
        if updates:
            if self.post_mgr.update_post(post_id, **updates):
                print(f"\n✓ Post {post_id} updated successfully")
        else:
            print("\nNo changes made.")
    
    def cmd_delete(self, args):
        """Delete a post"""
        if not args or not args.strip().isdigit():
            print("Usage: delete <post_id>")
            return
        
        post_id = int(args.strip())
        post = self.post_mgr.get_post(post_id)
        
        if not post:
            print(f"Post {post_id} not found.")
            return
        
        # Check permission
        if not self.user_mgr.can_delete_post(self.current_user, post['author_callsign']):
            print("Error: You don't have permission to delete this post.")
            return
        
        # Confirm deletion
        print(f"\nPost: {post['title']}")
        confirm = input(f"Delete post {post_id}? This will also delete all comments. (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            if self.post_mgr.delete_post(post_id):
                print(f"✓ Post {post_id} deleted successfully")
        else:
            print("Deletion cancelled.")
    
    def cmd_publish(self, args):
        """Publish a draft post"""
        if not args or not args.strip().isdigit():
            print("Usage: publish <post_id>")
            return
        
        post_id = int(args.strip())
        post = self.post_mgr.get_post(post_id)
        
        if not post:
            print(f"Post {post_id} not found.")
            return
        
        # Check permission
        if not self.user_mgr.can_edit_post(self.current_user, post['author_callsign']):
            print("Error: You don't have permission to publish this post.")
            return
        
        if post['status'] == 'published':
            print(f"Post {post_id} is already published.")
            return
        
        self.post_mgr.publish_post(post_id)
    
    def cmd_unpublish(self, args):
        """Unpublish a post"""
        if not args or not args.strip().isdigit():
            print("Usage: unpublish <post_id>")
            return
        
        post_id = int(args.strip())
        post = self.post_mgr.get_post(post_id)
        
        if not post:
            print(f"Post {post_id} not found.")
            return
        
        # Check permission
        if not self.user_mgr.can_edit_post(self.current_user, post['author_callsign']):
            print("Error: You don't have permission to unpublish this post.")
            return
        
        if post['status'] == 'draft':
            print(f"Post {post_id} is already a draft.")
            return
        
        self.post_mgr.unpublish_post(post_id)
    
    def cmd_comment(self, args):
        """Add a comment to a post"""
        if not args or not args.strip().isdigit():
            print("Usage: comment <post_id>")
            return
        
        post_id = int(args.strip())
        post = self.post_mgr.get_post(post_id)
        
        if not post:
            print(f"Post {post_id} not found.")
            return
        
        # Can only comment on published posts (unless you're the author/admin)
        if post['status'] == 'draft':
            if not self.user_mgr.can_edit_post(self.current_user, post['author_callsign']):
                print("Cannot comment on draft posts.")
                return
        
        print()
        print(f"Adding comment to: {post['title']}")
        print(self.formatter.format_separator("-"))
        print("Comment (type 'END' on a new line when finished):")
        
        comment_lines = []
        while True:
            line = input()
            if line.strip().upper() == 'END':
                break
            comment_lines.append(line)
        
        content = '\n'.join(comment_lines).strip()
        
        if not content:
            print("Comment cannot be empty. Cancelled.")
            return
        
        self.comment_mgr.add_comment(post_id, self.current_user, content)
    
    def cmd_delete_comment(self, args):
        """Delete a comment"""
        if not args or not args.strip().isdigit():
            print("Usage: delcomment <comment_id>")
            return
        
        comment_id = int(args.strip())
        comment = self.comment_mgr.get_comment(comment_id)
        
        if not comment:
            print(f"Comment {comment_id} not found.")
            return
        
        # Check permission
        if not self.user_mgr.can_delete_comment(self.current_user, comment['author_callsign']):
            print("Error: You don't have permission to delete this comment.")
            return
        
        # Confirm deletion
        confirm = input(f"Delete comment {comment_id}? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            self.comment_mgr.delete_comment(comment_id)
    
    def cmd_search(self, args):
        """Search posts"""
        if not args:
            print("Usage: search <search_term>")
            return
        
        search_term = args.strip()
        
        # Search in published posts only for readers
        status = 'published' if self.current_user_data['role'] == 'reader' else None
        
        posts = self.post_mgr.search_posts(search_term, status=status)
        
        if not posts:
            print(f"No posts found matching '{search_term}'")
            return
        
        print()
        print(self.formatter.format_separator("="))
        print(f"SEARCH RESULTS: '{search_term}'")
        print(self.formatter.format_separator("="))
        print()
        
        for post in posts:
            print(self.formatter.format_post_list_item(post))
            print()
    
    def cmd_category(self, args):
        """Show posts in a category"""
        if not args:
            print("Usage: category <category_name>")
            return
        
        category = args.strip()
        
        # Show published posts only for readers
        status = 'published' if self.current_user_data['role'] == 'reader' else None
        
        posts = self.post_mgr.list_posts(status=status, category=category, limit=50)
        
        if not posts:
            print(f"No posts found in category '{category}'")
            return
        
        print()
        print(self.formatter.format_separator("="))
        print(f"CATEGORY: {category}")
        print(self.formatter.format_separator("="))
        print()
        
        for post in posts:
            print(self.formatter.format_post_list_item(post))
            print()
    
    def cmd_categories(self):
        """List all categories"""
        categories = self.post_mgr.get_categories()
        
        if not categories:
            print("No categories found.")
            return
        
        print()
        print(self.formatter.format_separator("="))
        print("CATEGORIES")
        print(self.formatter.format_separator("="))
        print()
        
        for category in categories:
            count = self.post_mgr.count_posts(category=category, status='published')
            print(f"  {category} ({count} post{'s' if count != 1 else ''})")
        
        print()
    
    def cmd_author(self, args):
        """Show posts by an author"""
        if not args:
            print("Usage: author <callsign>")
            return
        
        author = args.strip().upper()
        
        # Show published posts only for readers
        status = 'published' if self.current_user_data['role'] == 'reader' else None
        
        posts = self.post_mgr.list_posts(status=status, author=author, limit=50)
        
        if not posts:
            print(f"No posts found by {author}")
            return
        
        print()
        print(self.formatter.format_separator("="))
        print(f"POSTS BY: {author}")
        print(self.formatter.format_separator("="))
        print()
        
        for post in posts:
            print(self.formatter.format_post_list_item(post))
            print()
    
    def cmd_user(self, args):
        """User management (admin only)"""
        if not self.user_mgr.is_admin(self.current_user):
            print("Error: Only admins can manage users.")
            return
        
        parts = args.split(maxsplit=2)
        
        if not parts:
            print("Usage: user <list|add|role>")
            return
        
        subcmd = parts[0].lower()
        
        if subcmd == 'list':
            users = self.user_mgr.list_users()
            
            print()
            print(self.formatter.format_separator("="))
            print("USERS")
            print(self.formatter.format_separator("="))
            print()
            
            for user in users:
                date = self.formatter.format_datetime(user['created_at'])
                name = f" - {user['name']}" if user.get('name') else ""
                print(f"  {user['callsign']:<10} {user['role']:<10} {date}{name}")
            
            print()
        
        elif subcmd == 'add':
            if len(parts) < 3:
                print("Usage: user add <callsign> <role>")
                print("Roles: admin, author, reader")
                return
            
            callsign = parts[1].upper()
            role = parts[2].lower()
            
            self.user_mgr.add_user(callsign, role=role)
        
        elif subcmd == 'role':
            if len(parts) < 3:
                print("Usage: user role <callsign> <new_role>")
                print("Roles: admin, author, reader")
                return
            
            callsign = parts[1].upper()
            role = parts[2].lower()
            
            self.user_mgr.update_role(callsign, role)
        
        else:
            print(f"Unknown user command: {subcmd}")
            print("Available: list, add, role")
    
    def cmd_whoami(self):
        """Show current user info"""
        print()
        print(self.formatter.format_separator("-"))
        print(f"Callsign: {self.current_user_data['callsign']}")
        
        if self.current_user_data.get('name'):
            print(f"Name: {self.current_user_data['name']}")
        
        print(f"Role: {self.current_user_data['role']}")
        print(f"Member since: {self.formatter.format_datetime(self.current_user_data['created_at'])}")
        
        # Show post count
        post_count = self.post_mgr.count_posts(author=self.current_user)
        print(f"Posts: {post_count}")
        
        # Show comment count
        comments = self.comment_mgr.get_user_comments(self.current_user, limit=1000)
        print(f"Comments: {len(comments)}")
        
        print(self.formatter.format_separator("-"))

def main():
    """Main entry point"""
    config_path = "blog_config.json"
    
    if not os.path.exists(config_path):
        print("Error: blog_config.json not found")
        print("Please create the config file or run setup_blog.py first")
        return 1
    
    try:
        console = BlogConsole(config_path)
        console.start()
        return 0
    except KeyboardInterrupt:
        print("\n\n73! Goodbye!")
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        if 'console' in locals() and console.db:
            console.db.disconnect()

if __name__ == "__main__":
    sys.exit(main())
