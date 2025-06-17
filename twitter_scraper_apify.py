#!/usr/bin/env python3
"""
Apify-based Twitter scraper for NFT data collection.

Uses Apify's Twitter scraper (kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest) to avoid account suspensions.
Drop-in replacement for the original twitter_scraper.py with better historical date filtering.
"""

import asyncio
import os
import json
import httpx
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
APIFY_BASE_URL = "https://api.apify.com/v2"
ACTOR_ID = "kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest"  # New improved actor

class NFTTwitterScraper:
    """
    Apify-based Twitter scraper for collecting NFT-related tweets.
    Drop-in replacement for the original twitter_scraper.py with better historical search capabilities.
    """
    
    def __init__(self, username: str = None, email: str = None, password: str = None):
        """
        Initialize Apify Twitter scraper.
        
        Args:
            username, email, password: Not used in Apify version (kept for compatibility)
        """
        self.apify_api_key = os.getenv('APIFY_API_KEY') or os.getenv('APIFY')
        if not self.apify_api_key:
            raise ValueError("APIFY API key is required. Please add APIFY_API_KEY=your_key to .env file")
        
        self.base_url = APIFY_BASE_URL
        self.actor_id = ACTOR_ID  # New improved actor with better date filtering
        
        # HTTP client for API calls
        self.client = httpx.AsyncClient(timeout=120.0)
        
        # Rate limiting (minimize Apify API calls, not data collection)
        self.last_request_time = 0
        self.min_request_interval = 5  # 5 seconds between Apify requests to be respectful
        
        print(f"✅ Apify Twitter scraper initialized with API key: {self.apify_api_key[:8]}...")
        print(f"🔧 Using improved actor: {self.actor_id}")
    
    async def login(self):
        """Compatibility method - Apify doesn't require login."""
        print("✅ Using Apify - no login required")
        return True
    
    def _parse_twitter_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse Twitter's timestamp format: 'Tue Jun 10 18:54:23 +0000 2025'"""
        try:
            if not timestamp_str:
                return None
                
            # Handle different timestamp formats
            if isinstance(timestamp_str, str):
                # Twitter format: 'Tue Jun 10 18:54:23 +0000 2025'
                if '+0000' in timestamp_str and len(timestamp_str) > 20:
                    return datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S %z %Y')
                # ISO format fallback
                elif timestamp_str.endswith('Z'):
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    return datetime.fromisoformat(timestamp_str)
            
            return None
            
        except Exception as e:
            print(f"    ⚠️  Could not parse timestamp '{timestamp_str}': {e}")
            return None
    
    async def search_tweets_for_nft(self, nft_sale: Dict, max_tweets: int = None) -> List[Dict]:
        """
        Search for tweets related to a specific NFT sale with time filtering.
        Main method used by the data collection pipeline.
        """
        if max_tweets is None:
            print(f"🔍 Searching tweets for NFT sale - using ALL tweets found")
        else:
            print(f"🔍 Searching tweets for NFT sale - limit: {max_tweets}")
        
        # Extract parameters from sale data
        keywords = nft_sale.get('twitter_keywords', [])
        collection_name = nft_sale.get('collection_name', '')
        nft_name = nft_sale.get('nft_name', '')
        search_start = nft_sale.get('twitter_search_start')
        search_end = nft_sale.get('twitter_search_end')
        
        print(f"   🔑 Keywords: {keywords}")
        if search_start and search_end:
            # Calculate hours for display
            try:
                from datetime import datetime
                start_dt = datetime.fromisoformat(search_start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(search_end.replace('Z', '+00:00'))
                hours_diff = (end_dt - start_dt).total_seconds() / 3600
                print(f"   📅 Time window: {search_start} to {search_end} ({hours_diff:.0f}h window)")
            except:
                print(f"   📅 Time window: {search_start} to {search_end}")
        
        all_tweets = []
        
        # Search for each keyword
        keyword = keywords[0]   # Limit to top 3 keywords
        try:
            tweets = await self._search_with_time_filter(keyword, search_start, search_end, max_tweets)
            
            if tweets:
                print(f"    ✅ Found {len(tweets)} tweets for '{keyword}'")
                
                # Format tweets and add sale context
                for tweet in tweets:
                    formatted_tweet = self._format_tweet_data(tweet, nft_name, collection_name, keyword)
                    if formatted_tweet:
                        # Add sale context
                        formatted_tweet.update({
                            'sale_price_eth': nft_sale.get('sale_price_eth', 0),
                            'sale_timestamp': nft_sale.get('sale_timestamp', ''),
                            'hours_before_sale': self._calculate_hours_before_sale(
                                formatted_tweet.get('created_at'), 
                                nft_sale.get('sale_timestamp', '')
                            )
                        })
                        all_tweets.append(formatted_tweet)
                
        except Exception as e:
            print(f"    ❌ Error searching for '{keyword}': {e}")
            
    
        # Remove duplicates
        unique_tweets = self._remove_duplicate_tweets(all_tweets)
        print(f"   🔄 After deduplication: {len(all_tweets)} → {len(unique_tweets)} tweets")
        
        # Filter by time window if available
        if search_start and search_end:
            print(f"   📅 Applying precise time filter:")
            print(f"      Start: {search_start}")
            print(f"      End: {search_end}")
            
            time_filtered_tweets = self._filter_tweets_by_time(unique_tweets, search_start, search_end)
            print(f"   📅 Time filtering: {len(unique_tweets)} → {len(time_filtered_tweets)} tweets")
            
            # Show which tweets were kept/filtered
            if len(time_filtered_tweets) > 0:
                print(f"   ✅ Tweets that passed time filter:")
                for i, tweet in enumerate(time_filtered_tweets[:3], 1):
                    tweet_time = tweet.get('created_at', 'Unknown')
                    hours_before = tweet.get('hours_before_sale', 'Unknown')
                    tweet_text = tweet.get('text', '')[:40] + '...' if len(tweet.get('text', '')) > 40 else tweet.get('text', '')
                    print(f"      {i}. {tweet_time} ({hours_before}h before sale) - \"{tweet_text}\"")
                if len(time_filtered_tweets) > 3:
                    print(f"      ... and {len(time_filtered_tweets) - 3} more")
            else:
                # Check if this was a historical search
                try:
                    end_dt = datetime.fromisoformat(search_end.replace('Z', '+00:00'))
                    days_ago = (datetime.now(timezone.utc) - end_dt).days
                    if days_ago > 7:
                        print(f"   ⚠️  No historical tweets found for {days_ago} days ago")
                        print(f"   💡 New API endpoint should have better historical access")
                        print(f"   💡 Consider: 1) Using recent NFT sales, 2) Enterprise Twitter API access,")
                        print(f"              or 3) Alternative historical data sources")
                except:
                    print(f"   ⚠️  No tweets passed time filter")
            
            unique_tweets = time_filtered_tweets
        
        # Return ALL tweets if no limit specified, otherwise apply limit
        if max_tweets is None:
            result = unique_tweets  # Use ALL tweets we paid for
            print(f"✅ Collected and returning ALL {len(result)} tweets to pipeline")
        else:
            result = unique_tweets[:max_tweets]
            print(f"✅ Collected {len(unique_tweets)} total tweets from API")
            print(f"🎯 Final output: {len(result)} tweets (exactly as requested by pipeline limit)")
        
        return result

    async def _search_with_time_filter(self, keyword: str, start_time: str, end_time: str, max_tweets: int = None) -> List[Dict]:
        """Search for tweets with time filtering using Apify."""
        
        # Convert times to Apify format
        since_str, until_str = self._convert_to_apify_time_format(start_time, end_time)
        
        search_query = f"{keyword} since:{since_str} until:{until_str}"
        
        # Prepare actor input
        actor_input = {
            "searchTerms": [search_query],
            "lang": "en",
            "maxItems": max_tweets or 15,
            "twitterContent": keyword
        }
        
        try:
            # Start the actor run
            actor_id_formatted = self.actor_id.replace('/', '~')
            run_url = f"{self.base_url}/acts/{actor_id_formatted}/runs"
            run_response = await self.client.post(
                run_url,
                json=actor_input,
                params={"token": self.apify_api_key}
            )
            run_response.raise_for_status()
            run_data = run_response.json()
            
            run_id = run_data["data"]["id"]
            print(f"    🚀 Started search: {run_id}")
            
            # Wait for completion and return results
            return await self._wait_for_completion(run_id)
            
        except Exception as e:
            print(f"    ❌ Search failed: {e}")
            return []

    def _convert_to_apify_time_format(self, start_time: str, end_time: str) -> tuple[str, str]:
        """Convert ISO timestamps to Apify search format."""
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Format: YYYY-MM-DD_HH:MM:SS_UTC
            since_str = start_dt.strftime('%Y-%m-%d_%H:%M:%S_UTC')
            until_str = end_dt.strftime('%Y-%m-%d_%H:%M:%S_UTC')
            
            return since_str, until_str
            
        except Exception as e:
            # Fallback to basic date format
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                return start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d')
            except:
                return "2022-01-01", "2023-01-01"
    
    async def _wait_for_completion(self, run_id: str) -> List[Dict]:
        """Wait for actor run to complete and fetch results."""
        
        status_url = f"{self.base_url}/actor-runs/{run_id}"
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                status_response = await self.client.get(
                    status_url,
                    params={"token": self.apify_api_key}
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                status = status_data["data"]["status"]
                
                if status == "SUCCEEDED":
                    return await self._fetch_results(status_data["data"]["defaultDatasetId"])
                elif status == "FAILED":
                    print(f"    ❌ Actor run failed")
                    return []
                else:
                    print(f"    ⏳ Run {status.lower()}...")
                    await asyncio.sleep(10)
                    
            except Exception as e:
                print(f"    ❌ Error checking status: {e}")
                await asyncio.sleep(10)
        
        print(f"    ⏰ Timeout waiting for results")
        return []
    
    async def _fetch_results(self, dataset_id: str) -> List[Dict]:
        """Fetch results from Apify dataset."""
        try:
            results_url = f"{self.base_url}/datasets/{dataset_id}/items"
            results_response = await self.client.get(
                results_url,
                params={"token": self.apify_api_key, "format": "json"}
            )
            results_response.raise_for_status()
            
            results = results_response.json()
            print(f"    📊 Retrieved {len(results)} tweets from Apify (API minimum baseline)")
            
            return results
            
        except Exception as e:
            print(f"    ❌ Error fetching results: {e}")
            return []
    
    def _format_tweet_data(self, tweet: Dict, nft_name: str, collection_name: str, search_term: str) -> Optional[Dict]:
        """Format Apify tweet data to match expected structure."""
        try:
            # Extract tweet text
            tweet_text = tweet.get('text', '').strip()
            
            if not tweet_text or len(tweet_text) < 10:
                return None
            
            # Extract user info
            user_info = tweet.get('author', {}) or {}
            username = user_info.get('userName', '') or user_info.get('username', '') or tweet.get('username', '')
            user_id = user_info.get('id', '') or user_info.get('userId', '') or tweet.get('authorId', '')
            
            # Extract engagement metrics
            engagement = tweet.get('public_metrics', {}) or {}
            retweet_count = engagement.get('retweet_count', 0) or tweet.get('retweetCount', 0)
            like_count = engagement.get('like_count', 0) or tweet.get('likeCount', 0)
            reply_count = engagement.get('reply_count', 0) or tweet.get('replyCount', 0)
            
            # Extract timestamp
            created_at = tweet.get('created_at', '') or tweet.get('createdAt', '')
            
            # Extract tweet ID
            tweet_id = tweet.get('id', '') or tweet.get('tweetId', '')
            
            return {
                'id': tweet_id,
                'text': tweet_text,
                'created_at': created_at,
                'author_id': user_id,
                'username': username,
                'retweet_count': retweet_count,
                'like_count': like_count,
                'reply_count': reply_count,
                'search_term': search_term,
                'nft_name': nft_name,
                'collection_name': collection_name
            }
            
        except Exception as e:
            print(f"    ❌ Error formatting tweet: {e}")
            return None
    
    def _remove_duplicate_tweets(self, tweets: List[Dict]) -> List[Dict]:
        """Remove duplicate tweets based on tweet ID or text similarity."""
        seen_ids = set()
        seen_texts = set()
        unique_tweets = []
        
        for tweet in tweets:
            tweet_id = tweet.get('id', '')
            tweet_text = tweet.get('text', '')[:100]  # First 100 chars for similarity check
            
            if tweet_id and tweet_id not in seen_ids:
                seen_ids.add(tweet_id)
                seen_texts.add(tweet_text)
                unique_tweets.append(tweet)
            elif not tweet_id and tweet_text not in seen_texts:
                seen_texts.add(tweet_text)
                unique_tweets.append(tweet)
        
        return unique_tweets

    def _filter_tweets_by_time(self, tweets: List[Dict], start_time: str, end_time: str) -> List[Dict]:
        """Filter tweets by timestamp on the client side with detailed logging."""
        try:
            start_dt = self._parse_twitter_timestamp(start_time)
            end_dt = self._parse_twitter_timestamp(end_time)
            
            if not start_dt or not end_dt:
                print(f"    ⚠️  Could not parse time window, returning all tweets")
                return tweets
            
            print(f"    🔍 Filtering tweets between {start_dt} and {end_dt}")
            
            filtered_tweets = []
            rejected_count = 0
            
            for tweet in tweets:
                tweet_time_str = tweet.get('created_at', '')
                if tweet_time_str:
                    tweet_dt = self._parse_twitter_timestamp(tweet_time_str)
                    if tweet_dt:
                        if start_dt <= tweet_dt <= end_dt:
                            filtered_tweets.append(tweet)
                            if len(filtered_tweets) <= 3:  # Show first few matches
                                hours_before = (end_dt - tweet_dt).total_seconds() / 3600
                                print(f"       ✅ KEPT: {tweet_dt} ({hours_before:.1f}h before sale)")
                        else:
                            rejected_count += 1
                            if rejected_count <= 3:  # Show first few rejections
                                if tweet_dt > end_dt:
                                    hours_after = (tweet_dt - end_dt).total_seconds() / 3600
                                    print(f"       ❌ REJECTED: {tweet_dt} ({hours_after:.1f}h AFTER sale)")
                                else:
                                    hours_before = (start_dt - tweet_dt).total_seconds() / 3600
                                    print(f"       ❌ REJECTED: {tweet_dt} ({hours_before:.1f}h before window)")
                    else:
                        print(f"       ❌ REJECTED: Could not parse timestamp '{tweet_time_str}'")
                        rejected_count += 1
                else:
                    print(f"       ❌ REJECTED: No timestamp found")
                    rejected_count += 1
            
            if rejected_count > 3:
                print(f"       ... and {rejected_count - 3} more rejections")
            
            return filtered_tweets
            
        except Exception as e:
            print(f"    ❌ Error filtering tweets by time: {e}")
            return tweets

    def _calculate_hours_before_sale(self, tweet_time_str: str, sale_time_str: str) -> float:
        """Calculate how many hours before sale this tweet was posted."""
        try:
            if not tweet_time_str or not sale_time_str:
                return 0.0
                
            tweet_dt = self._parse_twitter_timestamp(tweet_time_str)
            sale_dt = self._parse_twitter_timestamp(sale_time_str)
            
            if not tweet_dt or not sale_dt:
                return 0.0
            
            time_diff = sale_dt - tweet_dt
            hours_before = time_diff.total_seconds() / 3600
            
            return max(0.0, hours_before)  # Return 0 if tweet was after sale
            
        except Exception as e:
            return 0.0

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Test function
async def test_apify_scraper():
    """Test the Apify scraper with realistic NFT sale data."""
    print("🧪 Testing Apify Twitter scraper...")
    
    scraper = NFTTwitterScraper()
    
    try:
        # Create a mock NFT sale with 24-hour search window
        now = datetime.now(timezone.utc)
        sale_time = now
        search_start = sale_time - timedelta(hours=24)
        
        mock_sale = {
            'collection_name': 'boredapeyachtclub',
            'nft_name': 'Bored Ape #1234',
            'sale_timestamp': sale_time.isoformat(),
            'twitter_search_start': search_start.isoformat(),
            'twitter_search_end': sale_time.isoformat(),
            'twitter_keywords': ['boredapeyachtclub', '#BAYC'],
            'sale_price_eth': 15.5
        }
        
        tweets = await scraper.search_tweets_for_nft(mock_sale)  # Use ALL tweets
        
        print(f"\n📊 Test Results:")
        print(f"   Found {len(tweets)} tweets")
        
        for i, tweet in enumerate(tweets, 1):
            print(f"   {i}. @{tweet.get('username', 'unknown')}: {tweet.get('text', '')[:80]}...")
            print(f"      ❤️ {tweet.get('like_count', 0)} | 🔄 {tweet.get('retweet_count', 0)} | 💬 {tweet.get('reply_count', 0)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_apify_scraper()) 