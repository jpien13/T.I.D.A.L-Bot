import requests
from bs4 import BeautifulSoup
import time
from typing import List, Union
from urllib.parse import urlparse
import re
from user_preferences import preferences

class ArticleScraper:
    def __init__(self, urls: List[str]):
        """
        Initializes an instance of the ArticleScraper class.
        Accepts a list of URLs (urls) to scrape.
        Sets a User-Agent in the headers to mimic a real web browser, which helps avoid being blocked by websites.
        """

        self.urls = urls
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    def fetch_article(self, url: str) -> Union[str, None]:
        """
        Fetches an article and extracts content.
        
        Tries to fetch the HTML content of an article by making a GET request to the given URL.
        Uses the User-Agent header set in the __init__ method. If the request is successful, 
        it returns the HTML content as a string; otherwise, it returns None and prints an error message.
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raises HTTPError for bad responses
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_content(self, html: str) -> str:
        """
        Parses HTML content to extract relevant article text using heuristics
        for identifying content-rich sections of a webpage.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        
        # Heuristic: Look for blocks of text within certain tags, giving priority to more common content tags
        content_tags = ['article', 'main', 'div', 'section']
        likely_classes_patterns = ['content', 'post', 'text', 'article', 'body']
        content = ""

        for tag in content_tags:
            for element in soup.find_all(tag):
                # Check if class attribute of the tag hints at containing main content
                class_text = " ".join(element.get("class", []))
                if any(re.search(pattern, class_text, re.IGNORECASE) for pattern in likely_classes_patterns):
                    paragraphs = element.find_all('p')
                    current_content = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                    # Heuristic: Prefer the block with the most paragraphs
                    if current_content.count('\n') > content.count('\n'):
                        content = current_content

        # If no content found with class hints, fall back to a simpler method
        if not content:
            paragraphs = soup.find_all('p')
            content = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        return content

    def scrape(self) -> List[str]:
        """
        Main method to scrape articles.
        
        The main method that orchestrates the scraping process.
        Iterates through each URL in the list, fetches the HTML content, 
        and then parses it to extract the article's text.
        Includes a time.sleep(1) call between requests to be respectful to the 
        server's resources. Returns a list containing the text of each article. 
        """
        articles_content = []
        for url in self.urls:
            print(f"Processing {url}")
            html = self.fetch_article(url)
            if html:
                article_text = self.parse_content(html)
                if article_text != "":
                    articles_content.append(article_text)
                time.sleep(1)  # Sleep to be polite to the server
        
        return articles_content

def scrape_articles(urls):
    """
    Will return only num_articles of all the articles processed
    """
    scraper = ArticleScraper(urls)
    res = scraper.scrape()
    return res[:preferences["num_articles"]]

# Example usage for testing
if __name__ == "__main__":
    """ RETURNS A LIST WHERE EACH ELEMENT IS A LONG STRING FOR EACH ARTICLE IN THE ARTICLES LIST"""
    urls = ["https://www.cnbc.com/2024/03/25/elon-musk-requires-fsd-demo-for-every-prospective-tesla-buyer-in-north-america.html?utm_source=tldrnewsletter", "https://www.cnbc.com/2024/03/25/adam-neumann-submits-bid-of-more-than-500-million-to-buy-wework.html?utm_source=tldrnewsletter", "https://www.theregister.com/2024/03/25/ai_boom_nuclear/?utm_source=tldrnewsletter"]
    articles = scrape_articles(urls)
    print(len(articles))
    for article in articles:
        print(article[:20000])  # Print first 20,000 characters of each article for preview
        print("-------------------------------------------")