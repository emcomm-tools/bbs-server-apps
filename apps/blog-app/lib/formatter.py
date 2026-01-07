#!/usr/bin/env python3
"""
Text Formatter for BBS Blog Engine
Formats content for RF/telnet display (79 char max)
"""

import textwrap
from datetime import datetime
from typing import List, Dict

class RFFormatter:
    """Format text for RF/packet radio transmission"""
    
    def __init__(self, max_line_length: int = 79):
        self.max_line_length = max_line_length
    
    def wrap_text(self, text: str, indent: str = "") -> str:
        """Wrap text to max line length"""
        if not text:
            return ""
        
        # Handle multiple paragraphs
        paragraphs = text.split('\n')
        wrapped_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                wrapped = textwrap.fill(
                    paragraph.strip(),
                    width=self.max_line_length,
                    initial_indent=indent,
                    subsequent_indent=indent
                )
                wrapped_paragraphs.append(wrapped)
            else:
                wrapped_paragraphs.append("")  # Preserve blank lines
        
        return '\n'.join(wrapped_paragraphs)
    
    def format_header(self, text: str, char: str = "=") -> str:
        """Create a header line"""
        header_line = char * min(len(text) + 4, self.max_line_length)
        return f"{header_line}\n{text.center(len(header_line))}\n{header_line}"
    
    def format_separator(self, char: str = "-") -> str:
        """Create a separator line"""
        return char * self.max_line_length
    
    def format_datetime(self, dt) -> str:
        """Format datetime for display"""
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except:
                return dt
        
        return dt.strftime("%Y-%m-%d %H:%M") if dt else ""
    
    def format_post_list_item(self, post: Dict, index: int = None) -> str:
        """Format a post for list display"""
        output = []
        
        # Post ID and title
        post_id = post.get('id', '?')
        title = f"[{post_id}] {post['title']}"
        
        if len(title) > self.max_line_length:
            title = title[:self.max_line_length-3] + "..."
        
        output.append(title)
        
        # Author and date
        author = post.get('author_name') or post['author_callsign']
        date = self.format_datetime(post['created_at'])
        category = f" [{post['category']}]" if post.get('category') else ""
        status = f" ({post['status']})" if post.get('status') == 'draft' else ""
        comment_count = post.get('comment_count', 0)
        comments = f" - {comment_count} comment{'s' if comment_count != 1 else ''}" if comment_count else ""
        
        meta = f"   By: {author} | {date}{category}{status}{comments}"
        output.append(meta)
        
        return '\n'.join(output)
    
    def format_post_full(self, post: Dict) -> str:
        """Format a full post for reading"""
        output = []
        
        # Title header
        output.append(self.format_header(post['title']))
        output.append("")
        
        # Metadata
        author = post.get('author_name') or post['author_callsign']
        date = self.format_datetime(post['created_at'])
        output.append(f"By: {author} ({post['author_callsign']})")
        output.append(f"Published: {date}")
        
        if post.get('category'):
            output.append(f"Category: {post['category']}")
        
        if post.get('tags'):
            output.append(f"Tags: {post['tags']}")
        
        if post.get('status') == 'draft':
            output.append("Status: DRAFT")
        
        output.append("")
        output.append(self.format_separator())
        output.append("")
        
        # Content
        content = self.wrap_text(post['content'])
        output.append(content)
        
        output.append("")
        output.append(self.format_separator())
        
        return '\n'.join(output)
    
    def format_comment(self, comment: Dict, index: int = None) -> str:
        """Format a comment for display"""
        output = []
        
        # Header
        author = comment.get('author_name') or comment['author_callsign']
        date = self.format_datetime(comment['created_at'])
        prefix = f"Comment #{index} - " if index else "Comment - "
        header = f"{prefix}{author} ({comment['author_callsign']}) - {date}"
        
        output.append(header)
        output.append(self.format_separator("-"))
        
        # Content
        content = self.wrap_text(comment['content'])
        output.append(content)
        
        return '\n'.join(output)
    
    def format_help(self, commands: Dict[str, str]) -> str:
        """Format help text"""
        output = []
        output.append(self.format_header("BBS BLOG ENGINE - HELP"))
        output.append("")
        output.append("Available Commands:")
        output.append(self.format_separator("-"))
        
        for cmd, desc in commands.items():
            cmd_line = f"  {cmd:<20} - {desc}"
            if len(cmd_line) > self.max_line_length:
                # Wrap description
                wrapped = textwrap.fill(
                    desc,
                    width=self.max_line_length - 25,
                    initial_indent=f"  {cmd:<20} - ",
                    subsequent_indent=" " * 25
                )
                output.append(wrapped)
            else:
                output.append(cmd_line)
        
        output.append(self.format_separator("-"))
        return '\n'.join(output)
    
    def format_banner(self, callsign: str, role: str) -> str:
        """Format welcome banner"""
        output = []
        output.append(self.format_header("BBS BLOG ENGINE", "="))
        output.append("")
        output.append(f"Logged in as: {callsign} ({role})")
        output.append("")
        output.append("Type 'help' for available commands")
        output.append(self.format_separator("="))
        return '\n'.join(output)
