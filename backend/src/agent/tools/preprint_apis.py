"""Preprint Server APIs for HypothesisAI Literature Hunter Agent.

Implementation for major preprint servers including arXiv.
"""

import asyncio
import aiohttp
import xmltodict
import feedparser
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import re
from urllib.parse import quote
from ratelimit import limits, sleep_and_retry
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Paper:
    """Unified paper representation across preprint servers."""
    id: str
    title: str
    abstract: str
    authors: List[str]
    date_published: datetime
    source: str
    url: str
    categories: List[str] = field(default_factory=list)
    doi: Optional[str] = None
    citations: int = 0
    version: int = 1
    pdf_url: Optional[str] = None
    relevance_score: float = 0.0
    quality_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PreprintAPI(ABC):
    """Abstract base class for preprint server APIs."""
    
    def __init__(self, rate_limit: Tuple[int, int] = (3, 1)):
        """Initialize with rate limiting configuration."""
        self.session = None
        self.rate_limit = rate_limit
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 100) -> List[Paper]:
        """Search for papers matching the query"""
        pass
    
    @abstractmethod
    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Retrieve a specific paper by ID"""
        pass
    
    def calculate_relevance(self, paper: Paper, query: str) -> float:
        """Calculate relevance score using TF-IDF similarity"""
        documents = [query, f"{paper.title} {paper.abstract}"]
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(documents)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    
    def calculate_quality(self, paper: Paper) -> float:
        """Calculate quality score based on various metrics"""
        score = 0.0
        
        # Recency bonus (papers from last 2 years)
        days_old = (datetime.now() - paper.date_published).days
        if days_old < 730:  # 2 years
            score += max(0, (730 - days_old) / 730) * 0.3
        
        # Abstract length (ideal: 150-300 words)
        abstract_words = len(paper.abstract.split())
        if 150 <= abstract_words <= 300:
            score += 0.2
        elif abstract_words > 100:
            score += 0.1
        
        # Number of authors (collaborative work tends to be higher quality)
        if 2 <= len(paper.authors) <= 10:
            score += 0.2
        elif len(paper.authors) > 10:
            score += 0.1
        
        # Version number (updated papers show engagement)
        if paper.version > 1:
            score += min(0.2, paper.version * 0.05)
        
        # Citation count (if available)
        if paper.citations > 0:
            score += min(0.3, np.log(paper.citations + 1) / 10)
        
        return min(1.0, score)


class ArxivAPI(PreprintAPI):
    """arXiv API implementation"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    @sleep_and_retry
    @limits(calls=3, period=1)  # 3 requests per second
    async def search(self, query: str, max_results: int = 100) -> List[Paper]:
        """
        Search arXiv using their API
        Query syntax: https://arxiv.org/help/api/user-manual#query_details
        """
        # Build advanced query
        search_query = self._build_query(query)
        
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        async with self.session.get(self.BASE_URL, params=params) as response:
            xml_data = await response.text()
            
        return self._parse_arxiv_response(xml_data, query)
    
    def _build_query(self, query: str) -> str:
        """Build advanced arXiv query"""
        # Search in title, abstract, and comments
        terms = []
        
        # Split query into individual terms
        keywords = query.split()
        
        # Search in multiple fields
        for keyword in keywords:
            if len(keyword) > 2:  # Skip very short words
                terms.append(f'(ti:"{keyword}" OR abs:"{keyword}")')
        
        return ' AND '.join(terms)
    
    def _parse_arxiv_response(self, xml_data: str, query: str) -> List[Paper]:
        """Parse arXiv XML response"""
        parsed = xmltodict.parse(xml_data)
        papers = []
        
        if 'feed' not in parsed or 'entry' not in parsed['feed']:
            return papers
        
        entries = parsed['feed']['entry']
        if not isinstance(entries, list):
            entries = [entries]
        
        for entry in entries:
            try:
                # Extract authors
                authors = []
                author_data = entry.get('author', [])
                if not isinstance(author_data, list):
                    author_data = [author_data]
                authors = [a.get('name', '') for a in author_data]
                
                # Extract categories
                categories = []
                category_data = entry.get('category', [])
                if not isinstance(category_data, list):
                    category_data = [category_data]
                categories = [c.get('@term', '') for c in category_data]
                
                # Parse date
                published = datetime.strptime(
                    entry['published'][:10], '%Y-%m-%d'
                )
                
                # Extract version from ID
                arxiv_id = entry['id'].split('/')[-1]
                version = 1
                if 'v' in arxiv_id:
                    version = int(arxiv_id.split('v')[-1])
                
                paper = Paper(
                    id=arxiv_id,
                    title=entry.get('title', '').replace('\n', ' ').strip(),
                    abstract=entry.get('summary', '').replace('\n', ' ').strip(),
                    authors=authors,
                    date_published=published,
                    source='arxiv',
                    url=entry.get('id', ''),
                    categories=categories,
                    doi=entry.get('arxiv:doi', {}).get('#text') if 'arxiv:doi' in entry else None,
                    version=version,
                    pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                    metadata={
                        'comment': entry.get('arxiv:comment', {}).get('#text', '') if 'arxiv:comment' in entry else ''
                    }
                )
                
                # Calculate scores
                paper.relevance_score = self.calculate_relevance(paper, query)
                paper.quality_score = self.calculate_quality(paper)
                
                papers.append(paper)
                
            except Exception as e:
                print(f"Error parsing arXiv entry: {e}")
                continue
        
        return papers
    
    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Get specific paper by arXiv ID"""
        params = {
            'id_list': paper_id,
            'max_results': 1
        }
        
        async with self.session.get(self.BASE_URL, params=params) as response:
            xml_data = await response.text()
        
        papers = self._parse_arxiv_response(xml_data, "")
        return papers[0] if papers else None


class BioRxivAPI(PreprintAPI):
    """bioRxiv/medRxiv API implementation"""
    
    BASE_URL = "https://api.biorxiv.org"
    
    def __init__(self, server: str = "biorxiv", rate_limit: Tuple[int, int] = (3, 1)):
        """
        Args:
            server: 'biorxiv' or 'medrxiv'
        """
        super().__init__(rate_limit)
        self.server = server
    
    @sleep_and_retry
    @limits(calls=3, period=1)
    async def search(self, query: str, max_results: int = 100) -> List[Paper]:
        """
        Search bioRxiv/medRxiv
        Note: Their API is limited, so we use metadata endpoint + filtering
        """
        # Get recent papers and filter
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        papers = []
        cursor = 0
        
        while len(papers) < max_results:
            url = f"{self.BASE_URL}/details/{self.server}/{start_date}/{end_date}/{cursor}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    break
                    
                data = await response.json()
                
                if 'collection' not in data or not data['collection']:
                    break
                
                for item in data['collection']:
                    # Basic text matching (their API doesn't support full-text search)
                    if self._matches_query(item, query):
                        paper = self._parse_biorxiv_paper(item, query)
                        papers.append(paper)
                        
                        if len(papers) >= max_results:
                            break
                
                cursor += len(data['collection'])
                
                # Their API returns max 100 per request
                if len(data['collection']) < 100:
                    break
        
        return papers[:max_results]
    
    def _matches_query(self, item: dict, query: str) -> bool:
        """Check if paper matches query terms"""
        query_lower = query.lower()
        keywords = query_lower.split()
        
        searchable_text = f"{item.get('title', '')} {item.get('abstract', '')}".lower()
        
        # Require at least half of the keywords to match
        matches = sum(1 for keyword in keywords if keyword in searchable_text)
        return matches >= len(keywords) / 2
    
    def _parse_biorxiv_paper(self, item: dict, query: str) -> Paper:
        """Parse bioRxiv/medRxiv paper data"""
        paper = Paper(
            id=item.get('doi', ''),
            title=item.get('title', ''),
            abstract=item.get('abstract', ''),
            authors=item.get('authors', '').split('; ') if item.get('authors') else [],
            date_published=datetime.strptime(item.get('date', ''), '%Y-%m-%d'),
            source=self.server,
            url=f"https://www.{self.server}.org/content/{item.get('doi')}",
            categories=[item.get('category', '')],
            doi=item.get('doi'),
            version=item.get('version', 1),
            pdf_url=f"https://www.{self.server}.org/content/{item.get('doi')}.full.pdf",
            metadata={
                'published': item.get('published', ''),
                'server': item.get('server', '')
            }
        )
        
        paper.relevance_score = self.calculate_relevance(paper, query)
        paper.quality_score = self.calculate_quality(paper)
        
        return paper
    
    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Get specific paper by DOI"""
        url = f"{self.BASE_URL}/details/{self.server}/{paper_id}"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                return None
                
            data = await response.json()
            
            if 'collection' in data and data['collection']:
                return self._parse_biorxiv_paper(data['collection'][0], "")
        
        return None


