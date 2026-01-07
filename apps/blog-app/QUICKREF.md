# BBS Blog Engine - Quick Reference Card

## Installation

```bash
# Option 1: Guided installation
python3 install.py

# Option 2: Manual installation
1. Edit blog_config.json
2. Create MySQL database
3. python3 setup_blog.py
```

## Starting the Blog

```bash
python3 blog.py
```

## Common Commands

### Reading Posts
```
list              # List recent posts
list 2            # Page 2
read 5            # Read post #5
search python     # Search for "python"
category Tech     # Posts in "Tech" category
author VA2OPS     # Posts by VA2OPS
```

### Creating Content (Authors/Admins)
```
new               # Create new post
comment 5         # Comment on post #5
edit 5            # Edit post #5
delete 5          # Delete post #5
publish 5         # Publish draft #5
unpublish 5       # Back to draft
```

### User Management (Admins)
```
user list              # List all users
user add VE2ABC author # Add author
user role VE2ABC admin # Make admin
whoami                 # Your info
```

## Roles

- **Reader**: View published posts, comment
- **Author**: Create posts, edit own posts
- **Admin**: Full access, manage users

## Database Quick Access

```bash
# Connect to database
mysql -u bbs_blog -p bbs_blog

# Useful queries
SELECT * FROM users;
SELECT id, title, author_callsign, status FROM posts;
SELECT COUNT(*) as count FROM posts WHERE status='published';
```

## Backup

```bash
# Backup database
mysqldump -u bbs_blog -p bbs_blog > backup.sql

# Restore database
mysql -u bbs_blog -p bbs_blog < backup.sql
```

## File Structure

```
blog/
├── blog.py                 # Main console interface
├── setup_blog.py           # Database setup
├── install.py              # Installation helper
├── blog_config.json        # Configuration
├── README.md               # Full documentation
├── QUICKREF.md             # This file
└── lib/
    ├── __init__.py         # Package init
    ├── database.py         # Database connection
    ├── user_manager.py     # User/permission handling
    ├── post_manager.py     # Post CRUD operations
    ├── comment_manager.py  # Comment handling
    └── formatter.py        # RF text formatting
```

## Troubleshooting

### Can't Connect
```bash
# Check MySQL is running
sudo systemctl status mariadb

# Test connection
mysql -u bbs_blog -p bbs_blog
```

### Permission Denied
```sql
-- Make yourself admin
UPDATE users SET role='admin' WHERE callsign='YOUR_CALL';
```

### Reset Database
```bash
python3 setup_blog.py  # Safe to re-run
```

## Tips

1. **Drafts**: Create posts as drafts, review, then publish
2. **Categories**: Use consistent category names
3. **Search**: Search works on title and content
4. **Line Length**: Auto-wrapped to 79 chars for RF
5. **Pagination**: Use `list 2`, `list 3` for more posts

## Example Post Creation

```
VA2OPS> new
Title: Installing LinBPQ on Raspberry Pi
Category (optional): Tutorial
Tags (comma-separated, optional): linbpq, raspberry pi, installation

Content (type 'END' on a new line when finished):
This guide will walk you through installing LinBPQ
on a Raspberry Pi 4 for packet radio operations.

Step 1: Update your system
sudo apt-get update && sudo apt-get upgrade

Step 2: Download LinBPQ
wget http://...
END

Publish now? (y/n, default=draft): n
✓ Post created successfully (ID: 1)

VA2OPS> read 1
[Reviews the post]

VA2OPS> publish 1
✓ Post 1 published
```

## Integration with BBS

The blog can be integrated into your LinBPQ BBS:

1. Create a wrapper script that passes callsign
2. Handle I/O through socket
3. Add as BBS application in linbpq.cfg

See your other BBS apps for examples.

## Support

For issues or questions:
- Check README.md for full documentation
- Review database schema in README.md
- Test with `whoami` and `user list` commands

73!
