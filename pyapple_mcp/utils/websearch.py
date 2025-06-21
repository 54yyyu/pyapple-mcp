"""
Web Search integration

Provides functionality to search the web using DuckDuckGo and retrieve content from search results.
"""

import logging
import httpx
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class WebSearchHandler:
    """Handler for web search functionality using DuckDuckGo."""
    
    def __init__(self):
        """Initialize the web search handler."""
        self.base_url = "https://duckduckgo.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def search_web(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search the web using DuckDuckGo and retrieve content from results.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with success status, results list, and any error message
        """
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=self.headers) as client:
                # First, get the search results page
                search_url = f"{self.base_url}/html/"
                params = {
                    'q': query,
                    'kl': 'us-en'
                }
                
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                
                # Parse the search results
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Find search result links
                result_links = soup.find_all('a', {'class': 'result__a'})
                
                for i, link in enumerate(result_links[:max_results]):
                    try:
                        # Extract basic information
                        title = link.get_text(strip=True)
                        url = link.get('href', '')
                        
                        # Get snippet from the result container
                        result_container = link.find_parent('div', {'class': 'result'})
                        snippet = ""
                        if result_container:
                            snippet_elem = result_container.find('div', {'class': 'result__snippet'})
                            if snippet_elem:
                                snippet = snippet_elem.get_text(strip=True)
                        
                        # Try to fetch and extract content from the actual page
                        page_content = await self._extract_page_content(client, url)
                        
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'content': page_content[:500] + "..." if len(page_content) > 500 else page_content
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error processing search result {i}: {e}")
                        continue
                
                return {
                    'success': True,
                    'results': results,
                    'error': None
                }
                
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {
                'success': False,
                'results': [],
                'error': str(e)
            }
    
    def search_web_sync(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Synchronous version of web search for compatibility.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with success status, results list, and any error message
        """
        import asyncio
        
        try:
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(self.search_web(query, max_results))
        except Exception as e:
            logger.error(f"Sync web search failed: {e}")
            return {
                'success': False,
                'results': [],
                'error': str(e)
            }
    
    async def _extract_page_content(self, client: httpx.AsyncClient, url: str) -> str:
        """
        Extract readable content from a web page.
        
        Args:
            client: HTTP client instance
            url: URL to extract content from
            
        Returns:
            Extracted text content
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return "Invalid URL"
            
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            
            # Parse the page content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "meta", "link"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
            
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {e}")
            return "Content not available"

# For compatibility with synchronous calls in the main server
def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Convenience function for synchronous web search.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary with success status, results list, and any error message
    """
    handler = WebSearchHandler()
    return handler.search_web_sync(query, max_results) 