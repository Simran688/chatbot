"""
Web search service for general knowledge queries.
Uses DuckDuckGo search (no API key required).
"""

import re
import json
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup

from app.core.config import settings


class WebSearchService:
    """
    Web search service using DuckDuckGo.
    Falls back to scraping if needed.
    """
    
    def __init__(self):
        self.timeout = 10.0
        self.max_results = 5
    
    async def search_duckduckgo(self, query: str) -> List[Dict[str, str]]:
        """
        Search using DuckDuckGo HTML interface.
        
        Args:
            query: Search query string
            
        Returns:
            List of search results with title, url, snippet
        """
        try:
            # DuckDuckGo HTML search URL
            search_url = "https://html.duckduckgo.com/html/"
            
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.post(
                    search_url,
                    data={"q": query, "kl": "us-en"}
                )
                response.raise_for_status()
                
                # Parse results
                results = self._parse_duckduckgo_results(response.text)
                return results[:self.max_results]
                
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []
    
    def _parse_duckduckgo_results(self, html: str) -> List[Dict[str, str]]:
        """
        Parse DuckDuckGo HTML results.
        
        Args:
            html: HTML response content
            
        Returns:
            List of parsed results
        """
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Find result containers
        for result in soup.find_all('div', class_='result'):
            try:
                # Extract title and URL
                title_elem = result.find('a', class_='result__a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                
                # Clean URL (DuckDuckGo wraps URLs)
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/'):
                    url = 'https://duckduckgo.com' + url
                
                # Extract snippet
                snippet_elem = result.find('a', class_='result__snippet')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                if title and url:
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
                    
            except Exception as e:
                continue
        
        return results
    
    async def search(self, query: str) -> List[Dict[str, str]]:
        """
        Perform web search.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        results = await self.search_duckduckgo(query)
        return results


# Global web search service instance
web_search_service = WebSearchService()
