# NFT Data Collection Pipeline

A streamlined NFT data collection and sentiment analysis pipeline that combines OpenSea market data, Twitter social metrics, and AI-powered sentiment analysis for machine learning training.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Set Environment Variables
Create a `.env` file with your API keys:
```bash
OPENSEA_API_KEY=your_opensea_api_key_here
APIFY_API_KEY=your_apify_api_key_here  
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3. Run the Pipeline

**Quick Test (3 NFTs, 5 tweets each):**
```bash
python3 run_pipeline.py --mode test
```

**Full Production Run (1000 NFTs, 15 tweets each):**
```bash  
python3 run_pipeline.py --mode full
```

## 📊 What It Does

This pipeline automatically:

1. **Collects NFT sales data** from OpenSea API (historical 2019-2022 data for better Twitter correlation)
2. **Scrapes relevant tweets** from the 24 hours before each NFT sale using Apify
3. **Analyzes sentiment** using Flare AI Consensus Learning (multi-model agreement)
4. **Exports CSV files** with combined market + sentiment data for ML training

## 🏗️ Pipeline Architecture

### Data Flow
```
OpenSea Sales → Twitter Search → Sentiment Analysis → CSV Export
     ↓              ↓                    ↓              ↓
   Market Data   Social Metrics    AI Consensus     ML Training
```

### Components
- **`run_pipeline.py`** - Main orchestrator
- **`opensea_collector.py`** - OpenSea API integration  
- **`twitter_scraper_apify.py`** - Apify Twitter scraping
- **`sentiment_analyzer_advanced.py`** - Flare AI consensus analysis

## 📄 Output Files

Generated in `nft_data/` directory:

- **`nft_features.csv`** - NFT sales with sentiment features for ML training
- **`nft_metadata.csv`** - Detailed NFT and market metadata  
- **`raw_tweets.csv`** - Raw tweet data with timestamps and sentiment scores

### Sample Output
```csv
collection_name,nft_name,sale_price_eth,tweet_count,avg_sentiment,consensus_quality
Boredapeyachtclub,NFT #5172,71.0,5,0.6,0.9
Pudgypenguins,Pudgy Penguin #1987,5.9,5,0.6,0.9
```

## ⚙️ Configuration

### Test Mode (Default)
- **3 NFT sales** from Bored Ape Yacht Club and Pudgy Penguins
- **5 tweets per NFT** from 24 hours before sale
- **Historical data** (2019-2022) for better Twitter correlation
- **~2 minutes runtime**

### Full Mode  
- **1000 NFT sales** from 6 major collections
- **15 tweets per NFT** from 24 hours before sale
- **Historical data** (2019-2022)
- **~2-3 hours runtime**

To modify collections or parameters, edit the `RUN_MODES` configuration in `run_pipeline.py`.

## 🎯 Use Cases

### Machine Learning Training
- **Price prediction models** with social sentiment features
- **Market timing algorithms** using Twitter signals
- **Sentiment classification** for crypto/NFT content

### Research & Analysis
- **Academic research** on social sentiment impact on NFT pricing
- **Market analysis** of Twitter buzz vs. sales correlation
- **Trend identification** for emerging NFT collections

## 💰 API Costs

- **OpenSea**: Free tier (rate limited)
- **Apify**: ~$0.02-0.05 per tweet search
- **OpenRouter**: ~$0.001-0.01 per sentiment analysis

**Estimated costs:**
- Test mode: ~$0.50-1.00
- Full mode: ~$50-100

## 🔧 API Setup

### OpenSea API
1. Sign up at [OpenSea Developer Portal](https://docs.opensea.io/reference/api-overview)
2. Get your API key (free tier available)
3. Add to `.env`: `OPENSEA_API_KEY=your_key`

### Apify API
1. Sign up at [Apify.com](https://apify.com)
2. Get API token from dashboard
3. Add to `.env`: `APIFY_API_KEY=your_key`

### OpenRouter API  
1. Sign up at [OpenRouter.ai](https://openrouter.ai)
2. Get API key for AI model access
3. Add to `.env`: `OPENROUTER_API_KEY=your_key`

## 🚨 Important Notes

### Data Quality
- **Time filtering**: Only tweets from 24h before sale are included
- **Deduplication**: Removes duplicate tweets automatically  
- **Historical focus**: Uses 2019-2022 data when Twitter was more active for NFTs
- **Multi-model consensus**: Sentiment scores from multiple AI models for accuracy

### Rate Limiting
- Built-in rate limiting for all APIs
- Automatic retries on failures
- Progress tracking with detailed logs

## 🔍 Troubleshooting

### Common Issues

**❌ Missing API Keys**
```bash
❌ Missing API keys: OPENSEA_API_KEY, APIFY_API_KEY
```
**Solution**: Add all required keys to your `.env` file

**❌ No NFT Sales Data**
```bash
❌ No sales data collected
```
**Solution**: Check OpenSea API key or try different collections

**❌ No Tweets Found**
```bash
⚠️ No tweets found
```
**Solution**: Normal for some NFTs - historical data may have limited Twitter activity

**❌ Sentiment Analysis Failed**
```bash
❌ Error analyzing sentiment
```
**Solution**: Check OpenRouter API key and account balance

### Debug Tips
1. **Start with test mode** to validate setup
2. **Check API key permissions** and rate limits
3. **Monitor costs** in API dashboards
4. **Review logs** for specific error messages

## 📈 Example Output

After running `python3 run_pipeline.py --mode test`, you'll see:

```bash
🎯 Running test mode: Quick test run
🚀 Initializing Quick test run
📊 Target: 3 NFT sales
✅ Components initialized

📈 Collecting NFT sales data...
📊 Collected 2 NFT sales

🐦 Collecting Twitter data...
  [1/2] NFT #5172
    ✅ Found 5 tweets
  [2/2] Pudgy Penguin #1987  
    ✅ Found 5 tweets
🐦 Collected 10 total tweets

🧠 Analyzing sentiment for 10 tweets...
    ✅ NFT #5172: 0.600
    ✅ Pudgy Penguin #1987: 0.600
🧠 Analyzed 2 NFT sales

💾 Saving results...
✅ Results saved

🎉 Pipeline completed in 0:01:14
📊 NFT sales: 2
🐦 Tweets: 10
🧠 Sentiment analyzed: 2 sales
```

## 🤝 Contributing

This pipeline is designed to be simple and maintainable. The codebase has been cleaned and optimized for:

- **Readability**: Clear, concise code
- **Maintainability**: Minimal dependencies  
- **Performance**: Efficient API usage
- **Reliability**: Built-in error handling

Feel free to submit issues or pull requests! 