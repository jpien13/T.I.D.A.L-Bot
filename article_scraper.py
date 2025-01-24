import requests
from bs4 import BeautifulSoup
import time
from typing import List, Union, Dict
from urllib.parse import urlparse
import re
import random
from user_preferences import preferences

class ArticleScraper:
    def __init__(self, urls: List[str]):
        """
        Initializes an instance of the ArticleScraper class with improved headers
        and rotation capabilities.
        """
        self.urls = urls
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        ]
        self.session = requests.Session()
        self.max_retries = 3
        self.retry_delay = 2

    def _get_random_headers(self) -> Dict[str, str]:
        """
        Generate random headers to make requests look more like real browser traffic.
        """
        user_agent = random.choice(self.user_agents)
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        return headers

    def _add_referrer(self, url: str) -> Dict[str, str]:
        """
        Add a plausible referrer to the headers based on the URL being accessed.
        """
        headers = self._get_random_headers()
        parsed_url = urlparse(url)
        
        common_referrers = {
            'google.com': 'https://www.google.com/',
            'bing.com': 'https://www.bing.com/',
            'twitter.com': 'https://twitter.com/',
            'linkedin.com': 'https://www.linkedin.com/',
        }
        
        headers['Referer'] = random.choice(list(common_referrers.values()))
        return headers

    def fetch_article(self, url: str) -> Union[str, None]:
        """
        Fetches an article with improved error handling and retry logic.
        """
        attempts = 0
        while attempts < self.max_retries:
            try:
                headers = self._add_referrer(url)
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=10,
                    allow_redirects=True
                )
                
                if response.status_code == 403:
                    print(f"Access forbidden for {url}. Trying with different headers...")
                    time.sleep(self.retry_delay * (attempts + 1))
                    attempts += 1
                    continue
                
                response.raise_for_status()
                return response.text
                
            except requests.RequestException as e:
                print(f"Attempt {attempts + 1} failed for {url}: {e}")
                if attempts < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempts + 1)
                    print(f"Waiting {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                attempts += 1
        
        print(f"Failed to fetch {url} after {self.max_retries} attempts")
        return None

    def parse_content(self, html: str) -> str:
        """
        Enhanced parsing with better content detection and cleaning.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Remove social media widgets and ads
        for element in soup.find_all(class_=re.compile(r'(social|share|ad|cookie|popup|banner)', re.I)):
            element.decompose()
        
        # Enhanced content detection
        content_tags = ['article', 'main', 'div', 'section']
        likely_classes_patterns = [
            'content', 'post', 'text', 'article', 'body', 'story', 'entry',
            'main-content', 'article-content', 'post-content'
        ]
        
        content = ""
        max_content_score = 0
        
        for tag in content_tags:
            for element in soup.find_all(tag):
                current_content = ""
                score = 0
                
                # Check class and id attributes
                attrs_text = " ".join([
                    " ".join(element.get("class", [])),
                    element.get("id", ""),
                    element.get("role", "")
                ]).lower()
                
                if any(re.search(pattern, attrs_text, re.IGNORECASE) for pattern in likely_classes_patterns):
                    score += 5
                
                paragraphs = element.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text:
                        # Score based on text length and quality
                        words = len(text.split())
                        if words > 10:  # Likely a content paragraph
                            score += 2
                            current_content += text + '\n'
                
                if score > max_content_score:
                    max_content_score = score
                    content = current_content
        
        # Fallback to simpler method if no content found
        if not content:
            paragraphs = soup.find_all('p')
            content = '\n'.join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True).split()) > 10)
        
        # Clean up the content
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Remove excessive newlines
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        
        return content.strip()

    def scrape(self) -> List[str]:
        """
        Main scraping method with improved rate limiting and status reporting.
        """
        articles_content = []
        successful_urls = []
        failed_urls = []
        
        for url in self.urls:
            print(f"\nProcessing {url}")
            
            # Add jitter to delay to appear more human-like
            delay = 1 + random.uniform(0.5, 2.0)
            time.sleep(delay)
            
            html = self.fetch_article(url)
            if html:
                article_text = self.parse_content(html)
                if article_text:
                    articles_content.append(article_text)
                    successful_urls.append(url)
                    print(f"✓ Successfully scraped article ({len(article_text)} characters)")
                else:
                    failed_urls.append(url)
                    print("✗ Failed to extract content from page")
            else:
                failed_urls.append(url)
                print("✗ Failed to fetch page")
        
        # Print summary
        print("\n" + "="*50)
        print(f"Scraping Summary:")
        print(f"Total URLs attempted: {len(self.urls)}")
        print(f"Successfully scraped: {len(successful_urls)}")
        print(f"Failed to scrape: {len(failed_urls)}")
        if failed_urls:
            print("\nFailed URLs:")
            for url in failed_urls:
                print(f"- {url}")
        print("="*50 + "\n")
        
        return articles_content

def scrape_articles(urls):
    """
    Will return only num_articles of all the articles processed
    """
    scraper = ArticleScraper(urls)
    res = scraper.scrape()
    return res[:preferences["num_articles"]]

# Example usage
if __name__ == "__main__":
    urls = [
        "https://www.cnbc.com/2024/03/25/elon-musk-requires-fsd-demo-for-every-prospective-tesla-buyer-in-north-america.html",
        "https://www.cnbc.com/2024/03/25/adam-neumann-submits-bid-of-more-than-500-million-to-buy-wework.html",
        "https://www.theregister.com/2024/03/25/ai_boom_nuclear/"
    ]
    articles = scrape_articles(urls)
    print(f"Successfully scraped {len(articles)} articles")
    for i, article in enumerate(articles, 1):
        print(f"\nArticle {i} preview:")
        print(article[:500])
        print("-------------------------------------------")