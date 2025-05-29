# NFT Data Collection Pipeline

**Enterprise-grade NFT data collection with advanced consensus sentiment analysis**

Collect comprehensive NFT datasets with social metrics, sentiment analysis, and market data for machine learning and research.

## 🚀 Features

- **📊 Complete NFT Data**: Sales, prices, metadata from OpenSea
- **🐦 Social Metrics**: Twitter engagement and reach analysis  
- **🤖 Advanced Sentiment**: Consensus learning with 300+ LLMs via OpenRouter
- **⚡ Fast & Scalable**: Optimized for large datasets (1000+ NFTs)
- **📁 Clean Output**: Production-ready CSV files for ML training
- **🛡️ Robust**: Error handling, rate limiting, retry logic

## 📁 Project Structure

```
NFT-Scraping/
├── quick_test.py              # Quick pipeline test (3-5 NFTs)
├── full_collection.py         # Full collection (1000+ NFTs)  
├── data_collector.py          # Main orchestrator
├── opensea_collector.py       # OpenSea API integration
├── twitter_scraper.py         # Twitter data collection
├── sentiment_analyzer_advanced.py  # Flare AI consensus learning
├── flare-ai-consensus/        # Advanced consensus framework
├── requirements.txt           # Dependencies
└── .env                       # API keys (create this)
```

## ⚡ Quick Start

### 1. Setup Environment

```bash
# Clone repository
git clone <repository-url>
cd NFT-Scraping

# Install dependencies
pip3 install -r requirements.txt

# Create environment file
cp .env.example .env
```

### 2. Add API Keys

Create `.env` file with your credentials:

```bash
# Required for sentiment analysis
OPENROUTER_API_KEY=your_openrouter_key_here

# Required for social metrics
X_USERNAME=your_twitter_username
X_EMAIL=your_twitter_email  
X_PASSWORD=your_twitter_password

# Optional (higher rate limits)
OPENSEA_API_KEY=your_opensea_key_here
```

### 3. Run Quick Test

```bash
python3 quick_test.py
```

### 4. Run Full Collection

```bash
python3 full_collection.py
```

## 🔑 API Keys Setup

### OpenRouter (Required for Sentiment)
1. Visit [OpenRouter.ai](https://openrouter.ai/keys)
2. Create account and generate API key
3. Add credits for paid tier models (recommended)

### Twitter (Required for Social Metrics)
- Use your existing Twitter account credentials
- Ensure account is in good standing (not rate-limited)

### OpenSea (Optional)
1. Visit [OpenSea Developer](https://opensea.io/account/settings)
2. Generate API key for higher rate limits

## 📊 Output Data

### Main Dataset: `nft_data/nft_features.csv`

Complete feature set for ML training:

| Column | Description | Type |
|--------|-------------|------|
| `nft_name` | NFT identifier | string |
| `collection_slug` | Collection identifier | string |
| `sale_price_eth` | Sale price in ETH | float |
| `transaction_hash` | Blockchain transaction | string |
| `seller_address` | Seller wallet address | string |
| `buyer_address` | Buyer wallet address | string |
| `total_tweets` | Tweet volume | int |
| `unique_tweeters` | Unique users tweeting | int |
| `total_engagement` | Likes + retweets + replies | int |
| `avg_sentiment` | Consensus sentiment (-1 to +1) | float |
| `sentiment_confidence` | Analysis confidence (0-1) | float |
| `positive_tweets` | Count of positive tweets | int |
| `negative_tweets` | Count of negative tweets | int |
| `neutral_tweets` | Count of neutral tweets | int |
| `consensus_model_count` | Models used in consensus | int |

### Additional Files

- `nft_metadata.csv`: NFT details and timestamps
- `raw_tweets.csv`: Individual tweet data

## 🤖 Sentiment Analysis

**Enterprise-Grade Flare AI Consensus Learning**

- **Framework**: Flare AI Consensus Learning
- **Models**: 300+ LLMs via OpenRouter 
- **Method**: Multi-model consensus with aggregation
- **Speed**: Optimized with 2 fast models, 0 iterations
- **Quality**: Production-ready enterprise accuracy
- **Required**: OpenRouter API key

## 📈 Use Cases

- **Price Prediction**: Sentiment → price correlation analysis
- **Hype Detection**: Social metrics → market timing
- **Collection Analysis**: Community engagement patterns
- **Market Research**: NFT ecosystem insights
- **Academic Research**: Social media impact studies

## ⚙️ Configuration

### Collection Size
- **Quick Test**: 4 NFTs across 2 collections (~60-90 seconds)
- **Full Collection**: 1000+ NFTs (~2-3 hours)

### Rate Limiting
- **Twitter**: 8 seconds between NFTs, 3 minutes between collections
- **OpenSea**: Respects API limits
- **OpenRouter**: Optimized for paid tier

### Tweet Analysis
- **Quick Test**: 6 tweets per NFT (optimized for speed)
- **Full Collection**: 20 tweets per NFT (comprehensive analysis)

### Popular Collections Included
```python
POPULAR_COLLECTIONS = [
    'boredapeyachtclub', 'cryptopunks', 'azuki',
    'pudgypenguins', 'doodles-official', 'moonbirds',
    'clonex', 'otherdeed', 'veefriends', 'cool-cats-nft',
    # ... 20 total collections
]
```

## 🛠️ Advanced Usage

### Custom Collections
Edit collections list in `full_collection.py`:

```python
CUSTOM_COLLECTIONS = [
    'your-collection-slug',
    'another-collection'
]
```

### Sentiment Model Selection
Modify models in `sentiment_analyzer_advanced.py`:

```python
models = [
    ModelConfig(model_id="anthropic/claude-3-haiku", ...),
    ModelConfig(model_id="openai/gpt-4o-mini", ...),
    # Add more models as needed
]
```

## 🔧 Troubleshooting

### Common Issues

**"Twitter rate limited"**
- Wait 15-30 minutes and retry
- Ensure account is in good standing

**"OpenRouter API error"**  
- Check API key validity
- Ensure sufficient credits
- Try different model selection

**"No NFT data found"**
- Verify collection slug is correct
- Check OpenSea API key
- Try different collection

### Debug Mode
Run with verbose logging:
```bash
export LOG_LEVEL=DEBUG
python3 quick_test.py
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request with tests

## 📧 Support

For issues or questions:
- Create GitHub issue
- Check troubleshooting section
- Review API provider documentation

---

**Built with Flare AI Consensus Learning** 🧠⚡ 