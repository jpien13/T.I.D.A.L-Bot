import os
from article_scraper import scrape_articles
from summarizer import summarize_articles
from sms_sender import send_sms_via_email
from sms_sender_telegram import send_telegram_message
from sms_sender_slack import send_slack_message
from email_processor import get_article_links
from user_preferences import preferences

# Access sensitive data from environment variables
USER_PHONE_NUMBER = os.getenv('USER_PHONE_NUMBER')
TELEGRAM_CHATID = os.getenv('TELEGRAM_CHATID')
TELEGRAM_BOT_API = os.getenv('TELEGRAM_BOT_API')
SLACK_BOT_OAUTH = os.getenv('SLACK_BOT_OAUTH')

def estimate_tokens(text):
    """Estimates the number of tokens in a text."""
    AVG_CHARS_PER_TOKEN = 4  # Rough approximation for GPT-like models
    return len(text) / AVG_CHARS_PER_TOKEN

def trim_articles_to_token_limit(articles, token_limit=4097):
    """Trims a list of articles to stay under a specified token limit."""
    total_tokens = sum(estimate_tokens(article) for article in articles)
    
    # Remove articles from the list until the total token count is under the limit
    while total_tokens > token_limit and articles:
        removed_article = articles.pop()  # Remove the last article
        total_tokens -= estimate_tokens(removed_article)  # Update total token count
    
    return articles

def summarize_and_notify():
    """
    Step 1: Fetch new article links from emails
    Step 2: Scrape articles from the fetched links
    Step 3: May have to truncate the number of articles based on token limits
    Step 4: Summarize the scraped articles
    Step 5: Send summarized articles via Slack
    """
    article_links = get_article_links('dan@tldrnewsletter.com')
    # Alternatively use another email, as needed
    # article_links = get_article_links('pien.jason@gmail.com')

    articles_content = scrape_articles(article_links)
    for article in articles_content:
       print(article)
       print("#############################")

    trimmed_articles = trim_articles_to_token_limit(articles_content, 4097)
    summaries = summarize_articles(trimmed_articles)

    if len(summaries) > 0:
        send_slack_message("Hey! It's T.I.D.A.L giving you your daily updates in tech! (Loading Content...)", SLACK_BOT_OAUTH, "#test")
    else:
        send_slack_message("Whoops! I've got nothing for you right now. Either I was unable to extract any content today or this was a hiccup! Sorry ", SLACK_BOT_OAUTH, "#test")

    for summary in summaries:
        send_slack_message(summary, SLACK_BOT_OAUTH, "#test")

if __name__ == "__main__":
    summarize_and_notify()
