#!/usr/bin/env python3
"""
NFT Data Collection Pipeline

Collects NFT sales data, tweets, and performs sentiment analysis.
"""

import asyncio
import argparse
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from opensea_collector import OpenSeaCollector
from twitter_scraper_apify import NFTTwitterScraper
from sentiment_analyzer_advanced import SimpleNFTSentimentAnalyzer

# Configuration
RUN_MODES = {
    'test': {
        'description': 'Quick test run',
        'opensea_limit': 3,
        'tweets_per_search': 30,
        'collections': ['boredapeyachtclub', 'pudgypenguins', 'azuki'],
        'use_historical_data': False,
    },
    'full': {
        'description': 'Full production run',
        'opensea_limit': 1000,
        'tweets_per_search': 50,
        'collections': [
            'boredapeyachtclub', 'cryptopunks', 'pudgypenguins', 
            'azuki', 'clonex', 'doodles-official'
        ],
        'use_historical_data': False,
    }
}

REQUIRED_API_KEYS = {
    'OPENSEA_API_KEY': 'OpenSea API key',
    'APIFY_API_KEY': 'Apify API key', 
    'OPENROUTER_API_KEY': 'OpenRouter API key'
}

OUTPUT_DIR = 'nft_data'

class NFTPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.opensea_collector = None
        self.twitter_scraper = None
        self.sentiment_analyzer = None
        
    def _check_api_keys(self):
        """Verify required API keys are present."""
        missing_keys = [key for key in REQUIRED_API_KEYS if not os.getenv(key)]
        if missing_keys:
            print(f"❌ Missing API keys: {', '.join(missing_keys)}")
            sys.exit(1)
        
    async def initialize(self):
        """Initialize pipeline components."""
        print(f"🚀 Initializing {self.config['description']}")
        print(f"📊 Target: {self.config['opensea_limit']} NFT sales")
        
        self._check_api_keys()
        
        self.opensea_collector = OpenSeaCollector()
        self.twitter_scraper = NFTTwitterScraper()
        self.sentiment_analyzer = SimpleNFTSentimentAnalyzer()
        
        print("✅ Components initialized\n")
            
    async def collect_opensea_data(self) -> List[Dict]:
        """Collect NFT sales data from OpenSea."""
        print("📈 Collecting NFT sales data...")
        
        try:
            sales_per_collection = max(1, self.config['opensea_limit'] // len(self.config['collections']))
            
            all_sales = await self.opensea_collector.collect_sample_data(
                collection_slugs=self.config['collections'],
                sales_per_collection=sales_per_collection,
                use_historical_data=self.config.get('use_historical_data', True)
            )
            
            if not all_sales:
                print("❌ No sales data collected")
                return []
            
            # Limit to target number
            all_sales = all_sales[:self.config['opensea_limit']]
            print(f"📊 Collected {len(all_sales)} NFT sales\n")
            
            return all_sales
            
        except Exception as e:
            print(f"❌ Error collecting data: {e}")
            return []
        
    async def collect_twitter_data(self, nft_sales: List[Dict]) -> List[Dict]:
        """Collect Twitter data for NFT sales."""
        print("🐦 Collecting Twitter data...")
        
        all_tweets = []
        for i, sale in enumerate(nft_sales, 1):
            nft_name = sale.get('nft_name', f"NFT #{sale.get('token_id', 'Unknown')}")
            print(f"  [{i}/{len(nft_sales)}] {nft_name}")
            
            try:
                sale_data = self._prepare_sale_for_twitter(sale)
                tweets = await self.twitter_scraper.search_tweets_for_nft(
                    nft_sale=sale_data,
                    max_tweets=self.config['tweets_per_search']
                )
                
                if tweets:
                    all_tweets.extend(tweets)
                    print(f"    ✅ Found {len(tweets)} tweets")
                else:
                    print(f"    ⚠️ No tweets found")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
                
        print(f"🐦 Collected {len(all_tweets)} total tweets\n")
        return all_tweets
        
    def _prepare_sale_for_twitter(self, sale: Dict) -> Dict:
        """Convert sale data for Twitter scraper."""
        sale_timestamp = sale.get('sale_timestamp')
        if sale_timestamp:
            sale_time = datetime.fromisoformat(sale_timestamp.replace('Z', '+00:00'))
            search_start = sale_time - timedelta(hours=24)
        else:
            search_start = sale.get('twitter_search_start')
            sale_time = sale.get('twitter_search_end')
        
        return {
            'nft_name': sale.get('nft_name') or f"NFT #{sale.get('token_id', 'Unknown')}",
            'collection_name': sale.get('collection_name', 'Unknown'),
            'twitter_keywords': sale.get('twitter_keywords', [sale.get('collection_name', 'nft')]),
            'twitter_search_start': search_start.isoformat() if hasattr(search_start, 'isoformat') else search_start,
            'twitter_search_end': sale_time.isoformat() if hasattr(sale_time, 'isoformat') else sale_time,
            'sale_price_eth': sale.get('sale_price_eth', 0),
            'sale_timestamp': sale.get('sale_timestamp')
        }
        
    async def analyze_sentiment(self, tweets: List[Dict]) -> Dict[str, Dict]:
        """Analyze sentiment of tweets grouped by NFT sale."""
        if not tweets:
            print("⚠️ No tweets to analyze\n")
            return {}
            
        print(f"🧠 Analyzing sentiment for {len(tweets)} tweets...")
        
        # Group tweets by NFT sale
        tweets_by_sale = {}
        for tweet in tweets:
            collection = tweet.get('collection_name', 'Unknown')
            nft_name = tweet.get('nft_name', 'Unknown')
            sale_timestamp = tweet.get('sale_timestamp', 'Unknown')
            sale_key = f"{collection}|{nft_name}|{sale_timestamp}"
            
            if sale_key not in tweets_by_sale:
                tweets_by_sale[sale_key] = {
                    'tweets': [],
                    'collection_name': collection,
                    'nft_name': nft_name,
                    'sale_timestamp': sale_timestamp,
                    'sale_price_eth': tweet.get('sale_price_eth', 0)
                }
            
            tweets_by_sale[sale_key]['tweets'].append(tweet)
        
        print(f"  📊 Grouped into {len(tweets_by_sale)} NFT sales")
        
        # Analyze sentiment for each sale
        sale_sentiment_results = {}
        for sale_key, sale_data in tweets_by_sale.items():
            sale_tweets = sale_data['tweets']
            nft_name = sale_data['nft_name']
            
            try:
                sentiment_metrics = await self.sentiment_analyzer.analyze_tweets_sentiment(sale_tweets)
                
                if sentiment_metrics and sentiment_metrics.get('analyzed_tweet_count', 0) > 0:
                    sale_sentiment_results[sale_key] = {
                        'collection_name': sale_data['collection_name'],
                        'nft_name': nft_name,
                        'sale_timestamp': sale_data['sale_timestamp'],
                        'sale_price_eth': sale_data['sale_price_eth'],
                        'tweet_count': len(sale_tweets),
                        'avg_sentiment': sentiment_metrics['avg_sentiment'],
                        'sentiment_confidence': sentiment_metrics['sentiment_confidence'],
                        'consensus_quality': sentiment_metrics['consensus_quality'],
                        'positive_tweets': sentiment_metrics['positive_tweets'],
                        'negative_tweets': sentiment_metrics['negative_tweets'],
                        'neutral_tweets': sentiment_metrics['neutral_tweets'],
                        'sentiment_range_min': sentiment_metrics['sentiment_range_min'],
                        'sentiment_range_max': sentiment_metrics['sentiment_range_max']
                    }
                    print(f"    ✅ {nft_name}: {sentiment_metrics['avg_sentiment']:.3f}")
                else:
                    print(f"    ⚠️ No sentiment for {nft_name}")
                
            except Exception as e:
                print(f"    ❌ Error analyzing {nft_name}: {e}")
            
        print(f"🧠 Analyzed {len(sale_sentiment_results)} NFT sales\n")
        return sale_sentiment_results
        
    async def save_results(self, nft_sales: List[Dict], tweets: List[Dict], sentiment_results: Dict[str, Dict] = None):
        """Save results to CSV files."""
        print("💾 Saving results...")
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        try:
            # Merge sentiment data
            enhanced_nft_sales = self._merge_sentiment_data(nft_sales, sentiment_results)
            
            # Save to CSV files
            if enhanced_nft_sales:
                features_df = pd.DataFrame(enhanced_nft_sales)
                features_df.to_csv(f"{OUTPUT_DIR}/nft_features.csv", index=False)
                
                metadata_df = pd.DataFrame(enhanced_nft_sales)
                metadata_df.to_csv(f"{OUTPUT_DIR}/nft_metadata.csv", index=False)
            
            if tweets:
                tweets_df = pd.DataFrame(tweets)
                tweets_df.to_csv(f"{OUTPUT_DIR}/raw_tweets.csv", index=False)
            
            print("✅ Results saved\n")
                    
        except Exception as e:
            print(f"❌ Error saving: {e}")
            
    def _merge_sentiment_data(self, nft_sales: List[Dict], sentiment_results: Dict[str, Dict] = None) -> List[Dict]:
        """Merge sentiment analysis results into NFT sales data."""
        if not sentiment_results:
            return nft_sales
            
        enhanced_sales = []
        for sale in nft_sales:
            # Create key matching sentiment analysis
            collection = sale.get('collection_name', 'Unknown')
            nft_name = sale.get('nft_name') or f"NFT #{sale.get('token_id', 'Unknown')}"
            sale_timestamp = sale.get('sale_timestamp', 'Unknown')
            sale_key = f"{collection}|{nft_name}|{sale_timestamp}"
            
            enhanced_sale = sale.copy()
            
            if sale_key in sentiment_results:
                sentiment_data = sentiment_results[sale_key]
                enhanced_sale.update({
                    'tweet_count': sentiment_data['tweet_count'],
                    'avg_sentiment': sentiment_data['avg_sentiment'],
                    'sentiment_confidence': sentiment_data['sentiment_confidence'],
                    'consensus_quality': sentiment_data['consensus_quality'],
                    'positive_tweets': sentiment_data['positive_tweets'],
                    'negative_tweets': sentiment_data['negative_tweets'],
                    'neutral_tweets': sentiment_data['neutral_tweets'],
                    'sentiment_range_min': sentiment_data['sentiment_range_min'],
                    'sentiment_range_max': sentiment_data['sentiment_range_max']
                })
            else:
                # Add empty sentiment data
                enhanced_sale.update({
                    'tweet_count': 0,
                    'avg_sentiment': 0.0,
                    'sentiment_confidence': 0.0,
                    'consensus_quality': 0.0,
                    'positive_tweets': 0,
                    'negative_tweets': 0,
                    'neutral_tweets': 0,
                    'sentiment_range_min': 0.0,
                    'sentiment_range_max': 0.0
                })
            
            enhanced_sales.append(enhanced_sale)
        
        return enhanced_sales
                
    async def run(self):
        """Execute the pipeline."""
        start_time = datetime.now()
        
        try:
            await self.initialize()
            
            # Collect data
            nft_sales = await self.collect_opensea_data()
            if not nft_sales:
                print("❌ No NFT sales data collected. Exiting.")
                return
                
            tweets = await self.collect_twitter_data(nft_sales)
            sentiment_results = await self.analyze_sentiment(tweets)
            await self.save_results(nft_sales, tweets, sentiment_results)
            
            # Summary
            duration = datetime.now() - start_time
            print(f"🎉 Pipeline completed in {duration}")
            print(f"📊 NFT sales: {len(nft_sales)}")
            print(f"🐦 Tweets: {len(tweets)}")
            print(f"🧠 Sentiment analyzed: {len(sentiment_results)} sales")
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            
        finally:
            if self.twitter_scraper:
                await self.twitter_scraper.close()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='NFT Data Collection Pipeline')
    parser.add_argument('--mode', choices=['test', 'full'], default='test',
                       help='Run mode (test/full)')
    
    args = parser.parse_args()
    config = RUN_MODES[args.mode].copy()
    
    print(f"🎯 Running {args.mode} mode: {config['description']}")
    print("=" * 50)
    
    pipeline = NFTPipeline(config)
    asyncio.run(pipeline.run())

if __name__ == "__main__":
    main() 