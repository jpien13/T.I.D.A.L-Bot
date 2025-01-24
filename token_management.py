def estimate_tokens(text):
    """Estimates the number of tokens in a text."""
    AVG_CHARS_PER_TOKEN = 4  # Rough approximation for GPT-like models
    return len(text) / AVG_CHARS_PER_TOKEN

def balance_articles_tokens(articles, total_token_limit=32000, num_articles=3):
    """
    Balances tokens across articles to ensure each gets approximately equal tokens
    and the total stays under the specified limit.
    
    Args:
        articles: List of article texts
        total_token_limit: Maximum total tokens allowed (default 32K)
        num_articles: Desired number of articles to process (default 3)
        
    Returns:
        List of processed articles with balanced token counts
    """
    # If we have fewer articles than requested, return them all
    if len(articles) <= num_articles:
        return articles
        
    # Calculate tokens per article
    tokens_per_article = total_token_limit // num_articles
    
    # Process each article to fit within its token allocation
    balanced_articles = []
    for i, article in enumerate(articles[:num_articles]):  # Only process the first num_articles
        article_tokens = estimate_tokens(article)
        
        if article_tokens > tokens_per_article:
            # If article is too long, trim it proportionally
            # We use characters as a proxy since we're working with text
            chars_to_keep = int((tokens_per_article / article_tokens) * len(article))
            # Try to break at a sentence boundary by finding the last period
            last_period = article[:chars_to_keep].rfind('.')
            if last_period != -1:
                balanced_articles.append(article[:last_period + 1])
            else:
                # If no period found, break at the last space
                last_space = article[:chars_to_keep].rfind(' ')
                if last_space != -1:
                    balanced_articles.append(article[:last_space])
                else:
                    balanced_articles.append(article[:chars_to_keep])
        else:
            balanced_articles.append(article)
            
    return balanced_articles

def verify_token_limits(articles):
    """
    Verifies that the articles meet token limits and prints diagnostic information.
    
    Args:
        articles: List of processed articles
        
    Returns:
        Boolean indicating whether articles meet token limits
    """
    total_tokens = 0
    for i, article in enumerate(articles, 1):
        tokens = estimate_tokens(article)
        total_tokens += tokens
        print(f"Article {i}: {tokens:.0f} tokens")
    
    print(f"Total tokens: {total_tokens:.0f}")
    return total_tokens <= 32000