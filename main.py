import os
from article_scraper import scrape_articles
from summarizer import summarize_articles
from sms_sender import send_sms_via_email
from sms_sender_telegram import send_telegram_message
from sms_sender_slack import send_slack_message
from email_processor import get_article_links
from email_processor import search_for_unread_emails
from email_processor import connect_to_email_server
from user_preferences import preferences
from process_Newsletter import fetch_email_body

channel = "#fintech-general-body-slack"
#channel = "#test-bot"

# Access sensitive data from environment variables
USER_PHONE_NUMBER = os.getenv('USER_PHONE_NUMBER')
TELEGRAM_CHATID = os.getenv('TELEGRAM_CHATID')
TELEGRAM_BOT_API = os.getenv('TELEGRAM_BOT_API')
SLACK_BOT_OAUTH = os.getenv('SLACK_BOT_OAUTH')

def estimate_tokens(text):
    """Estimates the number of tokens in a text."""
    AVG_CHARS_PER_TOKEN = 4  # Rough approximation for GPT-like models
    return len(text) / AVG_CHARS_PER_TOKEN

def trim_articles_to_token_limit(articles, token_limit=16385):
    """Trims a list of articles to stay under a specified token limit."""
    total_tokens = sum(estimate_tokens(article) for article in articles)
    
    print(f"Initial Total Tokens: {total_tokens}")

    # Remove articles until the total token count is under the limit
    for article in articles:
        article_tokens = estimate_tokens(article)
        print(f"Article Tokens: {article_tokens}")
        
        if total_tokens > token_limit:
            removed_article = articles.pop()
            total_tokens -= estimate_tokens(removed_article)
            print(f"Removed article. New Total Tokens: {total_tokens}")
        else:
            break

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

    print(f"Article Links: {article_links}")

    articles_content = scrape_articles(article_links)

    moneystuff_mail = connect_to_email_server()
    moneystuff_email_id = search_for_unread_emails(moneystuff_mail, "noreply@news.bloomberg.com")

    if moneystuff_email_id:
        email_id = moneystuff_email_id[0]
        email_body = fetch_email_body(moneystuff_mail, email_id)
        
        if email_body:
            print("Successfully fetched the email body.")
            articles_content.append(email_body)
        else:
            print("Failed to fetch the email body.")
    else:
        print("No unread emails found from Money Stuff today.")

    print(f"Articles Content: {articles_content}")

    #trimmed_articles = trim_articles_to_token_limit(articles_content, 16385)

    #print(f"Trimmed Articles: {trimmed_articles}")

    summaries = summarize_articles(articles_content)

    print("TEST SUMMARIES LENGTH:" + str(len(articles_content)))

    if len(summaries) > 0:
        send_slack_message("Hey! It's T.I.D.A.L giving you your daily updates! (Loading Content...)" , SLACK_BOT_OAUTH, channel)
        send_slack_message("*** From Head of Tech: This chatbot is not perfect and like any LLM, can make mistakes***", SLACK_BOT_OAUTH, channel)
    else:
        send_slack_message("I've got nothing for you today. Either today is a weekend, I was unable to scrape any content, or this was a hiccup!", SLACK_BOT_OAUTH, channel)

    for summary in summaries:
        send_slack_message(summary, SLACK_BOT_OAUTH, channel)

if __name__ == "__main__":
    summarize_and_notify()
