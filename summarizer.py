from openai import OpenAI
import os
from user_preferences import preferences
from article_scraper import scrape_articles

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def estimate_tokens(text):
    """Estimates the number of tokens in a text."""
    AVG_CHARS_PER_TOKEN = 4  # Rough approximation for GPT-like models
    return len(text) / AVG_CHARS_PER_TOKEN

def summarize_articles(articles_content):
    """
    Summarize a list of articles using OpenAI's API
    """
    summaries = []
    for article in articles_content:
        # Estimate the number of tokens in the article
        article_tokens = estimate_tokens(article)

        # Set a safe minimum for available tokens
        available_tokens_for_completion = max(0, 8192 - article_tokens)

        # Ensure we calculate `completion_tokens` correctly
        completion_tokens = min(preferences['summary_length'] * 5, available_tokens_for_completion)

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a precise and concise article summarizer."},
                    {"role": "user", "content": f"Your audience is students in a college fintech club. Summarize this event in {preferences['summary_length']} words, emphasizing key points:\n\n{article}"}
                ],
                temperature=0.5,
                max_tokens=int(completion_tokens),  # Ensure this is an integer
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            summaries.append(response.choices[0].message.content.strip())
            print(f"✓ Successfully summarized article ({len(article)} chars -> {len(summaries[-1])} chars)")
            
        except Exception as e:
            error_message = f"Error summarizing article: {str(e)}"
            print(f"✗ {error_message}")
            summaries.append(error_message)

    return summaries

if __name__ == "__main__":
    urls = [
        "https://www.theverge.com/2024/3/28/24112507/sam-bankman-fried-sentence-ftx-alameda",
        "https://arstechnica.com/gadgets/2024/03/netflix-ad-spend-led-to-facebook-dm-access-end-of-facebook-streaming-biz-lawsuit/"
    ]
    
    print("Scraping articles...")
    articles_content = scrape_articles(urls)
    
    print("\nGenerating summaries...")
    summaries = summarize_articles(articles_content)
    
    print("\nSummaries:")
    print("="*50)
    for i, summary in enumerate(summaries, 1):
        print(f"\nSummary {i}:")
        print(summary)
        print("-"*50)