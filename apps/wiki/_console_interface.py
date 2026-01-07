"""
Console interface for Wikipedia ZIM access
"""

import textwrap
from typing import List, Dict

class WikiConsoleInterface:
    """Console interface for Wikipedia ZIM access"""
    
    def __init__(self, zim_reader, default_max_chars=2000, rf_callsign="VA2OPS", zim_info=None):
        self.zim_reader = zim_reader
        self.current_article = None
        self.last_search_results = []
        self.default_max_chars = default_max_chars
        self.rf_callsign = rf_callsign
        self.zim_info = zim_info or {"name": "Unknown ZIM File", "description": "No description"}
    
    def start_interactive_session(self):
        """Start interactive console session"""
        print("=== Fixed Offline Wikipedia Console ===")
        print("Commands:")
        print("  search <query>     - Search for articles")
        print("  browse             - Browse available articles")
        print("  read <number>      - Read article by number from last search")
        print("  read <number> <length> - Read article with custom length (e.g. read 1 5000)")
        print("  find <n>        - Find how an article is stored in the archive")
        print("  debug <number>     - Debug a specific search result")
        print("  suggest <partial>  - Get title suggestions")
        print("  info               - Show ZIM file information")
        print("  test               - Test libzim API compatibility")
        print("  help               - Show this help")
        print("  quit               - Exit")
        print()
        
        while True:
            try:
                command = input("wiki> ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("73! Goodbye!")
                    break
                
                elif command.lower() == 'help':
                    self._show_help()
                
                elif command.lower() == 'info':
                    self._show_info()
                
                elif command.lower() == 'test':
                    self._test_api()
                
                elif command.lower() == 'browse':
                    self.last_search_results = self._handle_browse()
                
                elif command.lower().startswith('search '):
                    query = command[7:].strip()
                    if query:
                        self.last_search_results = self._handle_search(query)
                    else:
                        print("Usage: search <query>")
                
                elif command.lower().startswith('read '):
                    try:
                        parts = command[5:].strip().split()
                        article_num = int(parts[0]) - 1
                        # Optional length parameter
                        max_chars = self.default_max_chars  # use configured default
                        if len(parts) > 1:
                            max_chars = int(parts[1])
                        self._handle_read(self.last_search_results, article_num, max_chars)
                    except (ValueError, IndexError):
                        print("Usage: read <number> [max_chars]")
                        print("Example: read 1 3000  (read article 1 with max 3000 characters)")
                
                elif command.lower().startswith('suggest '):
                    partial = command[8:].strip()
                    if partial:
                        self._handle_suggestions(partial)
                    else:
                        print("Usage: suggest <partial_title>")
                
                elif command.lower().startswith('find '):
                    # New command to help diagnose missing articles
                    query = command[5:].strip()
                    if query:
                        self._handle_find(query)
                    else:
                        print("Usage: find <article_name>")
                
                elif command.lower().startswith('debug '):
                    # New command to debug search results
                    try:
                        article_num = int(command[6:].strip()) - 1
                        self._handle_debug_search_result(self.last_search_results, article_num)
                    except (ValueError, IndexError):
                        print("Usage: debug <number> (from last search results)")
                
                elif command.isdigit():
                    # Shortcut: allow just typing a number instead of "read <number>"
                    try:
                        article_num = int(command) - 1
                        self._handle_read(self.last_search_results, article_num, self.default_max_chars)
                    except (ValueError, IndexError):
                        print(f"Invalid article number. Choose 1-{len(self.last_search_results) if self.last_search_results else 0}")
                
                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\n73! Goodbye!")
                break
            except EOFError:
                print("\n73! Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _handle_browse(self) -> List[Dict]:
        """Handle browse command"""
        print("Browsing available articles...")
        results = self.zim_reader.browse_articles(max_results=20)
        
        if not results:
            print("No articles found to browse.")
            return []
        
        print(f"\nFirst {len(results)} articles:")
        print("-" * 50)
        
        for i, result in enumerate(results, 1):
            print(f"{i:2d}. {result['title']}")
            if result.get('snippet'):
                snippet = result['snippet'][:80] + "..." if len(result['snippet']) > 80 else result['snippet']
                print(f"     {snippet}")
            print()
        
        print("Use 'read <number>' to view an article")
        return results
    
    def _handle_search(self, query: str) -> List[Dict]:
        """Handle search command"""
        print(f"Searching for: {query}")
        results = self.zim_reader.search_articles(query, max_results=10)
        
        if not results:
            print("No results found.")
            print("Try:")
            print("1. Different search terms")
            print("2. 'suggest <word>' to find article titles")
            print("3. 'browse' to see available articles")
            return []
        
        print(f"\nFound {len(results)} results:")
        print("-" * 50)
        
        for i, result in enumerate(results, 1):
            print(f"{i:2d}. {result['title']}")
            if result.get('snippet'):
                # Wrap snippet text for console display
                snippet = result['snippet'][:120] + "..." if len(result['snippet']) > 120 else result['snippet']
                wrapped = textwrap.fill(snippet, width=70, initial_indent="     ", subsequent_indent="     ")
                print(wrapped)
            print()
        
        print("Use 'read <number>' to view an article")
        return results
    
    def _handle_read(self, search_results: List[Dict], article_index: int, max_chars: int = None):
        """Handle read command"""
        if max_chars is None:
            max_chars = self.default_max_chars
            
        if not search_results:
            print("No search results available. Search or browse first.")
            return
        
        if article_index < 0 or article_index >= len(search_results):
            print(f"Invalid article number. Choose 1-{len(search_results)}")
            return
        
        article = search_results[article_index]
        print(f"\n=== {article['title']} ===")
        print("=" * (len(str(article['title'])) + 8))
        
        # Get content with appropriate length for console display
        content = self.zim_reader.get_article_content(article['path'], max_chars=max_chars)
        if content:
            # Check if it's an error message
            if content.startswith("Error") or content.startswith("Article not found"):
                print(content)
                print("\nTroubleshooting suggestions:")
                print("1. Try a different article from the search results")
                print("2. Use 'test' command to check ZIM file compatibility")
                print("3. Try 'browse' to find articles that definitely exist")
            else:
                # Format for console display - preserve the spacing we added
                # Split by double newlines to preserve sentence spacing
                paragraphs = content.split('\n\n')
                formatted_paragraphs = []
                
                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if paragraph:
                        # Only wrap individual paragraphs, not the whole content
                        if paragraph.startswith('===') and paragraph.endswith('==='):
                            # Don't wrap headers
                            formatted_paragraphs.append(paragraph)
                        elif paragraph.startswith('•'):
                            # Don't wrap list items
                            formatted_paragraphs.append(paragraph)
                        else:
                            # Wrap long sentences but preserve spacing
                            wrapped = textwrap.fill(paragraph, width=72)
                            formatted_paragraphs.append(wrapped)
                
                # Join back with double newlines to preserve our spacing
                print('\n\n'.join(formatted_paragraphs))
        else:
            print("Unable to retrieve article content.")
        
        print("\n" + "=" * 50)
        self.current_article = article
    
    def _handle_find(self, query: str):
        """Find and display information about how articles are stored"""
        print(f"Searching for articles matching: '{query}'")
        
        # Since archive iteration doesn't work, try alternative approaches
        matches = []
        query_lower = query.lower()
        
        # Method 1: Try direct path construction and testing
        print("Trying direct path construction...")
        query_variants = [
            query,
            query.replace(' ', '_'),
            query.replace('_', ' '),
            query.title(),
            query.title().replace(' ', '_'),
            query.replace(':', '_'),
            query.replace(':', ''),
            query.replace("'", '_'),
            query.replace("'", ''),
        ]
        
        path_prefixes = ['A/', 'B/', 'C/', 'D/', 'E/', 'F/', 'G/', 'H/', 'I/', 'J/', 'K/', 'L/', 'M/', 'N/', 'O/', 'P/', 'Q/', 'R/', 'S/', 'T/', 'U/', 'V/', 'W/', 'X/', 'Y/', 'Z/', '']
        
        for variant in query_variants:
            for prefix in path_prefixes:
                test_path = f"{prefix}{variant}" if prefix else variant
                try:
                    if self.zim_reader.archive.has_entry_by_path(test_path):
                        entry = self.zim_reader.archive.get_entry_by_path(test_path)
                        title = self.zim_reader._safe_get_attribute(entry, 'title', test_path)
                        matches.append({
                            'title': title,
                            'path': test_path,
                            'method': 'direct_path'
                        })
                        print(f"✓ Found: '{test_path}' -> '{title}'")
                except:
                    continue
        
        # Method 2: Try suggestion-based search
        if self.zim_reader.suggestion_searcher:
            print("Trying suggestion-based search...")
            try:
                suggestions = self.zim_reader.get_suggestions(query.split()[0] if query.split() else query, 20)
                for suggestion in suggestions:
                    if query_lower in suggestion.lower():
                        # Try to find the actual path for this suggestion
                        for prefix in ['A/', 'B/', 'C/', 'D/', 'E/', 'F/', 'G/', 'H/', 'I/', 'J/', 'K/', 'L/', 'M/', 'N/', 'O/', 'P/', 'Q/', 'R/', 'S/', 'T/', 'U/', 'V/', 'W/', 'X/', 'Y/', 'Z/']:
                            test_path = f"{prefix}{suggestion.replace(' ', '_')}"
                            try:
                                if self.zim_reader.archive.has_entry_by_path(test_path):
                                    matches.append({
                                        'title': suggestion,
                                        'path': test_path,
                                        'method': 'suggestion'
                                    })
                                    print(f"✓ Found via suggestions: '{test_path}' -> '{suggestion}'")
                                    break
                            except:
                                continue
            except Exception as e:
                print(f"Suggestion search failed: {e}")
        
        # Method 3: Try a limited brute force with common patterns
        print("Trying common naming patterns...")
        words = query.split()
        if len(words) > 1:
            # Try different combinations
            patterns = [
                '_'.join(words),
                '_'.join(word.capitalize() for word in words),
                '_'.join(word.title() for word in words),
                ' '.join(words),
                ' '.join(word.capitalize() for word in words),
                ' '.join(word.title() for word in words),
            ]
            
            for pattern in patterns:
                for prefix in ['A/', 'P/', 'D/', 'M/', 'T/', 'L/', '']:  # Most common prefixes
                    test_path = f"{prefix}{pattern}" if prefix else pattern
                    try:
                        if self.zim_reader.archive.has_entry_by_path(test_path):
                            entry = self.zim_reader.archive.get_entry_by_path(test_path)
                            title = self.zim_reader._safe_get_attribute(entry, 'title', test_path)
                            matches.append({
                                'title': title,
                                'path': test_path,
                                'method': 'pattern_match'
                            })
                            print(f"✓ Found via pattern: '{test_path}' -> '{title}'")
                    except:
                        continue
        
        # Remove duplicates
        unique_matches = []
        seen_paths = set()
        for match in matches:
            if match['path'] not in seen_paths:
                unique_matches.append(match)
                seen_paths.add(match['path'])
        
        if unique_matches:
            print(f"\nFound {len(unique_matches)} unique matches:")
            print("-" * 60)
            
            for i, match in enumerate(unique_matches, 1):
                print(f"{i:2d}. Title: '{match['title']}'")
                print(f"     Path:  '{match['path']}'")
                print(f"     Method: {match['method']}")
                
                # Test accessibility
                try:
                    content = self.zim_reader.get_article_content(match['path'], 100)
                    if content and not content.startswith("Error") and not content.startswith("Article not found"):
                        print(f"     Status: ✓ Readable")
                    else:
                        print(f"     Status: ✗ Not readable")
                except:
                    print(f"     Status: ? Unknown")
                print()
        else:
            print("No matches found.")
            print("The article might be:")
            print("1. Stored under a completely different name")
            print("2. Not present in this ZIM file")
            print("3. Using a naming convention not covered by the search")
            print("\nTry: 'debug <number>' on a search result to see what's actually returned")

    def _handle_debug_search_result(self, search_results: List[Dict], article_index: int):
        """Debug what a search result actually contains"""
        if not search_results:
            print("No search results available. Search first.")
            return
        
        if article_index < 0 or article_index >= len(search_results):
            print(f"Invalid article number. Choose 1-{len(search_results)}")
            return
        
        result = search_results[article_index]
        print(f"\n=== Debugging Search Result #{article_index + 1} ===")
        print(f"Title: '{result['title']}'")
        print(f"Path: '{result['path']}'")
        print(f"Snippet: '{result.get('snippet', 'N/A')}'")
        print(f"URL: '{result.get('url', 'N/A')}'")
        
        # Test if the path exists
        if result['path']:
            try:
                exists = self.zim_reader.archive.has_entry_by_path(result['path'])
                print(f"Path exists in archive: {exists}")
                
                if exists:
                    try:
                        entry = self.zim_reader.archive.get_entry_by_path(result['path'])
                        actual_title = self.zim_reader._safe_get_attribute(entry, 'title', 'Unknown')
                        actual_path = self.zim_reader._safe_get_attribute(entry, 'path', 'Unknown')
                        print(f"Actual entry title: '{actual_title}'")
                        print(f"Actual entry path: '{actual_path}'")
                        
                        # Test if it's a redirect
                        try:
                            is_redirect = False
                            if hasattr(entry, 'is_redirect'):
                                redirect_attr = getattr(entry, 'is_redirect')
                                if callable(redirect_attr):
                                    is_redirect = redirect_attr()
                                else:
                                    is_redirect = bool(redirect_attr)
                            print(f"Is redirect: {is_redirect}")
                            
                            if is_redirect:
                                try:
                                    redirect_entry = entry.get_redirect_entry()
                                    redirect_path = self.zim_reader._safe_get_attribute(redirect_entry, 'path', 'Unknown')
                                    redirect_title = self.zim_reader._safe_get_attribute(redirect_entry, 'title', 'Unknown')
                                    print(f"Redirects to: '{redirect_path}' ('{redirect_title}')")
                                except Exception as e:
                                    print(f"Error following redirect: {e}")
                                    
                        except Exception as e:
                            print(f"Error checking redirect: {e}")
                            
                        # Test content retrieval
                        try:
                            item = entry.get_item()
                            content_length = len(bytes(item.content))
                            print(f"Content available: {content_length} bytes")
                        except Exception as e:
                            print(f"Error getting content: {e}")
                            
                    except Exception as e:
                        print(f"Error accessing entry: {e}")
                else:
                    print("Path does not exist in archive!")
                    
                    # Try some variations
                    print("Trying path variations...")
                    variations = [
                        result['path'].replace('_', ' '),
                        result['path'].replace(' ', '_'),
                        result['path'].replace(':', '_'),
                        result['path'].replace(':', ''),
                        result['path'].replace("'", '_'),
                        result['path'].replace("'", ''),
                    ]
                    
                    for var in variations:
                        if var != result['path']:
                            try:
                                if self.zim_reader.archive.has_entry_by_path(var):
                                    print(f"  ✓ Found variation: '{var}'")
                                    break
                            except:
                                continue
                    else:
                        print("  No working variations found")
                        
            except Exception as e:
                print(f"Error testing path: {e}")
        else:
            print("No path to test (empty path)")
        
        print("=" * 50)

    def _handle_suggestions(self, partial: str):
        """Handle suggestions command"""
        suggestions = self.zim_reader.get_suggestions(partial, max_results=10)
        
        if suggestions:
            print(f"Suggestions for '{partial}':")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i:2d}. {suggestion}")
        else:
            print(f"No suggestions found for '{partial}'")
    
    def _test_api(self):
        """Test libzim API compatibility"""
        print("=== libzim API Compatibility Test ===")
        
        # Test 1: Basic imports and versions
        try:
            import libzim
            print("✓ libzim imported successfully")
            if hasattr(libzim, '__version__'):
                print(f"  Version: {libzim.__version__}")
            else:
                print("  Version: Unknown")
        except Exception as e:
            print(f"✗ libzim import failed: {e}")
            return
        
        # Test 2: Archive properties
        try:
            archive = self.zim_reader.archive
            print("✓ Archive loaded successfully")
            print(f"  Entry count: {archive.entry_count}")
            print(f"  Has fulltext index: {archive.has_fulltext_index}")
            print(f"  Has title index: {archive.has_title_index}")
        except Exception as e:
            print(f"✗ Archive properties test failed: {e}")
        
        # Test 3: Suggestions
        try:
            suggestions = self.zim_reader.get_suggestions("test", 3)
            print(f"✓ Suggestions work: {len(suggestions)} found")
            if suggestions:
                print(f"  Examples: {suggestions[:2]}")
        except Exception as e:
            print(f"✗ Suggestions failed: {e}")
        
        # Test 4: Direct path access
        try:
            test_paths = ['A/Apple', 'A/Animal', 'F/France', 'P/Python', 'H/Hockey', 'M/Music']
            found_paths = []
            for path in test_paths:
                try:
                    if self.zim_reader.archive.has_entry_by_path(path):
                        found_paths.append(path)
                except:
                    continue
            
            if found_paths:
                print(f"✓ Direct path access works: {len(found_paths)} paths found")
                print(f"  Examples: {found_paths[:3]}")
            else:
                print("⚠ No test paths found (may be normal for some ZIM files)")
                
        except Exception as e:
            print(f"✗ Direct path access failed: {e}")
        
        # Test 5: Search functionality
        try:
            if self.zim_reader.searcher:
                print("✓ Search functionality available")
                test_results = self.zim_reader.search_articles("test", 1)
                print(f"  Test search returned {len(test_results)} results")
            else:
                print("⚠ No search functionality (ZIM file may lack fulltext index)")
        except Exception as e:
            print(f"✗ Search test failed: {e}")
        
        # Test 6: Content retrieval
        try:
            # Try to get content from a known path
            test_paths = ['A/Apple', 'A/Animal', 'F/France']
            for path in test_paths:
                try:
                    if self.zim_reader.archive.has_entry_by_path(path):
                        content = self.zim_reader.get_article_content(path, 100)
                        if content and not content.startswith("Error"):
                            print(f"✓ Content retrieval works (tested with {path})")
                            break
                except:
                    continue
            else:
                print("⚠ Content retrieval test skipped (no test articles found)")
        except Exception as e:
            print(f"✗ Content retrieval failed: {e}")
    
    def _show_info(self):
        """Show ZIM file information"""
        print(f"Current ZIM: {self.zim_info['name']}")
        print(f"Description: {self.zim_info['description']}")
        print(f"File path: {self.zim_reader.zim_file_path}")
        print(f"Default max chars: {self.default_max_chars}")
        print(f"RF callsign: {self.rf_callsign}")
        print("-" * 40)
        
        if self.zim_reader.archive:
            print(f"Entry count: {self.zim_reader.archive.entry_count}")
            print(f"Has fulltext index: {self.zim_reader.archive.has_fulltext_index}")
            print(f"Has title index: {self.zim_reader.archive.has_title_index}")
            print(f"Searcher available: {self.zim_reader.searcher is not None}")
            print(f"Suggestion searcher available: {self.zim_reader.suggestion_searcher is not None}")
        else:
            print("No ZIM file loaded")
    
    def _show_help(self):
        """Show help information"""
        print("""
Available Commands:
  search <query>     - Search for articles (uses multiple search methods)
  browse             - Browse available articles
  read <number>      - Read full article by number from last results
  read <number> <length> - Read article with custom length (e.g. read 1 5000)
  debug <number>     - Debug a specific search result to see what's wrong
  find <n>        - Find how an article is actually stored
  suggest <partial>  - Get article title suggestions
  info               - Show information about the ZIM file
  test               - Test libzim functionality and compatibility
  help               - Show this help message
  quit               - Exit the program

Examples:
  suggest hockey     # Find articles with "hockey" in title
  search hockey      # Search for hockey-related articles
  browse             # See what articles are available
  read 1             # Read first result from last search/browse
  find pink floyd    # See how Pink Floyd articles are stored

Troubleshooting:
  If "read" fails with "Article not found":
  1. Use "debug <number>" to see what's wrong with a search result
  2. Use "find <article_name>" to see the actual stored path
  3. Try other articles from the search results
  4. Use "browse" to find articles that definitely exist

Features:
- Multiple search methods (fulltext, suggestions, path guessing)
- Robust error handling for different libzim versions
- Content formatting optimized for console/RF display
- Automatic fallback when search indices are unavailable

This version includes improved error handling and compatibility fixes.
        """)
