#!/usr/bin/env python3
"""
Simple NFT Sentiment Analyzer using OpenRouter

Uses a single fast model (Claude 3 Haiku) for efficient sentiment analysis.
Maintains the same output format as the consensus-based analyzer for compatibility.
"""

import asyncio
import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import httpx
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Replaced BS consenus learning with a single model with justification, this is all we need
class SimpleNFTSentimentAnalyzer:
    """Simple sentiment analyzer using OpenRouter and Claude 3 Haiku."""
    
    def __init__(self, openrouter_api_key: str = None):
        self.openrouter_api_key = openrouter_api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY required")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "google/gemini-2.0-flash-001"
        self.client = httpx.AsyncClient(timeout=30.0)
        print(f"✅ Simple NFT Sentiment Analyzer initialized with {self.model}")
    
    async def analyze_tweets_sentiment(self, tweets: List[Dict]) -> Dict:
        """
        Analyze sentiment of tweets using Claude 3 Haiku.
        Returns the same format as the consensus-based analyzer for compatibility.
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
        
        print(f"🚀 Analyzing sentiment for {len(tweet_texts)} tweets...")
        
        try:
            # Create conversation with all tweets combined
            conversation = self._build_sentiment_conversation(tweet_texts)
            
            # Get sentiment from Claude
            response_text = await self._get_sentiment_from_claude(conversation)
            sentiment_score, confidence = self._parse_sentiment_from_response(response_text)
            
            # Calculate tweet distribution using the same response
            positive_tweets, negative_tweets, neutral_tweets = self._categorize_tweets_by_keywords(
                tweet_texts, 
                response_text
            )
            
            result = {
                'avg_sentiment': sentiment_score,
                'sentiment_std': 0.0,
                'sentiment_confidence': confidence,
                'consensus_quality': 0.9,  # Maintain same format
                'positive_tweets': positive_tweets,
                'negative_tweets': negative_tweets,
                'neutral_tweets': neutral_tweets,
                'sentiment_range_min': sentiment_score,
                'sentiment_range_max': sentiment_score,
                'analyzed_tweet_count': len(tweet_texts),
                'consensus_model_count': 1,  # Single model
                'consensus_iterations': 1,   # Single pass
                'combined_analysis': True
            }
            
            print(f"✅ Analysis complete: sentiment={result['avg_sentiment']:.3f}, confidence={result['sentiment_confidence']:.3f}")
            print(f"   📊 Tweet breakdown: {positive_tweets} positive, {negative_tweets} negative, {neutral_tweets} neutral")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Error in sentiment analysis: {e}")
            return self._empty_sentiment_result()
    
    def _build_sentiment_conversation(self, tweet_texts: List[str]) -> List[Dict]:
        """Build conversation for sentiment analysis."""
        
        # Combine all tweets
        combined_tweets = "\n".join([f"Tweet {i+1}: {text}" for i, text in enumerate(tweet_texts)])
        print("Combined Tweets: ", combined_tweets)
        # Truncate if too long
        max_length = 20000
        if len(combined_tweets) > max_length:
            combined_tweets = combined_tweets[:max_length] + "... [truncated]"
        
        return [
            {
                "role": "system",
                "content": """You are an expert NFT and crypto sentiment analyzer. Analyze all of the tweets below individually, and then as a collective sentiment about a specific NFT sale. You should also include a short justification for your overall sentiment score, referring to specific tweets and trends you notice. 

Format your output in JSON format. For each tweet, output "positive", "negative", or "neutral" for the sentiment of the tweet. 

Consider the OVERALL sentiment across all tweets together. Look for patterns, consensus, and dominant themes. Your output should be a JSON object with the following format:
{
    "tweets": [
        {
            "tweet_index": 1,
            "sentiment": "positive"
        },
        {
            "tweet_index": 2,
            "sentiment": "neural"
        },
        ...
    ],
    "overall_sentiment": "1.0",
    "justification": "The overall sentiment is positive because the tweets are overwhelmingly positive and bullish. Although tweet 2 suggests..."
}

For the overall sentiment, output a score between -1.0 and 1.0. 
Output format: SENTIMENT_SCORE: X.X (where X.X is between -1.0 and +1.0)
-1.0 = very negative overall sentiment
-0.5 = negative overall sentiment  
0.0 = neutral overall sentiment
+0.5 = positive overall sentiment
+1.0 = very positive overall sentiment

