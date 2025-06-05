import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from textblob import TextBlob
import time

class NFTTwitterScraper:
    def __init__(self, apify_token):
        self.apify_token = apify_token
        self.base_url = "https://api.apify.com/v2"
        
    def create_search_queries(self, nft_name, collection_name):
        """Create comprehensive search queries for the NFT"""
        base_queries = [
            nft_name,
            collection_name,
            f'"{collection_name}"',
            f"{collection_name} NFT",
            f"{collection_name} mint",
            f"{collection_name} floor",
            f"{collection_name} drop",
            f"#{collection_name.replace(' ', '')}",  # hashtag version
        ]
        
        # Remove duplicates and empty strings
        return list(set([q for q in base_queries if q.strip()]))
    
    def run_twitter_scraper_sync(self, search_query, start_date, end_date, max_tweets=1000):
        """Run Apify Twitter scraper synchronously and get results directly"""
        
        # Configure the scraper input - using correct field names from API spec
        scraper_input = {
            "searchTerms": [search_query],
            "maxItems": max_tweets,  # Changed from maxTweets
            "start": start_date.strftime("%Y-%m-%d"),  # Changed from startDate
            "end": end_date.strftime("%Y-%m-%d"),  # Changed from endDate
            "includeSearchTerms": True,
            "tweetLanguage": "en",
            "onlyVerifiedUsers": False,  # Changed from onlyVerified
            "onlyTwitterBlue": False,
            "sort": "Latest",  # "Latest" or "Top"
        }
        
        # Use the synchronous endpoint from the OpenAPI spec
        url = f"{self.base_url}/acts/apidojo~tweet-scraper/run-sync-get-dataset-items"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add token as query parameter as specified in the API
        params = {"token": self.apify_token}
        
        print(f"Running synchronous scraper for query: '{search_query}'")
        response = requests.post(url, json=scraper_input, headers=headers, params=params)
        
        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} tweets")
            return results
        else:
            print(f"Error running synchronous scraper: {response.text}")
            return None
    def run_twitter_scraper(self, search_query, start_date, end_date, max_tweets=1000):
        """Run Apify Twitter scraper asynchronously for a specific query and date range"""
        
        # Configure the scraper input - using correct field names from API spec
        scraper_input = {
            "searchTerms": [search_query],
            "maxItems": max_tweets,  # Changed from maxTweets
            "start": start_date.strftime("%Y-%m-%d"),  # Changed from startDate
            "end": end_date.strftime("%Y-%m-%d"),  # Changed from endDate
            "includeSearchTerms": True,
            "tweetLanguage": "en",
            "onlyVerifiedUsers": False,  # Changed from onlyVerified
            "onlyTwitterBlue": False,
            "sort": "Latest",  # "Latest" or "Top"
        }
        
        # Start the scraper - Using the correct actor name
        url = f"{self.base_url}/acts/apidojo~tweet-scraper/runs"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add token as query parameter as specified in the API
        params = {"token": self.apify_token}
        
        response = requests.post(url, json=scraper_input, headers=headers, params=params)
        
        if response.status_code == 201:
            run_data = response.json()["data"]
            run_id = run_data["id"]
            default_dataset_id = run_data["defaultDatasetId"]  # Get the dataset ID
            print(f"Started scraper run: {run_id}")
            print(f"Dataset ID: {default_dataset_id}")
            return self.wait_for_completion(run_id, default_dataset_id)
        else:
            print(f"Error starting scraper: {response.text}")
            return None
    
    def wait_for_completion(self, run_id, default_dataset_id, max_wait_minutes=10):
        """Wait for the scraper to complete and return results"""
        url = f"{self.base_url}/acts/apidojo~tweet-scraper/runs/{run_id}"
        params = {"token": self.apify_token}  # Use query params instead of headers
        
        for _ in range(max_wait_minutes * 6):  # Check every 10 seconds
            response = requests.get(url, params=params)
            if response.status_code == 200:
                status = response.json()["data"]["status"]
                print(f"Scraper status: {status}")
                
                if status == "SUCCEEDED":
                    return self.get_results(default_dataset_id)  # Pass dataset ID
                elif status == "FAILED":
                    print("Scraper failed!")
                    return None
                    
            time.sleep(10)
        
        print("Scraper timed out")
        return None
    
    def get_results(self, run_id):
        """Get the results from a completed scraper run"""
        url = f"{self.base_url}/acts/apify~twitter-scraper/runs/{run_id}/dataset/items"
        headers = {"Authorization": f"Bearer {self.apify_token}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting results: {response.text}")
            return None
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of tweet text"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                return "positive"
            elif polarity < -0.1:
                return "negative"
            else:
                return "neutral"
        except:
            return "neutral"
    
    def calculate_hype_score(self, tweet_data):
        """Calculate a hype score based on engagement metrics"""
        retweets = tweet_data.get('retweetCount', 0)
        likes = tweet_data.get('likeCount', 0)
        replies = tweet_data.get('replyCount', 0)
        
        # Weighted hype score (you can adjust these weights)
        hype_score = (retweets * 3) + (likes * 1) + (replies * 2)
        return hype_score
    
    def process_nft_data(self, nft_name, collection_name, sale_date, apify_token):
        """Main function to scrape and analyze NFT Twitter data"""
        
        # Calculate date range (1 week before sale date)
        end_date = datetime.strptime(sale_date, "%Y-%m-%d")
        start_date = end_date - timedelta(days=7)
        
        print(f"Analyzing tweets from {start_date.date()} to {end_date.date()}")
        
        # Create search queries
        search_queries = self.create_search_queries(nft_name, collection_name)
        
        all_tweets = []
        
        # Run scraper for each query - try sync first, fallback to async
        for query in search_queries:
            print(f"Scraping for query: '{query}'")
            
            # Try synchronous method first (faster and simpler)
            tweets = self.run_twitter_scraper_sync(query, start_date, end_date, max_tweets=500)
            
            # If sync fails, fallback to async method
            if not tweets:
                print("Sync method failed, trying async method...")
                tweets = self.run_twitter_scraper(query, start_date, end_date, max_tweets=500)
            
            if tweets:
                all_tweets.extend(tweets)
                print(f"Found {len(tweets)} tweets for query: {query}")
            
            # Add delay between queries to avoid rate limits
            time.sleep(5)
        
        # Remove duplicates based on tweet ID
        unique_tweets = {}
        for tweet in all_tweets:
            tweet_id = tweet.get('id')
            if tweet_id and tweet_id not in unique_tweets:
                unique_tweets[tweet_id] = tweet
        
        tweets_list = list(unique_tweets.values())
        print(f"Total unique tweets found: {len(tweets_list)}")
        
        # Analyze the tweets
        results = self.analyze_tweets(tweets_list)
        
        return results
    
    def analyze_tweets(self, tweets):
        """Analyze collected tweets and generate metrics"""
        
        metrics = {
            'total_tweets': len(tweets),
            'total_retweets': 0,
            'total_replies': 0,
            'total_likes': 0,
            'positive_tweets': 0,
            'negative_tweets': 0,
            'neutral_tweets': 0,
            'total_hype_score': 0,
            'daily_breakdown': {},
            'top_tweets': []
        }
        
        for tweet in tweets:
            # Count engagement metrics
            metrics['total_retweets'] += tweet.get('retweetCount', 0)
            metrics['total_replies'] += tweet.get('replyCount', 0)
            metrics['total_likes'] += tweet.get('likeCount', 0)
            
            # Analyze sentiment
            sentiment = self.analyze_sentiment(tweet.get('text', ''))
            metrics[f'{sentiment}_tweets'] += 1
            
            # Calculate hype score
            hype_score = self.calculate_hype_score(tweet)
            metrics['total_hype_score'] += hype_score
            
            # Daily breakdown
            tweet_date = tweet.get('createdAt', '')[:10]  # Get date part
            if tweet_date not in metrics['daily_breakdown']:
                metrics['daily_breakdown'][tweet_date] = {
                    'tweets': 0, 'retweets': 0, 'replies': 0, 'likes': 0
                }
            
            metrics['daily_breakdown'][tweet_date]['tweets'] += 1
            metrics['daily_breakdown'][tweet_date]['retweets'] += tweet.get('retweetCount', 0)
            metrics['daily_breakdown'][tweet_date]['replies'] += tweet.get('replyCount', 0)
            metrics['daily_breakdown'][tweet_date]['likes'] += tweet.get('likeCount', 0)
            
            # Store top tweets by engagement
            tweet['hype_score'] = hype_score
            tweet['sentiment'] = sentiment
        
        # Get top 10 tweets by hype score
        sorted_tweets = sorted(tweets, key=lambda x: x.get('hype_score', 0), reverse=True)
        metrics['top_tweets'] = sorted_tweets[:10]
        
        return metrics