class ChemRxivAPI(PreprintAPI):
    """ChemRxiv API implementation"""
    
    BASE_URL = "https://chemrxiv.org/engage/chemrxiv/public-api/v1"
    
    @sleep_and_retry
    @limits(calls=10, period=1)  # ChemRxiv allows more requests
    async def search(self, query: str, max_results: int = 100) -> List[Paper]:
        """Search ChemRxiv using their public API"""
        papers = []
        skip = 0
        limit = min(50, max_results)  # API limit per request
        
        while len(papers) < max_results:
            url = f"{self.BASE_URL}/items"
            params = {
                'term': query,
                'skip': skip,
                'limit': limit,
                'sortBy': 'RELEVANCE'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    break
                    
                data = await response.json()
                
                if 'itemHits' not in data or not data['itemHits']:
                    break
                
                for item in data['itemHits']:
                    paper = self._parse_chemrxiv_paper(item, query)
                    papers.append(paper)
                    
                    if len(papers) >= max_results:
                        break
                
                skip += limit
                
                # Check if we've retrieved all available papers
                if skip >= data.get('totalCount', 0):
                    break
        
        return papers[:max_results]
    
    def _parse_chemrxiv_paper(self, item: dict, query: str) -> Paper:
        """Parse ChemRxiv paper data"""
        # Extract authors
        authors = []
        for author in item.get('authors', []):
            name = f"{author.get('firstName', '')} {author.get('lastName', '')}".strip()
            if name:
                authors.append(name)
        
        paper = Paper(
            id=item.get('id', ''),
            title=item.get('title', ''),
            abstract=item.get('abstract', ''),
            authors=authors,
            date_published=datetime.fromisoformat(
                item.get('publishedDate', '').replace('Z', '+00:00')
            ) if item.get('publishedDate') else datetime.now(),
            source='chemrxiv',
            url=f"https://chemrxiv.org/engage/chemrxiv/article-details/{item.get('id')}",
            categories=item.get('categories', []),
            doi=item.get('doi'),
            version=item.get('version', 1),
            pdf_url=item.get('pdfUrl'),
            metadata={
                'keywords': item.get('keywords', []),
                'license': item.get('license', '')
            }
        )
        
        paper.relevance_score = self.calculate_relevance(paper, query)
        paper.quality_score = self.calculate_quality(paper)
        
        return paper
    
    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Get specific paper by ID"""
        url = f"{self.BASE_URL}/items/{paper_id}"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                return None
                
            data = await response.json()
            return self._parse_chemrxiv_paper(data, "")


class SSRNApi(PreprintAPI):
    """SSRN API implementation (limited, mainly through web scraping)"""
    
    BASE_URL = "https://papers.ssrn.com/sol3/results.cfm"
    
    async def search(self, query: str, max_results: int = 100) -> List[Paper]:
        """
        Search SSRN
        Note: SSRN doesn't have a proper API, this uses their RSS feed
        """
        # Use their RSS feed for search
        rss_url = f"https://papers.ssrn.com/sol3/Jeljour_results.cfm?form_name=journalBrowse&journal_id=&Network=no&lim=false&npage=1&stype=desc&Query={quote(query)}&format=rss"
        
        papers = []
        
        async with self.session.get(rss_url) as response:
            if response.status != 200:
                return papers
                
            content = await response.text()
            feed = feedparser.parse(content)
            
            for entry in feed.entries[:max_results]:
                paper = self._parse_ssrn_entry(entry, query)
                papers.append(paper)
        
        return papers
    
    def _parse_ssrn_entry(self, entry: dict, query: str) -> Paper:
        """Parse SSRN RSS feed entry"""
        # Extract abstract ID from link
        abstract_id = ""
        if 'link' in entry:
            match = re.search(r'abstract=(\d+)', entry.link)
            if match:
                abstract_id = match.group(1)
        
        # Parse authors (usually in format "by Author1, Author2")
        authors = []
        if 'author' in entry:
            authors = [a.strip() for a in entry.author.replace('by ', '').split(',')]
        
        paper = Paper(
            id=abstract_id,
            title=entry.get('title', ''),
            abstract=entry.get('summary', ''),
            authors=authors,
            date_published=datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now(),
            source='ssrn',
            url=entry.get('link', ''),
            categories=entry.get('tags', [{'term': 'Social Science'}])[0]['term'].split(',') if entry.get('tags') else [],
            doi=None,  # SSRN uses abstract IDs instead
            pdf_url=f"https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID{abstract_id}_code.pdf?abstractid={abstract_id}" if abstract_id else None
        )
        
        paper.relevance_score = self.calculate_relevance(paper, query)
        paper.quality_score = self.calculate_quality(paper)
        
        return paper
    
    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        """SSRN doesn't provide a good API for individual papers"""
        # Would need to implement web scraping for full functionality
        return None


class ResearchSquareAPI(PreprintAPI):
    """Research Square API implementation"""
    
    BASE_URL = "https://www.researchsquare.com/api/manuscripts"
    
    @sleep_and_retry
    @limits(calls=5, period=1)
    async def search(self, query: str, max_results: int = 100) -> List[Paper]:
        """Search Research Square"""
        papers = []
        page = 1
        per_page = min(50, max_results)
        
        while len(papers) < max_results:
            params = {
                'query': query,
                'page': page,
                'per_page': per_page,
                'sort': 'relevance'
            }
            
            async with self.session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    break
                    
                data = await response.json()
                
                if 'data' not in data or not data['data']:
                    break
                
                for item in data['data']:
                    paper = self._parse_rs_paper(item, query)
                    papers.append(paper)
                    
                    if len(papers) >= max_results:
                        break
                
                page += 1
                
                # Check if we've retrieved all pages
                if page > data.get('meta', {}).get('last_page', 1):
                    break
        
        return papers[:max_results]
    
    def _parse_rs_paper(self, item: dict, query: str) -> Paper:
        """Parse Research Square paper data"""
        authors = [author.get('name', '') for author in item.get('authors', [])]
        
        paper = Paper(
            id=item.get('id', ''),
            title=item.get('title', ''),
            abstract=item.get('abstract', ''),
            authors=authors,
            date_published=datetime.fromisoformat(
                item.get('posted_date', '').replace('Z', '+00:00')
            ) if item.get('posted_date') else datetime.now(),
            source='researchsquare',
            url=f"https://www.researchsquare.com/article/{item.get('doi', '')}",
            categories=item.get('subject_areas', []),
            doi=item.get('doi'),
            version=item.get('version', 1),
            pdf_url=item.get('pdf_url'),
            metadata={
                'status': item.get('status', ''),
                'license': item.get('license', '')
            }
        )
        
        paper.relevance_score = self.calculate_relevance(paper, query)
        paper.quality_score = self.calculate_quality(paper)
        
        return paper
    
    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Get specific paper by ID"""
        url = f"{self.BASE_URL}/{paper_id}"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                return None
                
            data = await response.json()
            return self._parse_rs_paper(data, "")


class PreprintAggregator:
    """
    Main aggregator class that searches across all preprint servers
    and implements intelligent ranking strategies
    """
    
    def __init__(self):
        self.apis = {
            'arxiv': ArxivAPI(),
            'biorxiv': BioRxivAPI(server='biorxiv'),
            'medrxiv': BioRxivAPI(server='medrxiv'),
            'chemrxiv': ChemRxivAPI(),
            'ssrn': SSRNApi(),
            'researchsquare': ResearchSquareAPI()
        }
        
        # Field-specific server preferences
        self.field_preferences = {
            'physics': ['arxiv'],
            'computer science': ['arxiv'],
            'mathematics': ['arxiv'],
            'biology': ['biorxiv', 'arxiv'],
            'medicine': ['medrxiv', 'biorxiv'],
            'chemistry': ['chemrxiv', 'arxiv'],
            'economics': ['ssrn', 'arxiv'],
            'social sciences': ['ssrn', 'researchsquare'],
            'general': ['arxiv', 'biorxiv', 'medrxiv', 'researchsquare']
        }
    
    def detect_field(self, query: str) -> str:
        """Detect the research field from the query"""
        query_lower = query.lower()
        
        field_keywords = {
            'physics': ['quantum', 'particle', 'relativity', 'cosmology', 'physics'],
            'computer science': ['algorithm', 'machine learning', 'neural network', 'software', 'computation'],
            'mathematics': ['theorem', 'proof', 'algebra', 'topology', 'calculus'],
            'biology': ['cell', 'protein', 'gene', 'dna', 'evolution', 'organism'],
            'medicine': ['treatment', 'disease', 'clinical', 'patient', 'therapy', 'drug'],
            'chemistry': ['molecule', 'reaction', 'compound', 'synthesis', 'catalyst'],
            'economics': ['market', 'economy', 'finance', 'trade', 'monetary'],
            'social sciences': ['society', 'psychology', 'behavior', 'culture', 'social']
        }
        
        field_scores = {}
        for field, keywords in field_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                field_scores[field] = score
        
        if field_scores:
            return max(field_scores, key=field_scores.get)
        return 'general'
    
    async def search_all(
        self, 
        query: str, 
        max_results_per_server: int = 50,
        servers: Optional[List[str]] = None
    ) -> List[Paper]:
        """
        Search across multiple preprint servers in parallel
        
        Args:
            query: Search query
            max_results_per_server: Maximum results from each server
            servers: List of servers to search (None = auto-detect)
        
        Returns:
            Combined and ranked list of papers
        """
        # Auto-detect field and select appropriate servers
        if servers is None:
            field = self.detect_field(query)
            servers = self.field_preferences.get(field, self.field_preferences['general'])
        
        # Search all servers in parallel
        all_papers = []
        
        async def search_server(server_name: str):
            if server_name not in self.apis:
                return []
            
            api = self.apis[server_name]
            try:
                async with api:
                    papers = await api.search(query, max_results_per_server)
                    return papers
            except Exception as e:
                print(f"Error searching {server_name}: {e}")
                return []
        
        # Parallel search
        results = await asyncio.gather(*[
            search_server(server) for server in servers
        ])
        
        # Combine results
        for papers in results:
            all_papers.extend(papers)
        
        # Remove duplicates and rank
        unique_papers = self._deduplicate(all_papers)
        ranked_papers = self._rank_papers(unique_papers, query)
        
        return ranked_papers
    
    def _deduplicate(self, papers: List[Paper]) -> List[Paper]:
        """Remove duplicate papers based on title similarity"""
        unique_papers = []
        seen_titles = set()
        
        for paper in papers:
            # Normalize title for comparison
            normalized_title = re.sub(r'[^a-z0-9]+', '', paper.title.lower())
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_papers.append(paper)
            else:
                # If duplicate, keep the one with higher quality score
                for i, existing in enumerate(unique_papers):
                    existing_normalized = re.sub(r'[^a-z0-9]+', '', existing.title.lower())
                    if existing_normalized == normalized_title:
                        if paper.quality_score > existing.quality_score:
                            unique_papers[i] = paper
                        break
        
        return unique_papers
    
    def _rank_papers(self, papers: List[Paper], query: str) -> List[Paper]:
        """
        Rank papers using a multi-factor scoring system
        
        Factors:
        - Relevance score (40%)
        - Quality score (30%)
        - Recency (20%)
        - Source reputation (10%)
        """
        source_weights = {
            'arxiv': 1.0,
            'biorxiv': 0.95,
            'medrxiv': 0.95,
            'chemrxiv': 0.9,
            'researchsquare': 0.85,
            'ssrn': 0.85
        }
        
        for paper in papers:
            # Calculate recency score
            days_old = (datetime.now() - paper.date_published).days
            recency_score = max(0, 1 - (days_old / 365))  # Linear decay over 1 year
            
            # Get source weight
            source_score = source_weights.get(paper.source, 0.8)
            
            # Calculate final score
            paper.metadata['ranking_score'] = (
                paper.relevance_score * 0.4 +
                paper.quality_score * 0.3 +
                recency_score * 0.2 +
                source_score * 0.1
            )
        
        # Sort by ranking score
        papers.sort(key=lambda p: p.metadata['ranking_score'], reverse=True)
        
        return papers


# Example usage
async def main():
    """Example of using the preprint aggregator"""
    aggregator = PreprintAggregator()
    
    # Example queries
    queries = [
        "quantum computing applications in drug discovery",
        "CRISPR gene editing therapeutic applications",
        "machine learning climate change prediction",
        "behavioral economics decision making"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Searching for: {query}")
        print(f"{'='*60}")
        
        papers = await aggregator.search_all(
            query=query,
            max_results_per_server=20
        )
        
        print(f"\nFound {len(papers)} unique papers")
        
        # Display top 5 results
        for i, paper in enumerate(papers[:5], 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors[:3])}")
            print(f"   Source: {paper.source} | Date: {paper.date_published.strftime('%Y-%m-%d')}")
            print(f"   Relevance: {paper.relevance_score:.2f} | Quality: {paper.quality_score:.2f}")
            print(f"   Overall Rank: {paper.metadata.get('ranking_score', 0):.2f}")
            print(f"   URL: {paper.url}")


if __name__ == "__main__":
    asyncio.run(main())