You are allowed to interploate between the above values.

Instructions
- Examples of some positive indicators: moon, diamond hands, HODL, LFG, pump, bullish, buy, strong, good investment, and general positive comments about the NFT
- Examples of some negative indicators: rug pull, paper hands, dump, FUD, crash, bearish, sell, weak, overpriced, and other negative comments about the NFT
- Never include ''' or ``` json in your output. Simply output the JSON.

"""
            },
            {
                "role": "user",
                "content": f"""Output an indvidual sentiment and overall sentiment score for the following {len(tweet_texts)} tweets about an NFT sale in JSON format:

{combined_tweets}

For the collective sentiment consider the dominant themes and overall tone."""
            }
        ]
    
    async def _get_sentiment_from_claude(self, conversation: List[Dict]) -> str:
        """Get sentiment score from Claude 3 Haiku."""
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "HTTP-Referer": "https://github.com/your-repo",  # Required by OpenRouter
                    "X-Title": "NFT Sentiment Analyzer"  # Optional but helpful
                },
                json={
                    "model": self.model,
                    "messages": conversation,
                    "temperature": 0.3,
                    "max_tokens": 5000
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the response text
            response_text = result['choices'][0]['message']['content']
            print("Response: ", response_text)
            
            return response_text
            
        except Exception as e:
            print(f"    ❌ Error getting sentiment from Claude: {e}")
            return ""
    
    def _parse_sentiment_from_response(self, response_text: str) -> tuple[float, float]:
        """Parse sentiment score from Claude's response."""
        try:
            # Clean the response text - remove any markdown code blocks
            cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parse the JSON response
            response_json = json.loads(cleaned_text)
            
            # Get the overall sentiment score
            sentiment_score = float(response_json.get('overall_sentiment', 0.0))
            
            confidence = 0.9  # Default confidence
            
            return sentiment_score, confidence
            
        except json.JSONDecodeError as e:
            print(f"    ❌ Error parsing JSON response: {e}")
            return self._fallback_sentiment_analysis(response_text)
        except Exception as e:
            print(f"    ❌ Error parsing sentiment: {e}")
            return self._fallback_sentiment_analysis(response_text)
    
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
    
    def _categorize_tweets_by_keywords(self, tweet_texts: List[str], response_text: str = None) -> tuple[int, int, int]:
        """Categorize tweets by sentiment from the LLM response."""
        try:
            if not response_text:
                return self._fallback_categorize_tweets(tweet_texts)
            
            # Clean the response text - remove any markdown code blocks
            cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parse the JSON response
            response_json = json.loads(cleaned_text)
            
            # Count sentiments from the LLM analysis
            sentiment_counts = {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }
            
            for tweet in response_json.get('tweets', []):
                sentiment = tweet.get('sentiment', '').lower()
                if sentiment in sentiment_counts:
                    sentiment_counts[sentiment] += 1
            
            return (
                sentiment_counts['positive'],
                sentiment_counts['negative'],
                sentiment_counts['neutral']
            )
            
        except Exception as e:
            print(f"    ❌ Error categorizing tweets: {e}")
            # Fallback to keyword-based categorization
            return self._fallback_categorize_tweets(tweet_texts)
    
    def _fallback_categorize_tweets(self, tweet_texts: List[str]) -> tuple[int, int, int]:
        """Fallback method to categorize tweets using keywords."""
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
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Test function
async def test_simple_sentiment_analyzer():
    """Test the sentiment analyzer."""
    
    print("🧪 Testing Simple NFT Sentiment Analyzer")
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
        },
        {
            'text': 'This NFT fucking sucks, it is bad and overpriced',
            'user_id': 'test3'
        },
        {
            'text': 'This is the best thing Ive ever seen',
            'user_id': 'test4'
        },
        {
            'text': 'I will die before spending money on ts',
            'user_id': 'test5'
        }
    ]
    
    try:
        if not os.getenv('OPENROUTER_API_KEY'):
            print("❌ OPENROUTER_API_KEY required")
            return False
        
        analyzer = SimpleNFTSentimentAnalyzer()
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
    asyncio.run(test_simple_sentiment_analyzer()) 