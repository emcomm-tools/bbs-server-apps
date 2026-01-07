"""
ZIM file reading and content extraction logic
"""

import re
import os
from typing import List, Dict, Optional

try:
    from libzim.reader import Archive
    from libzim.search import Query, Searcher
    from libzim.suggestion import SuggestionSearcher
    LIBZIM_AVAILABLE = True
except ImportError:
    LIBZIM_AVAILABLE = False
    print("Warning: python-libzim not installed. Install with: pip install libzim")

class WikiZimReader:
    """Interface for reading Wikipedia ZIM files offline"""
    
    def __init__(self, zim_file_path: str, rf_callsign: str = "VA2GWM"):
        if not LIBZIM_AVAILABLE:
            raise ImportError("libzim is required. Install with: pip install libzim")
        
        if not os.path.exists(zim_file_path):
            raise FileNotFoundError(f"ZIM file not found: {zim_file_path}")
            
        self.zim_file_path = zim_file_path
        self.rf_callsign = rf_callsign
        self.archive = None
        self.searcher = None
        self.suggestion_searcher = None
        self._load_archive()
    
    def _load_archive(self):
        """Load the ZIM archive and initialize searchers"""
        try:
            self.archive = Archive(self.zim_file_path)
            
            # Only initialize searchers if indices are available
            if self.archive.has_fulltext_index:
                self.searcher = Searcher(self.archive)
            else:
                print("Warning: ZIM file has no fulltext index - search will be limited")
                
            if self.archive.has_title_index:
                self.suggestion_searcher = SuggestionSearcher(self.archive)
            else:
                print("Warning: ZIM file has no title index - suggestions will be limited")
                
            print(f"✓ Loaded ZIM file: {self.zim_file_path}")
            print(f"  Articles available: {self.archive.entry_count}")
            print(f"  Has fulltext index: {self.archive.has_fulltext_index}")
            print(f"  Has title index: {self.archive.has_title_index}")
            
            # Debug: Show libzim version info if available
            try:
                import libzim
                if hasattr(libzim, '__version__'):
                    print(f"  libzim version: {libzim.__version__}")
            except AttributeError:
                pass
                
        except Exception as e:
            raise Exception(f"Failed to load ZIM file: {e}")
    
    def browse_articles(self, max_results: int = 20) -> List[Dict]:
        """Browse available articles using iterator"""
        results = []
        try:
            print("Browsing articles using iterator...")
            
            count = 0
            for entry in self.archive:
                if count >= max_results:
                    break
                    
                try:
                    # Check if it's an article entry
                    if hasattr(entry, 'is_article') and entry.is_article():
                        title = self._safe_get_attribute(entry, 'title', 'Unknown')
                        path = self._safe_get_attribute(entry, 'path', '')
                        
                        # Skip empty titles or system entries
                        if title and not title.startswith(('-/', '_')):
                            results.append({
                                'title': title,
                                'path': path,
                                'snippet': f"Article entry",
                                'url': path
                            })
                            count += 1
                    else:
                        # Fallback for entries without is_article method
                        title = self._safe_get_attribute(entry, 'title', '')
                        path = self._safe_get_attribute(entry, 'path', '')
                        
                        # Skip system entries and empty titles
                        if title and not title.startswith(('-/', '_', 'File:', 'Category:')):
                            results.append({
                                'title': title,
                                'path': path,
                                'snippet': f"Entry",
                                'url': path
                            })
                            count += 1
                        
                except Exception as e:
                    # Log error but continue processing
                    print(f"Warning: Error processing entry: {e}")
                    continue
            
            print(f"Found {len(results)} browseable articles")
            
            # Filter out phantom results here too
            verified_results = []
            for result in results:
                if result['path']:
                    try:
                        if self.archive.has_entry_by_path(result['path']):
                            verified_results.append(result)
                    except:
                        continue
            
            if len(verified_results) < len(results):
                print(f"Filtered to {len(verified_results)} verified accessible articles")
                results = verified_results
            
            return results
            
        except Exception as e:
            print(f"Browse error: {e}")
            return self._browse_by_path()
    
    def _browse_by_path(self) -> List[Dict]:
        """Alternative browse method by trying common paths"""
        results = []
        common_articles = [
            'A/Albert_Einstein', 'A/Apple', 'A/Art', 'A/Animal', 'A/Africa',
            'B/Biology', 'B/Book', 'B/Bird', 'B/Brazil',
            'C/Computer', 'C/Cat', 'C/City', 'C/Culture', 'C/Canada',
            'D/Dog', 'D/Dance', 'D/Democracy', 'D/DNA',
            'E/Earth', 'E/Education', 'E/Energy', 'E/Europe',
            'F/France', 'F/Food', 'F/Fish', 'F/Football',
            'G/Germany', 'G/Game', 'G/Geography', 'G/Guitar',
            'H/History', 'H/Human', 'H/Health', 'H/Hockey',
            'I/Internet', 'I/Italy', 'I/India', 'I/Islam',
            'J/Japan', 'J/Jazz', 'J/Jupiter', 'J/Jesus',
            'M/Music', 'M/Mathematics', 'M/Medicine', 'M/Moon',
            'P/Physics', 'P/Python_(programming_language)', 'P/Philosophy', 'P/Paris',
            'S/Science', 'S/Space', 'S/Sport', 'S/Sun',
            'T/Technology', 'T/Tree', 'T/Time', 'T/Tennis',
            'W/Water', 'W/World', 'W/Wikipedia', 'W/War'
        ]
        
        print("Trying common article paths...")
        for path in common_articles:
            try:
                if self.archive.has_entry_by_path(path):
                    entry = self.archive.get_entry_by_path(path)
                    title = self._safe_get_attribute(entry, 'title', path.split('/')[-1])
                    
                    results.append({
                        'title': title,
                        'path': path,
                        'snippet': f"Found by path: {path}",
                        'url': path
                    })
                    if len(results) >= 20:
                        break
            except Exception as e:
                print(f"Warning: Error checking path {path}: {e}")
                continue
        
        return results
    
    def search_articles(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for articles matching the query"""
        if not query.strip():
            return []
            
        # If no searcher is available, use alternative methods
        if not self.searcher:
            print("No fulltext searcher available, using alternative search methods...")
            return self._alternative_search(query, max_results)
        
        try:
            print(f"Searching for: '{query}'")
            
            # Create and configure query
            search_query = Query()
            search_query.set_query(query)
            
            # Perform the search
            search_results = self.searcher.search(search_query)
            
            # Check estimated matches
            estimated_matches = search_results.getEstimatedMatches()
            print(f"Estimated matches: {estimated_matches}")
            
            if estimated_matches == 0:
                print("No fulltext matches found. Trying alternative search methods...")
                return self._alternative_search(query, max_results)
            
            # Extract results
            results = []
            try:
                # Get the results iterator
                search_iterator = search_results.getResults(0, max_results)
                
                # Try different methods to access results
                result_count = 0
                
                # Method 1: If iterator has size() method
                if hasattr(search_iterator, 'size'):
                    try:
                        size = search_iterator.size()
                        print(f"Result set size: {size}")
                        
                        for i in range(min(size, max_results)):
                            try:
                                entry = search_iterator[i]  # Array-style access
                                
                                title = self._safe_get_attribute(entry, 'title', 'Unknown')
                                path = self._safe_get_attribute(entry, 'path', '')
                                snippet = self._safe_get_attribute(entry, 'snippet', '')
                                
                                # Fix: If path is empty but title looks like a path, use title as path
                                if not path and title and ('/' in title or title.startswith('A/')):
                                    path = title
                                elif not path and title:
                                    # Try to construct a reasonable path from title
                                    path = f"A/{title.replace(' ', '_')}"
                                
                                results.append({
                                    'title': title,
                                    'path': path,
                                    'snippet': snippet,
                                    'url': path
                                })
                                result_count += 1
                            except Exception as e:
                                print(f"Warning: Error accessing result {i}: {e}")
                                continue
                                
                    except Exception as e:
                        print(f"Size-based iteration failed: {e}")
                
                # Method 2: Direct iteration
                if result_count == 0:
                    try:
                        for i, entry in enumerate(search_iterator):
                            if i >= max_results:
                                break
                            
                            title = self._safe_get_attribute(entry, 'title', 'Unknown')
                            path = self._safe_get_attribute(entry, 'path', '')
                            snippet = self._safe_get_attribute(entry, 'snippet', '')
                            
                            # Fix: If path is empty but title looks like a path, use title as path
                            if not path and title and ('/' in title or title.startswith('A/')):
                                path = title
                            elif not path and title:
                                # Try to construct a reasonable path from title
                                path = f"A/{title.replace(' ', '_')}"
                            
                            results.append({
                                'title': title,
                                'path': path,
                                'snippet': snippet,
                                'url': path
                            })
                            result_count += 1
                            
                    except Exception as e:
                        print(f"Direct iteration failed: {e}")
                
                # Debug: Show available methods if nothing worked
                if result_count == 0:
                    print("Debugging search results iterator...")
                    methods = [m for m in dir(search_iterator) if not m.startswith('_')]
                    print(f"Available methods: {methods}")
                
            except Exception as e:
                print(f"Error extracting search results: {e}")
            
            print(f"Found {len(results)} results from fulltext search")
            
            # Filter out phantom results
            results = self._filter_phantom_results(results)
            
            # If search didn't work or no verified results, try alternative methods
            if len(results) == 0:
                print("No accessible results from fulltext search. Trying alternative methods...")
                return self._alternative_search(query, max_results)
                
            return results
            
        except Exception as e:
            print(f"Search error: {e}")
            return self._alternative_search(query, max_results)
    
    def _filter_phantom_results(self, results: List[Dict]) -> List[Dict]:
        """Filter out search results that don't actually exist in the archive"""
        if not results:
            return results
            
        print("Filtering results to show only accessible articles...")
        verified_results = []
        
        for i, result in enumerate(results):
            print(f"Testing result {i+1}: '{result['title']}' -> '{result['path']}'")
            if result['path']:
                try:
                    # Check if the path actually exists
                    if self.archive.has_entry_by_path(result['path']):
                        print(f"  ✓ Path exists")
                        verified_results.append(result)
                    else:
                        print(f"  ✗ Path does not exist, trying variations...")
                        # Try to find a working alternative
                        alternative_found = False
                        variations = [
                            result['path'].replace('_', ' '),
                            result['path'].replace(' ', '_'),
                            result['path'].replace(':', '_'),
                            result['path'].replace(':', ''),
                            result['path'].replace("'", '_'),
                            result['path'].replace("'", ''),
                            result['path'].replace('"', '_'),
                            result['path'].replace('"', ''),
                        ]
                        
                        for variation in variations:
                            if variation != result['path']:
                                try:
                                    if self.archive.has_entry_by_path(variation):
                                        print(f"  ✓ Found working variation: '{variation}'")
                                        # Update the result with the working path
                                        result['path'] = variation
                                        result['url'] = variation
                                        verified_results.append(result)
                                        alternative_found = True
                                        break
                                except:
                                    continue
                        
                        if not alternative_found:
                            print(f"  ✗ No working variations found - skipping")
                except Exception as e:
                    print(f"  ✗ Error testing path: {e}")
            else:
                print(f"  ✗ Empty path - skipping")
        
        print(f"Final result: {len(verified_results)} verified accessible articles out of {len(results)} total")
        return verified_results
    
    def _safe_get_attribute(self, obj, attr_name: str, default: str = '') -> str:
        """Safely get an attribute value, handling both properties and methods"""
        try:
            if hasattr(obj, attr_name):
                attr = getattr(obj, attr_name)
                if callable(attr):
                    return str(attr())
                else:
                    return str(attr)
            return default
        except Exception as e:
            print(f"Warning: Error getting {attr_name}: {e}")
            return default
    
    def _alternative_search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Alternative search methods when fulltext search fails"""
        print("Using alternative search approaches...")
        
        results = []
        
        # Method 1: Try suggestion-based search
        if self.suggestion_searcher:
            try:
                query_words = query.lower().split()
                for word in query_words:
                    if len(word) > 2:  # Skip very short words
                        suggestions = self.get_suggestions(word, max_results * 2)
                        
                        for suggestion in suggestions:
                            if any(q_word in suggestion.lower() for q_word in query_words):
                                # Try to find the actual article
                                potential_paths = self._generate_potential_paths(suggestion)
                                
                                for path in potential_paths:
                                    try:
                                        if self.archive.has_entry_by_path(path):
                                            results.append({
                                                'title': suggestion,
                                                'path': path,
                                                'snippet': f"Found via suggestions for '{word}'",
                                                'url': path
                                            })
                                            break
                                    except:
                                        continue
                                        
                                if len(results) >= max_results:
                                    break
                        
                        if len(results) >= max_results:
                            break
                            
            except Exception as e:
                print(f"Suggestion-based search failed: {e}")
        
        # Method 2: Direct path guessing
        if len(results) < max_results:
            path_results = self._search_by_path_guessing(query, max_results - len(results))
            results.extend(path_results)
        
        return results
    
    def _generate_potential_paths(self, title: str) -> List[str]:
        """Generate potential article paths for a title"""
        title_clean = title.replace(' ', '_')
        first_letter = title_clean[0].upper() if title_clean else 'A'
        
        return [
            f"{first_letter}/{title_clean}",
            f"A/{title_clean}",
            title_clean,
            f"{first_letter}/{title}",
            f"A/{title}",
            title
        ]
    
    def _search_by_path_guessing(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search by guessing article paths"""
        results = []
        query_words = [word.strip() for word in query.split() if len(word.strip()) > 2]
        
        # Generate potential article paths
        potential_articles = []
        
        for word in query_words:
            word_variations = [
                word.capitalize(),
                word.upper(),
                word.lower(),
                word.title()
            ]
            
            for variation in word_variations:
                potential_articles.extend([
                    f"{variation[0].upper()}/{variation}",
                    f"A/{variation}",
                    variation
                ])
        
        # Try combinations of words
        if len(query_words) > 1:
            for i in range(len(query_words)):
                for j in range(i + 1, len(query_words) + 1):
                    combined_words = query_words[i:j]
                    combined = "_".join(word.capitalize() for word in combined_words)
                    
                    potential_articles.extend([
                        f"{combined[0]}/{combined}",
                        f"A/{combined}",
                        combined
                    ])
        
        print(f"Trying {len(set(potential_articles))} potential paths...")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_articles = []
        for path in potential_articles:
            if path not in seen:
                seen.add(path)
                unique_articles.append(path)
        
        for path in unique_articles:
            try:
                if self.archive.has_entry_by_path(path):
                    entry = self.archive.get_entry_by_path(path)
                    title = self._safe_get_attribute(entry, 'title', path.split('/')[-1])
                    
                    results.append({
                        'title': title,
                        'path': path,
                        'snippet': f"Found by path guessing: {path}",
                        'url': path
                    })
                    
                    if len(results) >= max_results:
                        break
                        
            except Exception as e:
                continue
        
        return results
    
    def get_article_content(self, article_path: str, max_chars: int = 2000) -> Optional[str]:
        """Get article content by path, formatted for text display"""
        try:
            # Try the path as-is first
            if self.archive.has_entry_by_path(article_path):
                entry = self.archive.get_entry_by_path(article_path)
            else:
                # Try alternative path formats
                alternative_paths = []
                
                # If path starts with a letter and slash, try without the prefix
                if '/' in article_path and len(article_path.split('/')) == 2:
                    alternative_paths.append(article_path.split('/', 1)[1])
                
                # Try with 'A/' prefix if not already there
                if not article_path.startswith('A/'):
                    alternative_paths.append(f"A/{article_path}")
                
                # Try URL decoding in case of encoded characters
                try:
                    import urllib.parse
                    decoded_path = urllib.parse.unquote(article_path)
                    if decoded_path != article_path:
                        alternative_paths.append(decoded_path)
                except:
                    pass
                
                # Try replacing underscores with spaces and vice versa
                if '_' in article_path:
                    alternative_paths.append(article_path.replace('_', ' '))
                if ' ' in article_path:
                    alternative_paths.append(article_path.replace(' ', '_'))
                
                # Try handling special characters (colons, apostrophes, etc.)
                if ':' in article_path:
                    alternative_paths.append(article_path.replace(':', '_'))
                    alternative_paths.append(article_path.replace(':', ''))
                if "'" in article_path:
                    alternative_paths.append(article_path.replace("'", '_'))
                    alternative_paths.append(article_path.replace("'", ''))
                if '"' in article_path:
                    alternative_paths.append(article_path.replace('"', '_'))
                    alternative_paths.append(article_path.replace('"', ''))
                
                # Try URL-safe versions
                safe_path = re.sub(r'[^\w\s/]', '_', article_path)
                if safe_path != article_path:
                    alternative_paths.append(safe_path)
                
                entry = None
                for alt_path in alternative_paths:
                    try:
                        if self.archive.has_entry_by_path(alt_path):
                            entry = self.archive.get_entry_by_path(alt_path)
                            article_path = alt_path  # Update for redirect handling
                            break
                    except Exception:
                        continue
                
                if not entry:
                    # Last resort: try to find by iterating through archive
                    article_name = article_path.split('/')[-1] if '/' in article_path else article_path
                    
                    try:
                        count = 0
                        for archive_entry in self.archive:
                            if count > 2000:  # Increased search limit
                                break
                            try:
                                entry_title = self._safe_get_attribute(archive_entry, 'title', '')
                                entry_path = self._safe_get_attribute(archive_entry, 'path', '')
                                
                                # More flexible matching
                                if (article_name.lower().replace('_', ' ') in entry_title.lower().replace('_', ' ') or
                                    article_name.lower().replace(' ', '_') in entry_path.lower().replace(' ', '_') or
                                    entry_title.lower().replace('_', ' ') == article_name.lower().replace('_', ' ')):
                                    entry = archive_entry
                                    article_path = entry_path
                                    break
                                count += 1
                            except:
                                continue
                    except Exception:
                        pass
                
                if not entry:
                    return f"Article not found: '{article_path}'"
            
            # Handle redirects
            try:
                # Check if entry has redirect methods and handle different API versions
                is_redirect = False
                if hasattr(entry, 'is_redirect'):
                    redirect_attr = getattr(entry, 'is_redirect')
                    if callable(redirect_attr):
                        is_redirect = redirect_attr()
                    else:
                        is_redirect = bool(redirect_attr)
                
                if is_redirect:
                    try:
                        redirect_entry = entry.get_redirect_entry()
                        redirect_path = self._safe_get_attribute(redirect_entry, 'path', article_path)
                        return self.get_article_content(redirect_path, max_chars)
                    except Exception:
                        # Continue with original entry
                        pass
                    
            except Exception:
                # Continue with original entry
                pass
            
            # Get content
            try:
                item = entry.get_item()
                content_data = item.content
                
                # Handle different content data types
                if hasattr(content_data, 'tobytes'):
                    # If it's a memoryview or similar
                    content_bytes = content_data.tobytes()
                elif isinstance(content_data, (bytes, bytearray)):
                    content_bytes = bytes(content_data)
                else:
                    # Try to convert to bytes
                    content_bytes = bytes(content_data)
                
                content = content_bytes.decode('utf-8', errors='replace')
                
            except Exception as e:
                return f"Error retrieving content: {e}"
            
            # Convert HTML to text
            text_content = self._html_to_text(content)
            
            # Truncate if too long (only if max_chars is specified)
            if max_chars is not None and len(text_content) > max_chars:
                text_content = text_content[:max_chars] + f"\n\n--- 73 DE {self.rf_callsign} ---\n[Article truncated for RF transmission]\n[Use 'read <number> <length>' for more content]"
            
            return text_content
            
        except Exception as e:
            return f"Error retrieving article '{article_path}': {e}"
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to readable text"""
        if not html_content:
            return "No content available."
            
        # Remove script and style elements
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert headers to text format
        html_content = re.sub(r'<h([1-6])[^>]*>(.*?)</h\1>', r'\n\n\n=== \2 ===\n\n', html_content, flags=re.DOTALL)
        
        # Handle paragraphs and line breaks
        html_content = re.sub(r'<p[^>]*>', '\n\n', html_content)
        html_content = re.sub(r'</p>', '', html_content)
        html_content = re.sub(r'<br[^>]*/?>', '\n\n', html_content)
        
        # Convert lists
        html_content = re.sub(r'<li[^>]*>', '\n\n• ', html_content)
        html_content = re.sub(r'</li>', '', html_content)
        html_content = re.sub(r'<[/]?[ou]l[^>]*>', '\n\n', html_content)
        
        # Remove all remaining HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities
        html_content = html_content.replace('&amp;', '&')
        html_content = html_content.replace('&lt;', '<')
        html_content = html_content.replace('&gt;', '>')
        html_content = html_content.replace('&quot;', '"')
        html_content = html_content.replace('&#39;', "'")
        html_content = html_content.replace('&nbsp;', ' ')
        
        # Clean up whitespace first
        html_content = re.sub(r'[ \t]+', ' ', html_content)
        html_content = re.sub(r' *\n *', '\n', html_content)
        
        # Split into sentences and add spacing for RF readability
        sentences = []
        current_sentence = ""
        
        for line in html_content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Handle headers (lines with ===)
            if line.startswith('===') and line.endswith('==='):
                if current_sentence:
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
                sentences.append(line)
                continue
            
            # Handle list items - skip empty ones
            if line.startswith('•'):
                # Only add non-empty list items
                list_content = line[1:].strip()  # Remove bullet and whitespace
                if list_content:  # Only if there's actual content after the bullet
                    if current_sentence:
                        sentences.append(current_sentence.strip())
                        current_sentence = ""
                    sentences.append(line)
                continue
            
            # Accumulate text for sentence detection
            current_sentence += " " + line
            
            # Look for sentence endings
            sentence_endings = re.findall(r'[^.!?]*[.!?]+', current_sentence)
            if sentence_endings:
                for ending in sentence_endings:
                    sentences.append(ending.strip())
                # Keep any remaining text that doesn't end with punctuation
                remaining = re.sub(r'[^.!?]*[.!?]+', '', current_sentence)
                current_sentence = remaining.strip()
        
        # Add any remaining text
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # Join sentences with double line breaks for RF readability
        formatted_content = ""
        for sentence in sentences:
            if sentence.strip():
                formatted_content += sentence.strip() + "\n\n"
        
        return formatted_content.strip()
    
    def get_suggestions(self, partial_query: str, max_results: int = 5) -> List[str]:
        """Get article title suggestions for partial queries"""
        if not self.suggestion_searcher:
            print("No suggestion searcher available")
            return []
        
        try:
            suggestions_result = self.suggestion_searcher.suggest(partial_query)
            results = []
            
            # Handle different suggestion result formats
            if hasattr(suggestions_result, 'size'):
                try:
                    size = suggestions_result.size()
                    for i in range(min(max_results, size)):
                        try:
                            entry = suggestions_result.get_result(i)
                            title = self._safe_get_attribute(entry, 'title', str(entry))
                            if title:
                                results.append(title)
                        except Exception as e:
                            print(f"Warning: Error getting suggestion {i}: {e}")
                            continue
                except Exception as e:
                    print(f"Error using size() method: {e}")
            
            # Try iteration if size method failed
            if not results and hasattr(suggestions_result, '__iter__'):
                try:
                    for i, entry in enumerate(suggestions_result):
                        if i >= max_results:
                            break
                        title = self._safe_get_attribute(entry, 'title', str(entry))
                        if title:
                            results.append(title)
                except Exception as e:
                    print(f"Error iterating suggestions: {e}")
            
            return results
            
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []
