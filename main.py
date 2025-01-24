import os
from article_scraper import scrape_articles
from summarizer import summarize_articles
from sms_sender import send_sms_via_email
from sms_sender_telegram import send_telegram_message
from sms_sender_slack import send_slack_message
from email_processor import get_article_links
from user_preferences import preferences
from token_management import balance_articles_tokens, verify_token_limits

# Access sensitive data from environment variables
USER_PHONE_NUMBER = os.getenv('USER_PHONE_NUMBER')
TELEGRAM_CHATID = os.getenv('TELEGRAM_CHATID')
TELEGRAM_BOT_API = os.getenv('TELEGRAM_BOT_API')
SLACK_BOT_OAUTH = os.getenv('SLACK_BOT_OAUTH')

def summarize_and_notify():
    """
    Main function to process articles and send notifications.
    Now includes token balancing across articles.
    """
    # Fetch article links
    article_links = get_article_links('jason_pien@brown.edu')
    print(f"Article Links: {article_links}")
    
    # Scrape articles
    articles_content = scrape_articles(article_links)
    print(f"Number of articles scraped: {len(articles_content)}")
    
    # Balance tokens across articles
    balanced_articles = balance_articles_tokens(
        articles_content,
        total_token_limit=32000,
        num_articles=preferences['num_articles']
    )
    
    # Verify token limits are met
    if verify_token_limits(balanced_articles):
        print("Token limits verified successfully")
    else:
        print("Warning: Token limits exceeded")
    
    # Generate summaries
    summaries = summarize_articles(balanced_articles)
    print(f"Number of summaries generated: {len(summaries)}")
    
    # Send notifications
    if len(summaries) > 0:
        send_slack_message(
            "Hey! It's T.I.D.A.L giving you your daily updates! (Loading Content...)",
            SLACK_BOT_OAUTH,
            "#test"
        )
    else:
        send_slack_message(
            "Whoops! I've got nothing for you right now. Either I was unable to extract any content today or this was a hiccup! Sorry ",
            SLACK_BOT_OAUTH,
            "#test"
        )

    for summary in summaries:
        send_slack_message(summary, SLACK_BOT_OAUTH, "#test")

if __name__ == "__main__":
    summarize_and_notify()