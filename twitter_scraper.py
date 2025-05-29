import asyncio
from twikit import Client
import datetime
import json
from typing import List, Dict, Optional
import random
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class NFTTwitterScraper:
    """
    Enhanced Twitter scraper for collecting NFT-related tweets based on sale data.
    """
    
    def __init__(self, username: str, email: str, password: str):
        self.username = username
        self.email = email
        self.password = password
        self.client = Client(language='en-US')
        self.is_logged_in = False
    
    async def login(self):
        """Login to Twitter with security measures."""
        try:
            # Try to load saved cookies first
            try:
                self.client.load_cookies('twitter_cookies.json')
                # Test if cookies work
                try:
                    await self.client.get_me()
                except AttributeError:
                    # Fallback - just test if we can access the client
                    pass
                self.is_logged_in = True
                print("✅ Successfully logged in using saved cookies.")
                return
            except:
                print("No valid cookies found, attempting fresh login...")
            
            # Add delay to avoid automation detection
            await asyncio.sleep(random.randint(2, 5))
            
            await self.client.login(
                auth_info_1=self.username,
                auth_info_2=self.email,
                password=self.password
            )
            
            # Save cookies for future use
            self.client.save_cookies('twitter_cookies.json')
            self.is_logged_in = True
            print("✅ Successfully logged in to Twitter and saved cookies.")
            
        except Exception as e:
            error_str = str(e).lower()
            print(f"Error during login: {e}")
            
            if "blockiert" in error_str or "blocked" in error_str:
                raise Exception("Twitter account is temporarily blocked due to security measures. "
                               "Please login manually on twitter.com first, wait 1-2 hours, then try again.")
            elif "password" in error_str or "falsches passwort" in error_str:
                raise Exception("Password authentication failed. Check your credentials or verify if 2FA is enabled.")
            else:
                raise
    
    async def search_tweets_for_nft(self, nft_sale: Dict, max_tweets: int = 100) -> List[Dict]:
        """
        Search for tweets related to a specific NFT sale.
        
        Args:
            nft_sale: NFT sale data dictionary
            max_tweets: Maximum number of tweets to collect
        """
        if not self.is_logged_in:
            await self.login()
        
        tweets_data = []
        
        # Parse timestamps
        search_start = datetime.datetime.fromisoformat(nft_sale['twitter_search_start'])
        search_end = datetime.datetime.fromisoformat(nft_sale['twitter_search_end'])
        
        # Try different search strategies with the keywords
        keywords = nft_sale.get('twitter_keywords', [])
        
        for keyword in keywords[:3]:  # Try top 3 keywords to avoid rate limits
            try:
                # Build search query
                search_query = self._build_search_query(
                    keyword, search_start, search_end
                )
                
                print(f"Searching for: {search_query}")
                
                # Search tweets
                tweets_result = await self.client.search_tweet(
                    search_query, 'Latest', count=min(max_tweets, 50)
                )
                
                tweets = list(tweets_result)
                
                for tweet in tweets:
                    tweet_data = self._extract_tweet_data(tweet, nft_sale, keyword)
                    if tweet_data:
                        tweets_data.append(tweet_data)
                
                # Rate limiting
                await asyncio.sleep(1)
                
                if len(tweets_data) >= max_tweets:
                    break
                    
            except Exception as e:
                print(f"Error searching for keyword '{keyword}': {e}")
                continue
        
        # Remove duplicates based on tweet ID
        unique_tweets = {tweet['tweet_id']: tweet for tweet in tweets_data}
        
        return list(unique_tweets.values())
    
    def _build_search_query(self, keyword: str, start_time: datetime.datetime, 
                           end_time: datetime.datetime) -> str:
        """Build a Twitter search query."""
        # Format timestamps for Twitter search
        since_str = start_time.strftime('%Y-%m-%d_%H:%M:%S_UTC')
        until_str = end_time.strftime('%Y-%m-%d_%H:%M:%S_UTC')
        
        # Clean keyword for search
        if keyword.startswith('#'):
            search_term = keyword
        else:
            # Use quotes for exact phrase matching
            search_term = f'"{keyword}"'
        
        return f"{search_term} since:{since_str} until:{until_str}"
    
    def _extract_tweet_data(self, tweet, nft_sale: Dict, search_keyword: str) -> Optional[Dict]:
        """Extract relevant data from a tweet."""
        try:
            user_screen_name = tweet.user.screen_name if tweet.user else 'UnknownUser'
            tweet_text = tweet.text if hasattr(tweet, 'text') else 'No Text'
            created_at = tweet.created_at if hasattr(tweet, 'created_at') else 'No Date'
            tweet_id = tweet.id if hasattr(tweet, 'id') else 'NoID'
            
            # Extract additional metrics
            retweet_count = getattr(tweet, 'retweet_count', 0)
            favorite_count = getattr(tweet, 'favorite_count', 0)
            reply_count = getattr(tweet, 'reply_count', 0)
            
            tweet_data = {
                # Tweet identifiers
                'tweet_id': tweet_id,
                'user_screen_name': user_screen_name,
                'user_id': tweet.user.id if tweet.user else None,
                
                # Tweet content
                'text': tweet_text,
                'created_at': created_at,
                'search_keyword_used': search_keyword,
                
                # Engagement metrics
                'retweet_count': retweet_count,
                'favorite_count': favorite_count,
                'reply_count': reply_count,
                
                # Links
                'tweet_url': f"https://twitter.com/{user_screen_name}/status/{tweet_id}",
                
                # NFT sale context
                'nft_collection': nft_sale['collection_name'],
                'nft_identifier': nft_sale['nft_identifier'],
                'sale_price_eth': nft_sale['sale_price_eth'],
                'sale_timestamp': nft_sale['sale_timestamp'],
                
                # Timing analysis
                'hours_before_sale': self._calculate_hours_before_sale(created_at, nft_sale['sale_timestamp']),
            }
            
            return tweet_data
            
        except Exception as e:
            print(f"Error extracting tweet data: {e}")
            return None
    
    def _calculate_hours_before_sale(self, tweet_time, sale_time_str: str) -> float:
        """Calculate how many hours before sale this tweet was posted."""
        try:
            # Handle tweet time - Twitter format: 'Thu May 29 08:21:28 +0000 2025'
            if isinstance(tweet_time, str):
                if tweet_time.endswith('Z'):
                    tweet_dt = datetime.datetime.fromisoformat(tweet_time.replace('Z', '+00:00'))
                elif '+0000' in tweet_time:
                    # Twitter format: 'Thu May 29 08:21:28 +0000 2025' 
                    tweet_dt = datetime.datetime.strptime(tweet_time, '%a %b %d %H:%M:%S %z %Y')
                else:
                    tweet_dt = datetime.datetime.fromisoformat(tweet_time)
                    if tweet_dt.tzinfo is None:
                        tweet_dt = tweet_dt.replace(tzinfo=datetime.timezone.utc)
            else:
                tweet_dt = tweet_time
                if tweet_dt.tzinfo is None:
                    tweet_dt = tweet_dt.replace(tzinfo=datetime.timezone.utc)
            
            # Handle sale time - ensure it's timezone-aware
            if isinstance(sale_time_str, str):
                if '+' in sale_time_str or sale_time_str.endswith('Z'):
                    sale_dt = datetime.datetime.fromisoformat(sale_time_str.replace('Z', '+00:00'))
                else:
                    sale_dt = datetime.datetime.fromisoformat(sale_time_str)
                    if sale_dt.tzinfo is None:
                        sale_dt = sale_dt.replace(tzinfo=datetime.timezone.utc)
            else:
                sale_dt = sale_time_str
                if sale_dt.tzinfo is None:
                    sale_dt = sale_dt.replace(tzinfo=datetime.timezone.utc)
            
            # Now both should be timezone-aware
            diff = sale_dt - tweet_dt
            return diff.total_seconds() / 3600  # Convert to hours
            
        except Exception as e:
            print(f"Error calculating hours before sale: {e}")
            return 0.0
    
    async def process_nft_samples(self, nft_samples: List[Dict], 
                                tweets_per_nft: int = 50) -> Dict[str, List[Dict]]:
        """
        Process multiple NFT samples and collect tweets for each.
        
        Args:
            nft_samples: List of NFT sale data
            tweets_per_nft: Maximum tweets to collect per NFT
            
        Returns:
            Dictionary mapping NFT identifiers to their tweet data
        """
        if not self.is_logged_in:
            await self.login()
        
        all_tweets_data = {}
        
        for i, nft_sale in enumerate(nft_samples):
            nft_key = f"{nft_sale['collection_slug']}_{nft_sale['nft_identifier']}"
            
            print(f"\nProcessing NFT {i+1}/{len(nft_samples)}: {nft_key}")
            print(f"Sale price: {nft_sale['sale_price_eth']} ETH")
            print(f"Sale time: {nft_sale['sale_timestamp']}")
            
            try:
                tweets = await self.search_tweets_for_nft(nft_sale, tweets_per_nft)
                all_tweets_data[nft_key] = tweets
                
                print(f"Found {len(tweets)} tweets for {nft_key}")
                
                # Rate limiting between NFTs
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Error processing NFT {nft_key}: {e}")
                all_tweets_data[nft_key] = []
                continue
        
        return all_tweets_data
    
    async def calculate_social_metrics(self, tweets_data: List[Dict]) -> Dict:
        """
        Calculate social metrics from collected tweets.
        
        Args:
            tweets_data: List of tweet data dictionaries
            
        Returns:
            Dictionary with social metrics
        """
        if not tweets_data:
            return {
                'total_tweets': 0,
                'unique_users': 0,
                'total_engagement': 0,
                'avg_engagement': 0,
                'tweets_last_hour': 0,
                'tweets_last_6_hours': 0,
                'sample_tweets': []
            }
        
        # Calculate unique users
        unique_users = set(tweet['user_id'] for tweet in tweets_data if tweet['user_id'])
        
        # Calculate engagement
        total_engagement = sum(
            tweet['retweet_count'] + tweet['favorite_count'] + tweet['reply_count']
            for tweet in tweets_data
        )
        
        avg_engagement = total_engagement / len(tweets_data) if tweets_data else 0
        
        # Time-based metrics
        tweets_last_hour = sum(1 for tweet in tweets_data if tweet['hours_before_sale'] <= 1)
        tweets_last_6_hours = sum(1 for tweet in tweets_data if tweet['hours_before_sale'] <= 6)
        
        # Sample tweets for sentiment analysis (random 10)
        sample_tweets = random.sample(tweets_data, min(10, len(tweets_data)))
        
        return {
            'total_tweets': len(tweets_data),
            'unique_users': len(unique_users),
            'total_engagement': total_engagement,
            'avg_engagement': avg_engagement,
            'tweets_last_hour': tweets_last_hour,
            'tweets_last_6_hours': tweets_last_6_hours,
            'sample_tweets': sample_tweets
        }
    
    async def save_tweets_data(self, tweets_data: Dict, filename: str = None):
        """Save collected tweets data to JSON file."""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nft_tweets_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(tweets_data, f, indent=2, default=str)
        
        print(f"Saved tweets data to {filename}")
        return filename

    async def search_nft_tweets(self, nft_name: str, collection_name: str, limit: int = 20) -> List[Dict]:
        """
        Search for tweets about a specific NFT - compatibility method for data_collector.
        
        Args:
            nft_name: Name of the NFT
            collection_name: Collection name
            limit: Maximum number of tweets to return
            
        Returns:
            List of tweet dictionaries
        """
        if not self.is_logged_in:
            await self.login()
        
        tweets_data = []
        
        try:
            # Build search terms with multiple strategies
            search_strategies = []
            
            # Strategy 1: Collection name only (most reliable)
            if collection_name and collection_name != 'Unknown Collection':
                # Clean collection name for search
                clean_collection = collection_name.replace('-', ' ').replace('_', ' ')
                search_strategies.append(clean_collection)
                search_strategies.append(f"#{collection_name}")
                
                # Common abbreviations for popular collections
                if 'boredape' in collection_name.lower():
                    search_strategies.extend(['BAYC', '#BAYC', 'Bored Ape', 'BoredApe'])
                elif 'pudgy' in collection_name.lower():
                    search_strategies.extend(['Pudgy Penguins', '#PudgyPenguins', 'pudgy'])
                elif 'crypto' in collection_name.lower() and 'punk' in collection_name.lower():
                    search_strategies.extend(['CryptoPunk', '#CryptoPunks', 'punk'])
            
            # Strategy 2: NFT name if available and meaningful
            if nft_name and nft_name != 'Unknown NFT' and not nft_name.startswith(collection_name):
                search_strategies.append(nft_name)
            
            # Strategy 3: Generic NFT terms as last resort
            search_strategies.extend(['NFT', '#NFT', 'ethereum nft'])
            
            # Try each search strategy until we get results
            for search_term in search_strategies[:3]:  # Limit to first 3 strategies for speed
                try:
                    print(f"  🔍 Searching Twitter for: \"{search_term}\" -filter:retweets")
                    
                    # Search for tweets
                    tweets = await self.client.search_tweet(search_term, product='Latest', count=limit)
                    
                    if tweets:
                        print(f"    ✅ Found {len(tweets)} tweets with '{search_term}'")
                        for tweet in tweets:
                            tweet_data = {
                                'text': tweet.text or '',
                                'user_id': tweet.user.id if tweet.user else '',
                                'username': getattr(tweet.user, 'username', getattr(tweet.user, 'screen_name', '')) if tweet.user else '',
                                'created_at': getattr(tweet, 'created_at', None),
                                'favorite_count': getattr(tweet, 'favorite_count', 0),
                                'retweet_count': getattr(tweet, 'retweet_count', 0),
                                'reply_count': getattr(tweet, 'reply_count', 0),
                                'search_term_used': search_term,
                                'nft_name': nft_name,
                                'collection_name': collection_name
                            }
                            tweets_data.append(tweet_data)
                        
                        # If we found enough tweets, stop searching
                        if len(tweets_data) >= limit:
                            tweets_data = tweets_data[:limit]
                            break
                        
                    else:
                        print(f"    ⚠️  No tweets found for '{search_term}'")
                        
                except Exception as search_error:
                    print(f"    Error searching for '{search_term}': {search_error}")
                    continue
                
                # Small delay between searches
                await asyncio.sleep(2)
            
            print(f"  ✅ Found {len(tweets_data)} tweets total for {nft_name} ({collection_name})")
            return tweets_data
            
        except Exception as e:
            print(f"  ❌ Error in Twitter search: {e}")
            return []

    def _extract_simple_tweet_data(self, tweet, nft_name: str, collection_name: str) -> Optional[Dict]:
        """Extract simple tweet data for compatibility with data_collector."""
        try:
            user_screen_name = tweet.user.screen_name if tweet.user else 'UnknownUser'
            tweet_text = tweet.text if hasattr(tweet, 'text') else 'No Text'
            created_at = tweet.created_at if hasattr(tweet, 'created_at') else None
            tweet_id = tweet.id if hasattr(tweet, 'id') else 'NoID'
            user_id = tweet.user.id if tweet.user else None
            
            # Extract engagement metrics
            retweet_count = getattr(tweet, 'retweet_count', 0)
            favorite_count = getattr(tweet, 'favorite_count', 0) or getattr(tweet, 'like_count', 0)
            reply_count = getattr(tweet, 'reply_count', 0)
            
            tweet_data = {
                # Tweet identifiers
                'tweet_id': str(tweet_id),
                'user_screen_name': user_screen_name,
                'user_id': str(user_id) if user_id else None,
                
                # Tweet content
                'text': tweet_text,
                'created_at': str(created_at) if created_at else None,
                
                # Engagement metrics
                'retweet_count': retweet_count or 0,
                'favorite_count': favorite_count or 0,
                'reply_count': reply_count or 0,
                
                # Context
                'nft_name': nft_name,
                'collection_name': collection_name,
                
                # URL
                'tweet_url': f"https://twitter.com/{user_screen_name}/status/{tweet_id}",
            }
            
            return tweet_data
            
        except Exception as e:
            print(f"    Error extracting tweet data: {e}")
            return None

