"""
Web Search integration

Provides functionality to search the web using DuckDuckGo and retrieve content from search results.
"""

import logging
import httpx
from typing import Any, Dict, List
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import anyio

logger = logging.getLogger(__name__)

class WebSearchHandler:
    """Handler for web search functionality using DuckDuckGo."""
    
    def __init__(self):
        """Initialize the web search handler."""
        self.base_url = (
            "https://html.duckduckgo.com"  # Updated to use the correct domain
        )
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            ),
        }
    
    async def _get_vqd(self, client: httpx.AsyncClient, query: str) -> str:
        """
        Get the vqd token required for DuckDuckGo search.

        Args:
            client: HTTP client instance
            query: Search query

        Returns:
            vqd token string
        """
        # First, hit the main DDG page to harvest the vqd value
        r = await client.get("https://duckduckgo.com", params={"q": query})
        r.raise_for_status()
        m = re.search(r"vqd=([\d-]+)&", r.text)
        if not m:
            raise RuntimeError("Could not find vqd token")
        return m.group(1)
    
    async def search_web(
        self, query: str, max_results: int = 5
    ) -> Dict[str, Any]:
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
                # Get the vqd token required for search
                vqd = await self._get_vqd(client, query)
                
                # Perform the search with vqd token
                search_url = f"{self.base_url}/html/"
                params = {"q": query, "kl": "us-en", "vqd": vqd}
                
                response = await client.get(
                    search_url, params=params, follow_redirects=True
                )
                response.raise_for_status()
                
                # Parse the search results with updated selectors
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Use improved selector that works with current DuckDuckGo structure
                result_blocks = soup.select("div.result")
                
                for block in result_blocks[:max_results]:
                    try:
                        # Find the main result link
                        a = block.select_one("a.result__a")
                        if not a:  # Skip ads or malformed results
                            continue

                        # Extract basic information
                        title = a.get_text(" ", strip=True)
                        url = a.get("href", "")
                        
                        # Get snippet with fallback selectors
                        snippet_elem = block.select_one(
                            "div.result__snippet"
                        ) or block.select_one("span.result__snippet")
                        snippet = (
                            snippet_elem.get_text(" ", strip=True)
                            if snippet_elem
                            else ""
                        )
                        
                        # Try to fetch and extract content from the actual page
                        page_content = await self._extract_page_content(client, url)
                        
                        results.append(
                            {
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                                "content": (
                                    page_content[:500] + "..."
                                    if len(page_content) > 500
                                    else page_content
                                ),
                            }
                        )
                        
                    except Exception as e:
                        logger.warning(f"Error processing search result: {e}")
                        continue
                
                return {"success": True, "results": results, "error": None}
                
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"success": False, "results": [], "error": str(e)}
    
    def search_web_sync(
        self, query: str, max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Synchronous version of web search for compatibility.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with success status, results list, and any error message
        """
        try:
            # Try anyio first, fall back to asyncio if needed
            try:
                return anyio.run(self.search_web, query, max_results)
            except RuntimeError as e:
                if "asyncio" in str(e).lower():
                    # Fallback for environments where anyio doesn't work
                    import asyncio
                    
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # We're in an async context, create a new thread
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(
                                    asyncio.run, self.search_web(query, max_results)
                                )
                                return future.result()
                        else:
                            return loop.run_until_complete(
                                self.search_web(query, max_results)
                            )
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(
                                self.search_web(query, max_results)
                            )
                        finally:
                            loop.close()
                else:
                    raise
        except Exception as e:
            logger.error(f"Sync web search failed: {e}")
            return {"success": False, "results": [], "error": str(e)}
    
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
            
            # Enhanced headers to avoid blocking
            extra_headers = {
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml",
                "Referer": "https://duckduckgo.com/"
            }
            
            response = await client.get(
                url, 
                headers={**self.headers, **extra_headers},
                timeout=10.0,
                follow_redirects=True
            )
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
            
        except (httpx.HTTPStatusError, httpx.TimeoutException) as e:
            # Catch 4XX/5XX explicitly so one bad site doesn't kill the loop
            logger.warning(f"HTTP error fetching content from {url}: {e}")
            return "Content not available (HTTP error)"
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