# Example usage
def main():
    # Your Apify API token (get this from your Apify account settings)
    APIFY_TOKEN = "KEY_HERE"
    
    # Initialize scraper
    scraper = NFTTwitterScraper(APIFY_TOKEN)
    
    # Example NFT data
    nft_name = "Bored Ape #1234"
    collection_name = "Bored Ape Yacht Club"
    sale_date = "2024-03-15"  # Format: YYYY-MM-DD
    
    # Run the analysis
    results = scraper.process_nft_data(nft_name, collection_name, sale_date, APIFY_TOKEN)
    
    # Print results
    print("\n=== NFT Twitter Analysis Results ===")
    print(f"Total Tweets: {results['total_tweets']}")
    print(f"Total Retweets: {results['total_retweets']}")
    print(f"Total Replies: {results['total_replies']}")
    print(f"Total Likes: {results['total_likes']}")
    print(f"Positive Tweets: {results['positive_tweets']}")
    print(f"Negative Tweets: {results['negative_tweets']}")
    print(f"Neutral Tweets: {results['neutral_tweets']}")
    print(f"Total Hype Score: {results['total_hype_score']}")
    
    print("\n=== Daily Breakdown ===")
    for date, stats in results['daily_breakdown'].items():
        print(f"{date}: {stats['tweets']} tweets, {stats['retweets']} RTs, {stats['replies']} replies")

if __name__ == "__main__":
    main()