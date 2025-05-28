import asyncio
from twikit import Client
import datetime

# --- Configuration ---
USERNAME = 'rogermas05'  # Replace with your Twitter username
EMAIL = 'rogermas14@gmail.com'        # Replace with your Twitter email
PASSWORD = 'x'  # Replace with your Twitter password'
NFT_MENTION = 'beratoners'  # Replace with the NFT project name or relevant keyword
# Define the time range for the search
# Timestamps should be in UTC
# Example: Search from January 1, 2023, 00:00:00 UTC to January 31, 2023, 23:59:59 UTC
SINCE_TIMESTAMP = datetime.datetime(2025, 5, 28, 0, 0, 0, tzinfo=datetime.timezone.utc)
UNTIL_TIMESTAMP = datetime.datetime(2025, 5, 28, 23, 59, 59, tzinfo=datetime.timezone.utc)
# --- End Configuration ---

async def main():
    """
    Logs into Twitter, searches for tweets mentioning a specific NFT within a given time range,
    and prints the found tweets.
    """
    client = Client(language='en-US')
    try:
        await client.login(
            auth_info_1=USERNAME,
            auth_info_2=EMAIL,
            password=PASSWORD
        )
        print("Successfully logged in to Twitter.")
    except Exception as e:
        print(f"Error during login: {e}")
        return

    search_query = f"{NFT_MENTION} since:{SINCE_TIMESTAMP.strftime('%Y-%m-%d_%H:%M:%S_UTC')} until:{UNTIL_TIMESTAMP.strftime('%Y-%m-%d_%H:%M:%S_UTC')}"
    print(f"Searching for tweets with query: {search_query}")

    try:
        tweets_result = await client.search_tweet(search_query, 'Latest', count=100)

        tweets = list(tweets_result)

        if tweets:
            print(f"\nFound {len(tweets)} tweets:")
            for tweet in tweets:
                user_screen_name = tweet.user.screen_name if tweet.user else 'UnknownUser'
                tweet_text = tweet.text if hasattr(tweet, 'text') else 'No Text'
                created_at = tweet.created_at if hasattr(tweet, 'created_at') else 'No Date'
                tweet_id = tweet.id if hasattr(tweet, 'id') else 'NoID'

                print(f"\nUser: @{user_screen_name}")
                print(f"Text: {tweet_text}")
                print(f"Created at: {created_at}")
                print(f"Link: https://twitter.com/{user_screen_name}/status/{tweet_id}")
                print("-" * 20)
        else:
            print("No tweets found matching your criteria.")

    except Exception as e:
        print(f"Error searching tweets: {e}")

if __name__ == '__main__':
    asyncio.run(main())