# Integration function
async def collect_nft_training_data(username: str, email: str, password: str, 
                                  nft_samples_file: str = None):
    """
    Complete pipeline to collect NFT samples and their associated tweets.
    
    Args:
        username, email, password: Twitter credentials
        nft_samples_file: Path to existing NFT samples JSON file
    """
    
    # Step 1: Collect NFT samples (if not provided)
    if nft_samples_file:
        print(f"Loading NFT samples from {nft_samples_file}")
        with open(nft_samples_file, 'r') as f:
            nft_samples = json.load(f)
    else:
        print("Collecting fresh NFT samples from OpenSea...")
        from opensea_collector import collect_nft_samples
        nft_samples, samples_file = await collect_nft_samples()
    
    # Step 2: Collect tweets for each NFT
    print(f"\nCollecting tweets for {len(nft_samples)} NFT samples...")
    scraper = NFTTwitterScraper(username, email, password)
    
    try:
        tweets_data = await scraper.process_nft_samples(nft_samples, tweets_per_nft=30)
        
        # Step 3: Calculate metrics and save
        training_data = []
        
        for nft_key, tweets in tweets_data.items():
            # Find corresponding NFT sale data
            nft_sale = next((nft for nft in nft_samples 
                           if f"{nft['collection_slug']}_{nft['nft_identifier']}" == nft_key), None)
            
            if nft_sale:
                social_metrics = await scraper.calculate_social_metrics(tweets)
                
                training_record = {
                    'nft_data': nft_sale,
                    'social_metrics': social_metrics,
                    'tweets': tweets
                }
                
                training_data.append(training_record)
        
        # Save training data
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        training_filename = f"nft_training_data_{timestamp}.json"
        
        with open(training_filename, 'w') as f:
            json.dump(training_data, f, indent=2, default=str)
        
        print(f"\nTraining data collection complete!")
        print(f"Collected data for {len(training_data)} NFTs")
        print(f"Training data saved to: {training_filename}")
        
        return training_data, training_filename
        
    except Exception as e:
        print(f"Error in training data collection: {e}")
        raise

if __name__ == "__main__":
    # Example usage
    USERNAME = 'your_username'
    EMAIL = 'your_email@gmail.com'
    PASSWORD = 'your_password'
    
    asyncio.run(collect_nft_training_data(USERNAME, EMAIL, PASSWORD)) 