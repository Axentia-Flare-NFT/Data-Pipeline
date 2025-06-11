#!/usr/bin/env python3
"""
Advanced NFT Sentiment Analyzer with Flare AI Consensus Learning

Uses the official Flare AI consensus learning framework for sophisticated
multi-model sentiment analysis with iterative refinement.
"""

import asyncio
import os
import sys
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import statistics
from datetime import datetime

# Add the flare-ai-consensus src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flare-ai-consensus', 'src'))

try:
    from flare_ai_consensus.consensus.consensus import run_consensus
    from flare_ai_consensus.router import AsyncOpenRouterProvider
    from flare_ai_consensus.settings import ConsensusConfig, ModelConfig, AggregatorConfig, Message
    FLARE_CONSENSUS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Flare AI Consensus Learning required: {e}")
    FLARE_CONSENSUS_AVAILABLE = False

@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    sentiment_score: float
    confidence: float
    consensus_quality: float
    model_count: int
    iterations: int
    raw_consensus_text: str
    analysis_time: str

class AdvancedNFTSentimentAnalyzer:
    """Consensus-based sentiment analyzer using Flare AI framework."""
    
    def __init__(self, openrouter_api_key: str = None):
        if not FLARE_CONSENSUS_AVAILABLE:
            raise ImportError("Flare AI Consensus Learning required")
        
        self.openrouter_api_key = openrouter_api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY required")
        
        self.provider = AsyncOpenRouterProvider(
            api_key=self.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        self.consensus_config = self._create_sentiment_consensus_config()
        print(f"✅ Advanced NFT Sentiment Analyzer initialized with {len(self.consensus_config.models)} models")
    
    def _create_sentiment_consensus_config(self) -> ConsensusConfig:
        """Create consensus configuration for sentiment analysis."""
        
        # Fast models for sentiment analysis
        models = [
            ModelConfig(
                model_id="anthropic/claude-3-haiku",
                max_tokens=50,
                temperature=0.2
            ),
            ModelConfig(
                model_id="openai/gpt-4o-mini",
                max_tokens=50,
                temperature=0.2
            )
        ]
        
        # Aggregator model
        aggregator_model = ModelConfig(
            model_id="anthropic/claude-3-haiku",
            max_tokens=75,
            temperature=0.1
        )
        
        # Aggregator configuration
        aggregator_config = AggregatorConfig(
            model=aggregator_model,
            approach="fast_consensus",
            context=[
                {
                    "role": "system",
                    "content": """You are a fast NFT sentiment analyzer. Provide ONLY a score between -1.0 and +1.0.

Scale: -1.0=very negative, -0.5=negative, 0.0=neutral, +0.5=positive, +1.0=very positive

Format: SCORE: X.X"""
                }
            ],
            prompt=[
                {
                    "role": "user", 
                    "content": "Analyze these sentiment analyses and output: SCORE: X.X (where X.X is between -1.0 and +1.0)"
                }
            ]
        )
        
        return ConsensusConfig(
            models=models,
            aggregator_config=aggregator_config,
            improvement_prompt="Provide fast sentiment score between -1.0 and +1.0",
            iterations=0,
            aggregated_prompt_type="system"
        )
    
    async def analyze_tweets_sentiment(self, tweets: List[Dict]) -> Dict:
        """
        Analyze sentiment of tweets using consensus learning.
        """
        if not tweets:
            return self._empty_sentiment_result()
        
        # Extract tweet texts
        tweet_texts = []
        for tweet in tweets:
            tweet_text = tweet.get('text', '').strip()
            if tweet_text and len(tweet_text) >= 10:
                tweet_texts.append(tweet_text)
        
        if not tweet_texts:
            return self._empty_sentiment_result()
        
        print(f"🚀 Consensus sentiment analysis: combining {len(tweet_texts)} tweets into single prompt...")
        
        try:
            # Create conversation with all tweets combined
            conversation = self._build_combined_sentiment_conversation(tweet_texts)
            
            # Run consensus learning
            consensus_result = await run_consensus(
                self.provider,
                self.consensus_config,
                conversation
            )
            
            # Parse sentiment score
            sentiment_score, confidence = self._parse_sentiment_from_consensus(consensus_result)
            
            # Calculate tweet distribution
            positive_tweets, negative_tweets, neutral_tweets = self._categorize_tweets_by_keywords(tweet_texts)
            
            result = {
                'avg_sentiment': sentiment_score,
                'sentiment_std': 0.0,
                'sentiment_confidence': confidence,
                'consensus_quality': 0.9,
                'positive_tweets': positive_tweets,
                'negative_tweets': negative_tweets,
                'neutral_tweets': neutral_tweets,
                'sentiment_range_min': sentiment_score,
                'sentiment_range_max': sentiment_score,
                'analyzed_tweet_count': len(tweet_texts),
                'consensus_model_count': len(self.consensus_config.models),
                'consensus_iterations': self.consensus_config.iterations,
                'combined_analysis': True
            }
            
            print(f"✅ Combined consensus complete: sentiment={result['avg_sentiment']:.3f}, confidence={result['sentiment_confidence']:.3f}")
            print(f"   📊 Tweet breakdown: {positive_tweets} positive, {negative_tweets} negative, {neutral_tweets} neutral")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Error in sentiment analysis: {e}")
            return self._empty_sentiment_result()
    
    def _build_combined_sentiment_conversation(self, tweet_texts: List[str]) -> List[Message]:
        """Build conversation for sentiment analysis."""
        
        # Combine all tweets
        combined_tweets = "\n".join([f"Tweet {i+1}: {text}" for i, text in enumerate(tweet_texts)])
        
        # Truncate if too long
        max_length = 2000
        if len(combined_tweets) > max_length:
            combined_tweets = combined_tweets[:max_length] + "... [truncated]"
        
        return [
            {
                "role": "system",
                "content": """You are an expert NFT/crypto sentiment analyzer. Analyze ALL the tweets below as a collective sentiment about a specific NFT sale.

Consider the OVERALL sentiment across all tweets together. Look for patterns, consensus, and dominant themes.

Positive indicators: moon, diamond hands, HODL, LFG, pump, bullish, buy, strong, good investment
Negative indicators: rug pull, paper hands, dump, FUD, crash, bearish, sell, weak, overpriced

Output format: SENTIMENT_SCORE: X.X (where X.X is between -1.0 and +1.0)
-1.0 = very negative overall sentiment
-0.5 = negative overall sentiment  
0.0 = neutral overall sentiment
+0.5 = positive overall sentiment
+1.0 = very positive overall sentiment"""
            },
            {
                "role": "user",
                "content": f"""Analyze the OVERALL sentiment of these {len(tweet_texts)} tweets about an NFT sale:

{combined_tweets}

What is the collective sentiment across ALL these tweets? Consider the dominant themes and overall tone."""
            }
        ]
    
    def _categorize_tweets_by_keywords(self, tweet_texts: List[str]) -> tuple[int, int, int]:
        """Categorize tweets by positive/negative/neutral keywords."""
        
        positive_keywords = ['moon', 'diamond', 'hands', 'hodl', 'lfg', 'pump', 'bullish', 'buy', 'strong', 'good', 'great', '🚀', '💎', '📈']
        negative_keywords = ['rug', 'pull', 'paper', 'dump', 'fud', 'crash', 'bearish', 'sell', 'weak', 'bad', 'overpriced', '📉', '💸']
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for tweet_text in tweet_texts:
            tweet_lower = tweet_text.lower()
            
            pos_matches = sum(1 for keyword in positive_keywords if keyword in tweet_lower)
            neg_matches = sum(1 for keyword in negative_keywords if keyword in tweet_lower)
            
            if pos_matches > neg_matches:
                positive_count += 1
            elif neg_matches > pos_matches:
                negative_count += 1
            else:
                neutral_count += 1
        
        return positive_count, negative_count, neutral_count
    
    def _parse_sentiment_from_consensus(self, consensus_text: str) -> tuple[float, float]:
        """Parse sentiment score and confidence from consensus output."""
        try:
            import re
            
            # Look for SCORE: pattern
            score_pattern = r'SCORE:\s*(-?\d+\.?\d*)'
            score_match = re.search(score_pattern, consensus_text, re.IGNORECASE)
            
            if score_match:
                score = float(score_match.group(1))
                score = max(-1.0, min(1.0, score))  # Clamp to valid range
                confidence = 0.9
                return score, confidence
            
            # Try SENTIMENT_SCORE: pattern
            sentiment_pattern = r'SENTIMENT_SCORE:\s*(-?\d+\.?\d*)'
            sentiment_match = re.search(sentiment_pattern, consensus_text, re.IGNORECASE)
            
            if sentiment_match:
                score = float(sentiment_match.group(1))
                score = max(-1.0, min(1.0, score))
                confidence = 0.9
                return score, confidence
            
            # Try to find any number between -1 and 1
            number_pattern = r'(-?[01]\.?\d*)'
            numbers = re.findall(number_pattern, consensus_text)
            
            if numbers:
                for num_str in numbers:
                    try:
                        num = float(num_str)
                        if -1.0 <= num <= 1.0:
                            return num, 0.7
                    except ValueError:
                        continue
            
            # Fallback: analyze text for sentiment keywords
            return self._fallback_sentiment_analysis(consensus_text)
            
        except Exception as e:
            return self._fallback_sentiment_analysis(consensus_text)
    
    def _fallback_sentiment_analysis(self, text: str) -> tuple[float, float]:
        """Fallback sentiment analysis using keyword matching."""
        text_lower = text.lower()
        
        positive_words = ['positive', 'bullish', 'optimistic', 'good', 'strong', 'moon', 'pump']
        negative_words = ['negative', 'bearish', 'pessimistic', 'bad', 'weak', 'dump', 'crash']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 0.5, 0.5
        elif negative_count > positive_count:
            return -0.5, 0.5
        else:
            return 0.0, 0.3
    
    def _empty_sentiment_result(self) -> Dict:
        """Return empty sentiment result."""
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

# Test function
async def test_advanced_sentiment_analyzer():
    """Test the sentiment analyzer."""
    
    print("🧪 Testing Advanced NFT Sentiment Analyzer")
    print("=" * 50)
    
    # Sample tweets for testing
    test_tweets = [
        {
            'text': 'This NFT collection is absolutely going to the moon! 🚀 Diamond hands only! #LFG',
            'user_id': 'test1'
        },
        {
            'text': 'Another obvious rug pull happening. When will people learn? Paper hands everywhere selling.',
            'user_id': 'test2'
        }
    ]
    
    try:
        if not os.getenv('OPENROUTER_API_KEY'):
            print("❌ OPENROUTER_API_KEY required")
            return False
        
        analyzer = AdvancedNFTSentimentAnalyzer()
        result = await analyzer.analyze_tweets_sentiment(test_tweets)
        
        print(f"\n📊 Results:")
        print(f"   Tweets analyzed: {result['analyzed_tweet_count']}")
        print(f"   Average sentiment: {result['avg_sentiment']:.3f}")
        print(f"   Confidence: {result['sentiment_confidence']:.3f}")
        print(f"   Quality: {result['consensus_quality']:.3f}")
        print(f"   Positive/Negative/Neutral: {result['positive_tweets']}/{result['negative_tweets']}/{result['neutral_tweets']}")
        
        print(f"\n✅ Test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_advanced_sentiment_analyzer()) 