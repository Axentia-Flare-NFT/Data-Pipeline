#!/usr/bin/env python3
"""
NFT Data Collector with Advanced Consensus Sentiment Analysis

Comprehensive tool for collecting NFT sales data with social media metrics
and Flare AI consensus-based sentiment analysis for ML training.
"""

import asyncio
import os
import pandas as pd
import json
from typing import List, Dict, Optional
from datetime import datetime
import aiofiles

from opensea_collector import OpenSeaCollector
from twitter_scraper import NFTTwitterScraper
from sentiment_analyzer_advanced import AdvancedNFTSentimentAnalyzer

class NFTDataCollector:
    """Main NFT data collection orchestrator with advanced consensus sentiment analysis."""
    
    def __init__(self, twitter_username: str, twitter_email: str, twitter_password: str,
                 opensea_api_key: str = None):
        self.opensea = OpenSeaCollector(opensea_api_key)
        self.twitter = NFTTwitterScraper(twitter_username, twitter_email, twitter_password)
        
        # Initialize advanced sentiment analyzer
        self.sentiment_analyzer = self._initialize_sentiment_analyzer()
        
        # Data storage
        self.collected_data = []
        self.metadata_data = []
        self.tweets_data = []
        
        # Progress tracking
        self.total_nfts = 0
        self.processed_nfts = 0
        
        print(f"✅ NFT Data Collector initialized with Advanced Flare AI Consensus Learning")
    
    def _initialize_sentiment_analyzer(self):
        """Initialize the advanced sentiment analyzer."""
        
        if not os.getenv('OPENROUTER_API_KEY'):
            raise ValueError("OPENROUTER_API_KEY is required for advanced consensus learning. Please add it to your .env file.")
        
        try:
            analyzer = AdvancedNFTSentimentAnalyzer()
            print("🚀 Advanced Flare AI Consensus Learning initialized")
            return analyzer
        except Exception as e:
            raise ValueError(f"Failed to initialize advanced sentiment analyzer: {e}")
    
    async def collect_nft_sales(self, collection_slug: str, limit: int = 50) -> List[Dict]:
        """Collect NFT sales data for a specific collection."""
        print(f"\n📊 Collecting {limit} sales from {collection_slug}...")
        
        try:
            events_data = await self.opensea.get_collection_events(collection_slug, event_type="sale", limit=limit)
            # Extract the events list from the response
            sales = events_data.get('asset_events', []) if isinstance(events_data, dict) else []
            print(f"✅ Retrieved {len(sales)} sales from OpenSea")
            return sales
        except Exception as e:
            print(f"❌ Error collecting sales data: {e}")
            return []
    
    async def collect_social_data(self, nft_name: str, collection_name: str, limit: int = 20) -> Dict:
        """Collect social media data and sentiment for an NFT."""
        
        # Search for tweets about this NFT
        try:
            tweets = await self.twitter.search_nft_tweets(nft_name, collection_name, limit=limit)
            
            if not tweets:
                return self._empty_social_metrics()
            
            # Calculate basic social metrics
            unique_tweeters = len(set(tweet.get('user_id', '') for tweet in tweets))
            total_tweets = len(tweets)
            total_engagement = sum(
                tweet.get('favorite_count', 0) + 
                tweet.get('retweet_count', 0) + 
                tweet.get('reply_count', 0) 
                for tweet in tweets
            )
            
            # Perform advanced consensus sentiment analysis
            try:
                sentiment_result = await self.sentiment_analyzer.analyze_tweets_sentiment(tweets)
            except Exception as e:
                print(f"⚠️  Sentiment analysis failed: {e}")
                sentiment_result = self._empty_sentiment_metrics()
            
            # Store raw tweets for analysis
            for tweet in tweets:
                tweet['nft_name'] = nft_name
                tweet['collection_name'] = collection_name
                self.tweets_data.append(tweet)
            
            # Combine social and sentiment metrics
            social_metrics = {
                'unique_tweeters': unique_tweeters,
                'total_tweets': total_tweets,
                'total_engagement': total_engagement,
                'avg_engagement_per_tweet': total_engagement / total_tweets if total_tweets > 0 else 0,
                **sentiment_result
            }
            
            return social_metrics
                
        except Exception as e:
            print(f"⚠️  Error collecting social data: {e}")
            return self._empty_social_metrics()
    
    def _empty_social_metrics(self) -> Dict:
        """Return empty social metrics."""
        return {
            'unique_tweeters': 0,
            'total_tweets': 0,
            'total_engagement': 0,
            'avg_engagement_per_tweet': 0,
            **self._empty_sentiment_metrics()
        }
    
    def _empty_sentiment_metrics(self) -> Dict:
        """Return empty sentiment metrics for advanced analyzer."""
        return {
            'avg_sentiment': 0.0,
            'sentiment_std': 0.0,
            'sentiment_confidence': 0.0,
            'consensus_quality': 0.0,
            'positive_tweets': 0,
            'negative_tweets': 0,
            'neutral_tweets': 0,
            'sentiment_range_min': 0.0,
            'sentiment_range_max': 0.0,
            'analyzed_tweet_count': 0,
            'consensus_model_count': 0,
            'consensus_iterations': 0
        }
    
    async def collect_nft_data(self, nft_sale: Dict, collection_name: str, tweets_per_nft: int = 20) -> Dict:
        """Collect comprehensive data for a single NFT sale."""
        
        # Extract NFT info from the OpenSea API v2 event structure
        nft_info = nft_sale.get('nft', {})
        
        # Get token ID - this should be available
        token_id = nft_info.get('identifier', 'unknown')
        
        # Get NFT name - handle case where OpenSea name is None
        opensea_name = nft_info.get('name')
        if opensea_name and opensea_name.strip():
            nft_name = opensea_name
        else:
            # Generate name from collection and token ID
            nft_name = f"{collection_name} #{token_id}"
        
        print(f"  📱 Processing: {nft_name} (#{token_id})")
        
        # Collect social data with sentiment analysis
        social_data = await self.collect_social_data(nft_name, collection_name, limit=tweets_per_nft)
        
        # Extract sale information from the payment structure
        payment_info = nft_sale.get('payment', {})
        
        # Get sale price in wei and convert to ETH
        sale_price_wei = float(payment_info.get('quantity', 0))
        decimals = int(payment_info.get('decimals', 18))
        sale_price_eth = sale_price_wei / (10 ** decimals) if sale_price_wei > 0 else 0
        
        # Get transaction and timestamp info
        transaction_hash = nft_sale.get('transaction', '')
        event_timestamp = nft_sale.get('event_timestamp', '')
        
        # Convert timestamp to readable format if it's a unix timestamp
        sale_timestamp = event_timestamp
        if isinstance(event_timestamp, int):
            from datetime import datetime
            sale_timestamp = datetime.fromtimestamp(event_timestamp).isoformat()
        
        # Combine all data
        nft_data = {
            # NFT Identity
            'collection_slug': collection_name,
            'nft_name': nft_name,
            'token_id': token_id,
            'asset_contract_address': nft_info.get('contract', ''),
            
            # Sale Information
            'sale_price_wei': sale_price_wei,
            'sale_price_eth': sale_price_eth,
            'payment_token_symbol': payment_info.get('symbol', 'ETH'),
            'sale_timestamp': sale_timestamp,
            'transaction_hash': transaction_hash,
            
            # Market Context
            'seller_address': nft_sale.get('seller', ''),
            'buyer_address': nft_sale.get('buyer', ''),
            
            # Social & Sentiment Data
            **social_data
        }
        
        # Store metadata separately
        metadata = {
            'collection_slug': collection_name,
            'nft_name': nft_name,
            'token_id': token_id,
            'description': nft_info.get('description', ''),
            'image_url': nft_info.get('image_url', ''),
            'display_image_url': nft_info.get('display_image_url', ''),
            'external_link': nft_info.get('opensea_url', ''),
            'metadata_url': nft_info.get('metadata_url', ''),
            'is_nsfw': nft_info.get('is_nsfw', False)
        }
        
        self.metadata_data.append(metadata)
        self.collected_data.append(nft_data)
        
        # Update progress
        self.processed_nfts += 1
        progress = (self.processed_nfts / self.total_nfts) * 100 if self.total_nfts > 0 else 0
        print(f"    ✅ Complete ({self.processed_nfts}/{self.total_nfts} - {progress:.1f}%)")
        
        return nft_data
    
    async def save_data(self):
        """Save collected data to clean CSV files."""
        if not self.collected_data:
            print("⚠️  No data to save")
            return
        
        # Ensure output directory exists
        os.makedirs('nft_data', exist_ok=True)
        
        # Convert to DataFrame for clean processing
        df = pd.DataFrame(self.collected_data)
        
        # Clean and standardize column names - handle sentiment_range properly
        for i, row in enumerate(self.collected_data):
            if 'sentiment_range' in row and isinstance(row['sentiment_range'], tuple):
                self.collected_data[i]['sentiment_range_min'] = row['sentiment_range'][0]
                self.collected_data[i]['sentiment_range_max'] = row['sentiment_range'][1]
                
        # Recreate DataFrame with flattened data
        df = pd.DataFrame(self.collected_data)
        
        # Clean and standardize column names
        column_mapping = {
            'nft_name': 'nft_name',
            'token_id': 'token_id', 
            'collection_name': 'collection_name',
            'collection_slug': 'collection_slug',
            'sale_price_eth': 'sale_price_eth',
            'sale_price_usd': 'sale_price_usd',
            'transaction_hash': 'transaction_hash',
            'sale_date': 'sale_date',
            'total_tweets': 'total_tweets',
            'unique_tweeters': 'unique_tweeters',
            'total_engagement': 'total_engagement',
            'avg_engagement_per_tweet': 'avg_engagement_per_tweet',
            'avg_sentiment': 'avg_sentiment',
            'sentiment_confidence': 'sentiment_confidence',
            'consensus_quality': 'consensus_quality',
            'positive_tweets': 'positive_tweets',
            'negative_tweets': 'negative_tweets', 
            'neutral_tweets': 'neutral_tweets',
            'sentiment_range_min': 'sentiment_range_min',
            'sentiment_range_max': 'sentiment_range_max',
            'analyzed_tweet_count': 'analyzed_tweet_count',
            'consensus_model_count': 'consensus_model_count',
            'consensus_iterations': 'consensus_iterations'
        }
        
        # Rename columns for consistency
        df = df.rename(columns=column_mapping)
        
        # Ensure all numeric columns are properly formatted
        numeric_columns = [
            'sale_price_eth', 'sale_price_usd', 'total_tweets', 'unique_tweeters',
            'total_engagement', 'avg_engagement_per_tweet', 'avg_sentiment',
            'sentiment_confidence', 'consensus_quality', 'positive_tweets',
            'negative_tweets', 'neutral_tweets', 'sentiment_range_min',
            'sentiment_range_max', 'analyzed_tweet_count', 'consensus_model_count',
            'consensus_iterations'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Round decimal columns to reasonable precision
        decimal_columns = [
            'sale_price_eth', 'sale_price_usd', 'avg_engagement_per_tweet',
            'avg_sentiment', 'sentiment_confidence', 'consensus_quality',
            'sentiment_range_min', 'sentiment_range_max'
        ]
        
        for col in decimal_columns:
            if col in df.columns:
                df[col] = df[col].round(6)
        
        # Save main features dataset
        features_file = 'nft_data/nft_features.csv'
        df.to_csv(features_file, index=False)
        print(f"✅ Clean dataset saved: {features_file}")
        print(f"   Columns: {len(df.columns)}, Rows: {len(df)}")
        
        # Save metadata file with collection info
        metadata = []
        for _, row in df.iterrows():
            metadata.append({
                'collection_slug': row.get('collection_slug', ''),
                'collection_name': row.get('collection_name', ''),
                'nft_name': row.get('nft_name', ''),
                'token_id': row.get('token_id', ''),
                'transaction_hash': row.get('transaction_hash', ''),
                'sale_date': row.get('sale_date', ''),
                'data_collection_timestamp': datetime.now().isoformat()
            })
        
        metadata_df = pd.DataFrame(metadata)
        metadata_file = 'nft_data/nft_metadata.csv'
        metadata_df.to_csv(metadata_file, index=False)
        print(f"✅ Metadata saved: {metadata_file}")
        
        # Save individual tweets if available
        if hasattr(self, 'tweets_data') and self.tweets_data:
            tweets_df = pd.DataFrame(self.tweets_data)
            tweets_file = 'nft_data/raw_tweets.csv'
            tweets_df.to_csv(tweets_file, index=False)
            print(f"✅ Individual tweets saved: {tweets_file}")
        
        # Print summary of saved data
        print(f"\n📊 Data Summary:")
        print(f"   NFTs processed: {len(df)}")
        if 'avg_sentiment' in df.columns:
            sentiment_mean = df['avg_sentiment'].mean()
            print(f"   Average sentiment: {sentiment_mean:.3f}")
            print(f"   Sentiment range: {df['avg_sentiment'].min():.3f} to {df['avg_sentiment'].max():.3f}")
        if 'total_tweets' in df.columns:
            print(f"   Total tweets analyzed: {df['total_tweets'].sum()}")
        if 'total_engagement' in df.columns:
            print(f"   Total engagement: {df['total_engagement'].sum():,}")
        
        print(f"   Data files created in: nft_data/")
        print(f"   • nft_features.csv (main dataset with sentiment & hype metrics)")
        print(f"   • nft_metadata.csv (NFT details and timestamps)")
        if hasattr(self, 'tweets_data'):
            print(f"   • raw_tweets.csv (individual tweet data)")
    
    def get_progress_stats(self) -> Dict:
        """Get collection progress statistics."""
        
        if not self.collected_data:
            return {
            'total_nfts': 0,
                'collections': [],
                'price_range': (0.0, 0.0),
                'avg_sale_price': 0.0,
            'total_tweets': 0,
                'avg_unique_tweeters': 0.0,
                'sentiment_analyzer_type': type(self.sentiment_analyzer).__name__ if self.sentiment_analyzer else None,
                'timestamp': datetime.now().isoformat()
            }
        
        df = pd.DataFrame(self.collected_data)
        
        return {
            'total_nfts': len(df),
            'collections': df['collection_slug'].unique().tolist(),
            'price_range': (df['sale_price_eth'].min(), df['sale_price_eth'].max()),
            'avg_sale_price': df['sale_price_eth'].mean(),
            'total_tweets': df['total_tweets'].sum(),
            'avg_unique_tweeters': df['unique_tweeters'].mean(),
            'sentiment_analyzer_type': type(self.sentiment_analyzer).__name__ if self.sentiment_analyzer else None,
            'timestamp': datetime.now().isoformat()
        }

async def collect_nft_data(collections: List[str], sales_per_collection: int,
                          twitter_username: str, twitter_email: str, twitter_password: str,
                          opensea_api_key: str = None, tweets_per_nft: int = 20, 
                          collection_delay_seconds: int = 180) -> NFTDataCollector:
    """
    Main entry point for NFT data collection.
    
    Args:
        collections: List of OpenSea collection slugs
        sales_per_collection: Number of sales to collect per collection
        twitter_username: Twitter username for authentication
        twitter_email: Twitter email for authentication  
        twitter_password: Twitter password for authentication
        opensea_api_key: OpenSea API key (optional)
        tweets_per_nft: Number of tweets to analyze per NFT (default: 20)
        collection_delay_seconds: Delay between collections in seconds (default: 180)
    
    Returns:
        NFTDataCollector instance with collected data
    """
    
    collector = NFTDataCollector(twitter_username, twitter_email, twitter_password, opensea_api_key)
    
    # Calculate total NFTs for progress tracking
    collector.total_nfts = len(collections) * sales_per_collection
    
    print(f"\n🚀 Starting NFT data collection:")
    print(f"   Collections: {len(collections)}")
    print(f"   Sales per collection: {sales_per_collection}")
    print(f"   Total target: {collector.total_nfts} NFTs")
    print(f"   Tweets per NFT: {tweets_per_nft}")
    if collector.sentiment_analyzer:
        print(f"   Sentiment analysis: {type(collector.sentiment_analyzer).__name__}")
    print()
    
    for i, collection_slug in enumerate(collections, 1):
        print(f"\n📚 Collection {i}/{len(collections)}: {collection_slug}")
        
        # Collect sales data
        sales = await collector.collect_nft_sales(collection_slug, limit=sales_per_collection)
        
        if not sales:
            print(f"⚠️  No sales data found for {collection_slug}, skipping...")
            continue
        
        # Process each sale
        for sale in sales[:sales_per_collection]:
            try:
                await collector.collect_nft_data(sale, collection_slug, tweets_per_nft=tweets_per_nft)
                
                # Rate limiting
                await asyncio.sleep(8)  # 8 seconds between NFTs for Twitter API
                
            except Exception as e:
                print(f"❌ Error processing NFT sale: {e}")
                continue
        
        # Longer pause between collections
        if i < len(collections):
            print(f"⏳ Collection {collection_slug} complete. Waiting {collection_delay_seconds} seconds before next collection...")
            await asyncio.sleep(collection_delay_seconds)
    
    # Save all collected data
    await collector.save_data()
    
    print(f"\n🎉 Data collection complete!")
    stats = collector.get_progress_stats()
    print(f"   Total NFTs collected: {stats['total_nfts']}")
    print(f"   Collections processed: {len(stats['collections'])}")
    print(f"   Sentiment analyzer used: {stats['sentiment_analyzer_type']}")
    
    return collector

# Example usage:
# if __name__ == "__main__":
#     # See sample_test.py for small tests
#     # See full_collection.py for full data collection
#     pass 