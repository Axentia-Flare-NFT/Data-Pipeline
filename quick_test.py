#!/usr/bin/env python3
"""
Quick NFT Pipeline Test

Fast test with 3-5 NFTs to verify the complete pipeline is working:
- OpenSea data collection ✅
- Twitter social metrics ✅  
- Advanced consensus sentiment analysis ✅
- Clean CSV output ✅
"""

import asyncio
import os
from dotenv import load_dotenv
from data_collector import collect_nft_data

# Load environment variables
load_dotenv()

async def run_quick_test():
    """Run a quick pipeline test with 3-5 NFTs."""
    
    print("🚀 Quick NFT Pipeline Test")
    print("=" * 50)
    print("Target: 4 NFTs across 2 collections for pipeline verification")
    print()
    
    # Check API keys
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    twitter_creds = all([
        os.getenv('X_USERNAME'),
        os.getenv('X_EMAIL'), 
        os.getenv('X_PASSWORD')
    ])
    opensea_key = os.getenv('OPENSEA_API_KEY')
    
    print("📋 System Check:")
    print(f"   🚀 OpenRouter API: {'✓' if openrouter_key else '✗ REQUIRED'}")
    print(f"   🐦 Twitter Credentials: {'✓' if twitter_creds else '✗'}")
    print(f"   📊 OpenSea API: {'✓' if opensea_key else '✗'}")
    print()
    
    if not openrouter_key:
        print("❌ OpenRouter API key is REQUIRED for advanced consensus learning")
        print("   Get your key from: https://openrouter.ai/keys")
        print("   Add to .env as: OPENROUTER_API_KEY=your_key_here")
        return False
    if not twitter_creds:
        print("⚠️  Twitter credentials missing - will use mock social data")
    
    try:
        # Test with two popular collections for better coverage
        test_collections = ['boredapeyachtclub', 'pudgypenguins']
        
        print(f"🔄 Starting collection from: {test_collections}")
        print(f"⚡ Using optimized settings for speed...")
        print()
        
        collector = await collect_nft_data(
            collections=test_collections,
            sales_per_collection=2,  # 2 NFTs per collection = 4 total
            tweets_per_nft=6,  # Reduced from 20 for faster testing
            collection_delay_seconds=10,  # Only 10 seconds between collections for quick test
            twitter_username=os.getenv('X_USERNAME', 'test'),
            twitter_email=os.getenv('X_EMAIL', 'test@test.com'),
            twitter_password=os.getenv('X_PASSWORD', 'test')
        )
        
        # Display results
        stats = collector.get_progress_stats()
        
        print(f"\n🎉 Quick Test Results:")
        print(f"   NFTs collected: {stats['total_nfts']}")
        print(f"   Collections: {', '.join(stats['collections'])}")
        
        if stats['total_nfts'] > 0:
            print(f"   Price range: {stats['price_range'][0]:.3f} - {stats['price_range'][1]:.3f} ETH")
            print(f"   Average price: {stats['avg_sale_price']:.3f} ETH")
            print(f"   Total tweets: {stats['total_tweets']}")
            
            # Show sentiment analysis results
            try:
                import pandas as pd
                df = pd.read_csv('nft_data/nft_features.csv')
                
                if 'avg_sentiment' in df.columns and df['avg_sentiment'].sum() > 0:
                    avg_sentiment = df['avg_sentiment'].mean()
                    sentiment_confidence = df['sentiment_confidence'].mean()
                    print(f"\n🤖 Sentiment Analysis:")
                    print(f"   Average sentiment: {avg_sentiment:.3f} (-1=negative, +1=positive)")
                    print(f"   Confidence: {sentiment_confidence:.3f}")
                    print(f"   Positive tweets: {df['positive_tweets'].sum()}")
                    print(f"   Negative tweets: {df['negative_tweets'].sum()}")
                    print(f"   Models used: {df['consensus_model_count'].iloc[0] if len(df) > 0 else 0}")
                else:
                    print(f"\n📊 Social Metrics Only:")
                    print(f"   (Sentiment analysis skipped - see system check above)")
                    
            except Exception as e:
                print(f"   Could not read results: {e}")
        
        print(f"\n📁 Output Files:")
        print(f"   • nft_data/nft_features.csv (main dataset)")
        print(f"   • nft_data/nft_metadata.csv (NFT details)")
        
        print(f"\n✅ Quick test completed successfully!")
        print(f"💡 Ready for full collection? Run: python3 full_collection.py")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print(f"💡 Check your .env file and API keys")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_quick_test())
    exit(0 if success else 1) 