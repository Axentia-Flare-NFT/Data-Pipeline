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
        
        # Keywords for filtering relevant tweets
        self.nft_sentiment_keywords = [
            # Market sentiment
            'bullish', 'bearish', 'moon', 'dump', 'floor', 'price', 'pumping', 'dumping',
            'mooning', 'crashing', 'dipping', 'rising', 'falling', 'skyrocketing', 'plummeting',
            'rallying', 'tanking', 'soaring', 'dropping', 'surging', 'declining', 'booming',
            'correction', 'momentum', 'trend', 'volume', 'liquidity', 'volatile', 'stability',
            
            # Value assessment
            'value', 'worth', 'investment', 'potential', 'future', 'roi', 'profit', 'loss',
            'gains', 'expensive', 'cheap', 'overpriced', 'underpriced', 'bargain', 'premium',
            'overvalued', 'undervalued', 'fair price', 'market cap', 'valuation', 'priced in',
            'opportunity', 'risk', 'reward', 'upside', 'downside', 'growth', 'decline',
            
            # Project quality
            'project', 'team', 'utility', 'roadmap', 'community', 'development', 'innovation',
            'vision', 'execution', 'strategy', 'leadership', 'transparency', 'communication',
            'partnership', 'collaboration', 'ecosystem', 'adoption', 'usecase', 'application',
            'technology', 'platform', 'infrastructure', 'foundation', 'governance',
            
            # Criticism/praise
            'scam', 'rug', 'fake', 'legit', 'real', 'trash', 'gem', 'fraud', 'legitimate',
            'authentic', 'genuine', 'suspicious', 'sketchy', 'shady', 'trustworthy', 'reliable',
            'unreliable', 'questionable', 'solid', 'weak', 'strong', 'promising', 'disappointing',
            'impressive', 'underwhelming', 'outstanding', 'mediocre', 'excellent', 'terrible',
            'amazing', 'awful', 'great', 'poor', 'quality', 'worthless', 'valuable',
            
            # Art/aesthetic
            'artwork', 'design', 'aesthetic', 'beautiful', 'ugly', 'creative', 'unique',
            'generic', 'original', 'derivative', 'innovative', 'boring', 'exciting', 'stunning',
            'masterpiece', 'amateur', 'professional', 'artistic', 'style', 'theme',
            
            # Community sentiment
            'community', 'holders', 'paper hands', 'diamond hands', 'whales', 'fud',
            'fomo', 'hype', 'cope', 'hopium', 'shill', 'believers', 'doubters', 'supporters',
            'critics', 'sentiment', 'confidence', 'trust', 'distrust', 'faith', 'skepticism',
            
            # Rarity/collectible value
            'rare', 'common', 'unique', 'legendary', 'epic', 'special', 'exclusive',
            'limited', 'scarce', 'abundant', 'supply', 'demand', 'collectible', 'desirable',
            'sought after', 'prestigious', 'elite', 'premium', 'tier', 'grade',
            
            # Trading terms
            'buy', 'sell', 'hold', 'trade', 'flip', 'long term', 'short term', 'entry',
            'exit', 'position', 'accumulate', 'distribute', 'market', 'limit', 'orders',
            'resistance', 'support', 'breakout', 'breakdown', 'consolidation', 'pattern',
            
            # Emotional expressions
            'love', 'hate', 'believe', 'doubt', 'trust', 'fear', 'confident', 'worried',
            'excited', 'concerned', 'optimistic', 'pessimistic', 'bullish', 'bearish',
            'hopeful', 'skeptical', 'enthusiastic', 'cautious', 'passionate', 'indifferent'
        ]
        
        # Keywords to filter out irrelevant tweets
        self.exclude_patterns = [
            # Marketplace activities
            'just bought', 'just sold', 'just listed', 'for sale', 'minted', 'available now',
            'check out', 'look what I', 'opensea.io', 'rarible.com', 'nft.coinbase.com',
            'marketplace.', '.eth', 'bid now', 'auction ending', 'mint now', 'whitelist',
            'presale', 'public sale', 'drop today', 'dropping soon', 'available at',
            
            # Promotional content
            'follow for', 'follow back', 'follow me', 'check my', 'check our', 'link in bio',
            'link below', 'click here', 'dm me', 'dm for', 'dm to', 'message me',
            'message for', 'contact', 'join our', 'join the', 'discord.gg', 't.me/',
            
            # Trading announcements
            'floor price:', 'listing at', 'listed at', 'bought for', 'sold for',
            'price:', 'eth floor', 'current floor', 'last sale', 'last sold',
            'highest bid', 'lowest ask', 'accepting offers', 'make offer',
            
            # Collection announcements
            'new collection', 'launching soon', 'upcoming project', 'reveal today',
            'mint date', 'release date', 'announcement:', 'sneak peek', 'teaser',
            'stay tuned', 'coming soon', 'exclusive access', 'early access',
            
            # Giveaways/contests
            'giveaway', 'airdrop', 'win free', 'contest', 'raffle', 'lottery',
            'free mint', 'whitelist spot', 'chance to win', 'giving away',
            
            # Bot/spam indicators
            'dm to claim', 'dm to mint', 'dm to buy', 'dm to sell', 'dm to join',
            'auto dm', 'auto reply', 'bot for', 'generated by', 'powered by',
            
            # Generic promotions
            'dont miss', 'don\'t miss', 'limited time', 'exclusive offer',
            'special price', 'discount', 'promo', 'promotion', 'deal'
        ]
        
        print(f"✅ Simple NFT Sentiment Analyzer initialized with {self.model}")
    
    def _filter_relevant_tweets(self, tweets: List[Dict]) -> List[Dict]:
        """Filter tweets to keep only those relevant to NFT sentiment."""
        relevant_tweets = []
        seen_users = {}  # Map of user_id to tweet details for logging
        
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            user_id = tweet.get('author_id')
            username = tweet.get('username', 'unknown')
            
            # Skip if no user ID (required for uniqueness check)
            if not user_id:
                print(f"    ⚠️ Skipping tweet without user ID: {text[:50]}...")
                continue
                
            # Skip if tweet is too short
            if len(text) < 20:
                print(f"    ⚠️ Skipping short tweet from @{username}: {text}")
                continue
                
            # Skip if tweet contains exclude patterns (announcements, listings, etc.)
            if any(pattern.lower() in text for pattern in self.exclude_patterns):
                print(f"    ⚠️ Skipping promotional tweet from @{username}: {text[:50]}...")
                continue
                
            # Check if we already have a tweet from this user
            if user_id in seen_users:
                prev_tweet = seen_users[user_id]
                print(f"    ⚠️ Skipping duplicate user @{username}:")
                print(f"       Already have: {prev_tweet['text'][:50]}...")
                print(f"       Skipping: {text[:50]}...")
                continue
                
            # Check if tweet contains sentiment-related keywords
            if any(keyword.lower() in text for keyword in self.nft_sentiment_keywords):
                relevant_tweets.append(tweet)
                seen_users[user_id] = {
                    'text': text,
                    'username': username
                }
                print(f"    ✅ Keeping tweet from @{username}: {text[:50]}...")
                
        print(f"\n    📊 Tweet filtering summary:")
        print(f"       - Input tweets: {len(tweets)}")
        print(f"       - Unique users: {len(seen_users)}")
        print(f"       - Relevant tweets: {len(relevant_tweets)}")
        print(f"       - Filtered out: {len(tweets) - len(relevant_tweets)} tweets")
        
        if relevant_tweets:
            print("\n    👥 Selected tweets by user:")
            for tweet in relevant_tweets:
                username = tweet.get('username', 'unknown')
                text = tweet.get('text', '')[:50]
                print(f"       @{username}: {text}...")
                
        return relevant_tweets

    async def analyze_tweets_sentiment(self, tweets: List[Dict]) -> Dict:
        """
        Analyze sentiment of tweets using Claude 3 Haiku.
        Returns the same format as the consensus-based analyzer for compatibility.
        """
        if not tweets:
            return self._empty_sentiment_result()
            
        print("\n🔍 Starting tweet filtering and sentiment analysis...")
        
        # Filter tweets for relevance and uniqueness
        filtered_tweets = self._filter_relevant_tweets(tweets)
        
        if not filtered_tweets:
            print("⚠️ No relevant tweets found after filtering")
            return self._empty_sentiment_result()
            
        # Extract tweet texts
        tweet_texts = []
        for tweet in filtered_tweets:
            tweet_text = tweet.get('text', '').strip()
            if tweet_text:
                tweet_texts.append(tweet_text)
                
        if not tweet_texts:
            return self._empty_sentiment_result()
        
        print(f"\n🚀 Analyzing sentiment for {len(tweet_texts)} filtered tweets from {len(set(t.get('author_id') for t in filtered_tweets))} unique users...")
        
        try:
            # Create conversation with filtered tweets
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
                'unique_users': len(set(t.get('author_id') for t in filtered_tweets)),
                'consensus_model_count': 1,  # Single model
                'consensus_iterations': 1,   # Single pass
                'combined_analysis': True
            }
            
            print(f"\n✅ Analysis complete:")
            print(f"   - Sentiment score: {result['avg_sentiment']:.3f}")
            print(f"   - Confidence: {result['sentiment_confidence']:.3f}")
            print(f"   - Unique users: {result['unique_users']}")
            print(f"   - Tweet breakdown: {positive_tweets} positive, {negative_tweets} negative, {neutral_tweets} neutral")
            
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
            "sentiment": "neutral"
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
        """Parse sentiment score and confidence from Claude's response."""
        try:
            # Clean the response text - remove any markdown code blocks
            cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parse the JSON response
            response_data = json.loads(cleaned_text)
            
            # Get overall sentiment score
            sentiment_score = float(response_data.get('overall_sentiment', '0.0'))
            
            # Calculate confidence based on tweet agreement
            tweet_sentiments = [t.get('sentiment', 'neutral') for t in response_data.get('tweets', [])]
            if not tweet_sentiments:
                return 0.0, 0.5
                
            # Count agreement with overall sentiment
            agreement_count = 0
            for sentiment in tweet_sentiments:
                if sentiment == 'positive' and sentiment_score > 0:
                    agreement_count += 1
                elif sentiment == 'negative' and sentiment_score < 0:
                    agreement_count += 1
                elif sentiment == 'neutral' and abs(sentiment_score) < 0.2:
                    agreement_count += 1
                    
            confidence = (agreement_count / len(tweet_sentiments)) if tweet_sentiments else 0.5
            
            return sentiment_score, confidence
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"    ❌ Error parsing sentiment: {e}")
            return 0.0, 0.5
    
    def _categorize_tweets_by_keywords(self, tweet_texts: List[str], response_text: str = None) -> tuple[int, int, int]:
        """Categorize tweets as positive, negative, or neutral based on the model's response."""
        try:
            if not response_text:
                return self._fallback_categorize_tweets(tweet_texts)
                
            # Clean the response text - remove any markdown code blocks
            cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parse the JSON response
            response_data = json.loads(cleaned_text)
            
            # Count sentiments from the model's analysis
            positive = 0
            negative = 0
            neutral = 0
            
            for tweet in response_data.get('tweets', []):
                sentiment = tweet.get('sentiment', 'neutral').lower()
                if sentiment == 'positive':
                    positive += 1
                elif sentiment == 'negative':
                    negative += 1
                else:
                    neutral += 1
                    
            return positive, negative, neutral
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"    ❌ Error categorizing tweets: {e}")
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
            'unique_users': 0,
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
