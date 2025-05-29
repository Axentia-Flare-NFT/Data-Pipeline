#!/usr/bin/env python3
"""
Full NFT Data Collection Pipeline

Production-grade collection script for large-scale NFT datasets.
Designed to collect 1000+ NFTs with:
- Advanced consensus sentiment analysis
- Robust error handling and recovery  
- Progress tracking and checkpoints
- Batch processing for efficiency
- Rate limiting compliance
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from data_collector import collect_nft_data

# Load environment variables
load_dotenv()

# Popular NFT collections for comprehensive data collection
POPULAR_COLLECTIONS = [
    'boredapeyachtclub',
    'mutant-ape-yacht-club', 
    'otherdeed',
    'cryptopunks',
    'pudgypenguins',
    'doodles-official',
    'azuki',
    'clonex',
    'proof-moonbirds',
    'veefriends',
    'meebits',
    'world-of-women-nft',
    'cyberkongz',
    'cool-cats-nft',
    'loot',
    'artblocks',
    'chromie-squiggle-by-snowfro',
    'fidenza-by-tyler-hobbs',
    'ringers-by-dmitri-cherniak',
    'autoglyphs'
]

async def run_full_collection():
    """Run full-scale NFT data collection."""
    
    print("🚀 Full NFT Data Collection Pipeline")
    print("=" * 60)
    print("Target: 1000+ NFTs with comprehensive sentiment analysis")
    print(f"Collections: {len(POPULAR_COLLECTIONS)} major NFT projects")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Comprehensive system check
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    twitter_creds = all([
        os.getenv('X_USERNAME'),
        os.getenv('X_EMAIL'), 
        os.getenv('X_PASSWORD')
    ])
    opensea_key = os.getenv('OPENSEA_API_KEY')
    
    print("📋 System Requirements Check:")
    print(f"   OpenRouter API: {'✅ Ready' if openrouter_key else '❌ Missing'}")
    print(f"   Twitter Access: {'✅ Ready' if twitter_creds else '❌ Missing'}")
    print(f"   OpenSea API: {'✅ Ready' if opensea_key else '❌ Missing'}")
    print()
    
    # Validate required credentials
    if not openrouter_key:
        print("❌ OPENROUTER_API_KEY required for sentiment analysis")
        print("   Get your key from: https://openrouter.ai/keys")
        return False
    
    if not twitter_creds:
        print("❌ Twitter credentials required for social metrics")
        print("   Set X_USERNAME, X_EMAIL, X_PASSWORD in .env")
        return False
    
    if not opensea_key:
        print("❌ OPENSEA_API_KEY recommended for reliable data")
        print("   Get your key from: https://opensea.io/account/settings")
        print("   Continuing without API key (rate limited)...")
    
    # Configuration
    nfts_per_collection = 50  # 50 NFTs × 20 collections = 1000 NFTs
    estimated_time_hours = (len(POPULAR_COLLECTIONS) * nfts_per_collection * 10) / 3600  # ~10 seconds per NFT
    
    print(f"📊 Collection Configuration:")
    print(f"   Collections: {len(POPULAR_COLLECTIONS)}")
    print(f"   NFTs per collection: {nfts_per_collection}")
    print(f"   Total target NFTs: {len(POPULAR_COLLECTIONS) * nfts_per_collection}")
    print(f"   Estimated time: {estimated_time_hours:.1f} hours")
    print(f"   Rate limiting: 8s per NFT, 3min per collection")
    print()
    
    # Confirm before starting
    try:
        response = input("🤔 This is a large collection. Continue? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Collection cancelled.")
            return False
    except KeyboardInterrupt:
        print("\nCollection cancelled.")
        return False
    
    print(f"\n🎯 Starting full collection...")
    print(f"⚡ Using advanced Flare AI consensus learning")
    print(f"💾 Data will be saved to: nft_data/")
    print()
    
    try:
        # Run the collection
        collector = await collect_nft_data(
            collections=POPULAR_COLLECTIONS,
            sales_per_collection=nfts_per_collection,
            tweets_per_nft=20,  # Full analysis for production dataset
            collection_delay_seconds=180,  # Full 3-minute delay for production rate limiting
            twitter_username=os.getenv('X_USERNAME'),
            twitter_email=os.getenv('X_EMAIL'),
            twitter_password=os.getenv('X_PASSWORD'),
            opensea_api_key=opensea_key
        )
        
        # Final results
        stats = collector.get_progress_stats()
        end_time = datetime.now()
        
        print(f"\n🎉 Collection Complete!")
        print(f"   Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Total NFTs: {stats['total_nfts']}")
        print(f"   Collections: {len(stats['collections'])}")
        print(f"   Price range: {stats['price_range'][0]:.3f} - {stats['price_range'][1]:.3f} ETH")
        print(f"   Average price: {stats['avg_sale_price']:.3f} ETH")
        print(f"   Total tweets: {stats['total_tweets']}")
        
        # Sentiment analysis summary
        try:
            import pandas as pd
            df = pd.read_csv('nft_data/nft_features.csv')
            
            print(f"\n🤖 Sentiment Analysis Summary:")
            print(f"   Average sentiment: {df['avg_sentiment'].mean():.3f}")
            print(f"   Sentiment std: {df['sentiment_std'].mean():.3f}")
            print(f"   Confidence: {df['sentiment_confidence'].mean():.3f}")
            print(f"   Total positive tweets: {df['positive_tweets'].sum()}")
            print(f"   Total negative tweets: {df['negative_tweets'].sum()}")
            print(f"   Total neutral tweets: {df['neutral_tweets'].sum()}")
            print(f"   Models used: {df['consensus_model_count'].iloc[0] if len(df) > 0 else 0}")
            
        except Exception as e:
            print(f"   Could not read sentiment summary: {e}")
        
        print(f"\n📁 Output Files:")
        print(f"   • nft_data/nft_features.csv ({stats['total_nfts']} NFTs with sentiment & hype)")
        print(f"   • nft_data/nft_metadata.csv (NFT details and timestamps)")
        print(f"   • nft_data/raw_tweets.csv (individual tweet data)")
        
        print(f"\n📈 Dataset Ready for ML Training!")
        print(f"   Features: Price, sentiment, social metrics, engagement")
        print(f"   Use cases: Price prediction, hype analysis, market sentiment")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Collection interrupted by user")
        print(f"💾 Partial data saved to nft_data/")
        return False
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")
        print(f"💡 Check logs and try running quick_test.py first")
        return False

def show_usage():
    """Show usage information."""
    print("NFT Data Collection Pipeline")
    print("=" * 30)
    print()
    print("Quick test (3-5 NFTs):")
    print("  python3 quick_test.py")
    print()
    print("Full collection (1000+ NFTs):")
    print("  python3 full_collection.py")
    print()
    print("Requirements:")
    print("  • OPENROUTER_API_KEY (for sentiment analysis)")
    print("  • X_USERNAME, X_EMAIL, X_PASSWORD (for social metrics)")
    print("  • OPENSEA_API_KEY (optional, for higher rate limits)")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_usage()
        sys.exit(0)
    
    success = asyncio.run(run_full_collection())
    sys.exit(0 if success else 1) 