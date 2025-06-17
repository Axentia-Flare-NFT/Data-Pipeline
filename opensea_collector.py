import asyncio
import httpx
import json
import datetime
from typing import List, Dict, Optional
import time
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

class OpenSeaCollector:
    """Collects NFT data from OpenSea API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.opensea.io/api/v2"
        
        if not api_key:
            api_key = os.getenv('OPENSEA_API_KEY')
        
        self.headers = {
            "accept": "application/json",
            "user-agent": "NFT-Appraisal-Tool/1.0"
        }
        if api_key:
            self.headers["X-API-KEY"] = api_key
            print(f"✅ Using OpenSea API key: {api_key[:8]}...")
        else:
            print("⚠️ No OpenSea API key found.")
        
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)
    
    async def get_collection_stats(self, collection_slug: str) -> Dict:
        """Get basic stats for a collection."""
        try:
            url = f"{self.base_url}/collections/{collection_slug}/stats"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise ValueError(f"OpenSea API authentication failed for {collection_slug}. Please check your API key or upgrade to a paid tier.")
            else:
                raise ValueError(f"OpenSea API error for {collection_slug}: HTTP {e.response.status_code}")
        except Exception as e:
            raise ValueError(f"Failed to fetch collection stats for {collection_slug}: {e}")
    
    async def get_collection_events(self, collection_slug: str, event_type: str = "sale", 
                                  limit: int = 50, next_cursor: Optional[str] = None,
                                  before_timestamp: Optional[int] = None, 
                                  after_timestamp: Optional[int] = None) -> Dict:
        """
        Get sale events for a collection with date filtering.
        
        Args:
            collection_slug: OpenSea collection slug
            event_type: Type of event ('sale', 'transfer', etc.)
            limit: Number of events to fetch (max 100)
            next_cursor: Cursor for pagination
            before_timestamp: Unix epoch timestamp in seconds - only events before this date
            after_timestamp: Unix epoch timestamp in seconds - only events after this date
        """
        try:
            url = f"{self.base_url}/events/collection/{collection_slug}"
            params = {
                "event_type": event_type,
                "limit": min(limit, 100)
            }
            if next_cursor:
                params["next"] = next_cursor
            if before_timestamp:
                params["before"] = before_timestamp
            if after_timestamp:
                params["after"] = after_timestamp
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise ValueError(f"OpenSea API authentication failed for {collection_slug}. Please check your API key or upgrade to a paid tier.")
            else:
                raise ValueError(f"OpenSea API error for {collection_slug}: HTTP {e.response.status_code}")
        except Exception as e:
            raise ValueError(f"Failed to fetch collection events for {collection_slug}: {e}")
    
    async def get_trending_collections(self, limit: int = 10) -> List[str]:
        """Get trending collections from OpenSea."""
        try:
            # Try to get real trending data from OpenSea
            url = f"{self.base_url}/collections"
            params = {
                "order_by": "seven_day_volume",
                "order_direction": "desc",
                "limit": limit
            }
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if "collections" in data:
                    collections = [collection["collection"] for collection in data["collections"]]
                    print(f"✅ Retrieved {len(collections)} trending collections from OpenSea API")
                    return collections
            
            # If API fails, fall back to curated list
            print("⚠️  Using curated collection list (API may require higher tier access)")
            
        except Exception as e:
            print(f"⚠️  Error fetching trending collections: {e}")
            print("Using curated collection list instead")
        
        # Curated list of top collections by volume/popularity
        trending_collections = [
            "boredapeyachtclub",
            "mutant-ape-yacht-club", 
            "cryptopunks",
            "azuki",
            "pudgypenguins",
            "doodles-official",
            "moonbirds",
            "otherdeed",
            "clonex",
            "meebits",
            "veefriends",
            "cool-cats-nft",
            "bored-ape-kennel-club",
            "world-of-women-nft",
            "cyberkongz"
        ]
        return trending_collections[:limit]
    

    
    async def get_nft_details(self, collection_slug: str, identifier: str) -> Dict:
        """Get detailed information about a specific NFT."""
        try:
            # Get contract address from collection slug
            collection_url = f"{self.base_url}/collections/{collection_slug}"
            collection_response = await self.client.get(collection_url)
            collection_response.raise_for_status()
            
            # Parse collection response
            try:
                collection_data = collection_response.json()
            except Exception as e:
                print(f"Error parsing collection data for {collection_slug}: {e}")
                return {}
            
            # Get contract address directly from the collection data
            contract_address = None
            if isinstance(collection_data, dict):
                # Try to get contract address from the collection data
                contract_address = collection_data.get("primary_asset_contracts", [{}])[0].get("address")
            
            if not contract_address:
                # Fallback to known contract addresses for popular collections
                known_contracts = {
                    "boredapeyachtclub": "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d",
                    "pudgypenguins": "0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
                    "cryptopunks": "0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb",
                    "azuki": "0xed5af388653567af2f388e6224dc7c4b3241c544",
                    "clonex": "0x49cf6f5d44e70224e2e23fdcdd2c053f30ada28b",
                    "doodles-official": "0x8a90cab2b38dba80c64b7734e58ee1db38b8992e"
                }
                contract_address = known_contracts.get(collection_slug)
            
            if not contract_address:
                print(f"No contract address found for {collection_slug}")
                return {}
            
            # Get NFT details using contract address
            url = f"{self.base_url}/chain/ethereum/contract/{contract_address}/nfts/{identifier}"
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parse NFT response
            try:
                nft_data = response.json()
            except Exception as e:
                print(f"Error parsing NFT data for {collection_slug}/{identifier}: {e}")
                return {}
            
            if not isinstance(nft_data, dict):
                print(f"Invalid NFT data format for {collection_slug}/{identifier}")
                return {}
            
            return nft_data
            
        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching NFT details for {collection_slug}/{identifier}: {e}")
            return {}
        except Exception as e:
            print(f"Error fetching NFT details for {collection_slug}/{identifier}: {e}")
            return {}
    
    async def collect_sample_data(self, collection_slugs: List[str], 
                                sales_per_collection: int = 20,
                                use_historical_data: bool = True) -> List[Dict]:
        """
        Collect sample NFT sale data from multiple collections.
        
        Args:
            collection_slugs: List of OpenSea collection slugs
            sales_per_collection: Number of sales to collect per collection
            use_historical_data: If True, filter for 2019-2022 historical data
        
        Returns a list of sale events with relevant metadata for Twitter searching.
        """
        all_sales = []
        
        # Set date range for historical data (2019-2022)
        if use_historical_data:
            import datetime
            # Use 2019-2022 for better Twitter data correlation
            # Convert dates to Unix timestamps (seconds)
            start_date = datetime.datetime(2019, 1, 1, tzinfo=datetime.timezone.utc)
            end_date = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)
            after_timestamp = int(start_date.timestamp())   # Start of 2019
            before_timestamp = int(end_date.timestamp())    # End of 2022
            print(f"📅 Filtering for historical sales: {start_date.isoformat()} to {end_date.isoformat()}")
            print(f"    Unix timestamps: {after_timestamp} to {before_timestamp}")
        else:
            after_timestamp = None
            before_timestamp = None
        
        for collection_slug in collection_slugs:
            print(f"Collecting data for collection: {collection_slug}")
            
            # Get collection stats first
            stats = await self.get_collection_stats(collection_slug)
            
            # Get historical sales with date filtering
            events_data = await self.get_collection_events(
                collection_slug, 
                event_type="sale", 
                limit=sales_per_collection,
                after_timestamp=after_timestamp,
                before_timestamp=before_timestamp
            )
            
            if "asset_events" in events_data:
                print(f"  📊 Found {len(events_data['asset_events'])} historical sales")
                for event in events_data["asset_events"]:
                    try:
                        # Get detailed NFT information including rarity
                        nft = event.get("nft", {})
                        if not isinstance(nft, dict):
                            print(f"Invalid NFT data in event: {nft}")
                            continue
                            
                        nft_identifier = nft.get("identifier")
                        if nft_identifier:
                            nft_details = await self.get_nft_details(collection_slug, nft_identifier)
                            if nft_details and "nft" in nft_details:
                                # Update the event with detailed NFT data
                                event["nft"] = nft_details["nft"]
                        
                        sale_data = self._extract_sale_data(event, collection_slug, stats)
                        if sale_data:
                            all_sales.append(sale_data)
                    except Exception as e:
                        print(f"Error processing event: {e}")
                        continue
            else:
                print(f"  ⚠️  No historical sales found for {collection_slug}")
            
            # Rate limiting - be respectful to OpenSea API
            await asyncio.sleep(0.5)
        
        return all_sales
    
    def _extract_sale_data(self, event: Dict, collection_slug: str, collection_stats: Dict) -> Dict:
        """Extract relevant data from a sale event."""
        try:
            # Extract basic sale data
            nft = event.get("nft", {})
            if not isinstance(nft, dict):
                return None
                
            sale_data = {
                "collection_slug": collection_slug,
                "collection_name": collection_stats.get("name", ""),
                "nft_identifier": nft.get("identifier", ""),
                "nft_name": nft.get("name", ""),
                "token_id": nft.get("identifier", ""),
                "sale_price_wei": event.get("total_price", "0"),
                "sale_price_eth": float(event.get("total_price", "0")) / 1e18,
                "sale_timestamp": event.get("created_date", ""),
                "sale_timestamp_unix": int(datetime.fromisoformat(event.get("created_date", "")).timestamp()),
                "twitter_search_start": (datetime.fromisoformat(event.get("created_date", "")) - timedelta(days=1)).isoformat(),
                "twitter_search_end": event.get("created_date", ""),
                "twitter_keywords": self._generate_twitter_keywords(nft, collection_slug),
                "buyer": event.get("winner_account", {}).get("address", ""),
                "seller": event.get("seller", {}).get("address", ""),
                "transaction_hash": event.get("transaction", {}).get("transaction_hash", ""),
                "opensea_url": f"https://opensea.io/assets/ethereum/{nft.get('contract_address', '')}/{nft.get('identifier', '')}",
                "floor_price": collection_stats.get("floor_price", 0),
                "total_volume": collection_stats.get("total_volume", 0),
                "num_owners": collection_stats.get("num_owners", 0),
                "tweet_count": 0,  # Will be updated by Twitter scraper
                "avg_sentiment": 0.0,  # Will be updated by sentiment analyzer
                "sentiment_confidence": 0.0,  # Will be updated by sentiment analyzer
                "consensus_quality": 0.0,  # Will be updated by sentiment analyzer
                "positive_tweets": 0,  # Will be updated by sentiment analyzer
                "negative_tweets": 0,  # Will be updated by sentiment analyzer
                "neutral_tweets": 0,  # Will be updated by sentiment analyzer
                "sentiment_range_min": 0.0,  # Will be updated by sentiment analyzer
                "sentiment_range_max": 0.0,  # Will be updated by sentiment analyzer
                "rarity_score": nft.get("rarity", {}).get("score"),
                "rarity_rank": nft.get("rarity", {}).get("rank"),
                "rarity_max_rank": nft.get("rarity", {}).get("max_rank"),
                "rarity_tokens_scored": nft.get("rarity", {}).get("tokens_scored"),
                "trait_count": nft.get("rarity", {}).get("trait_count")
            }
            
            return sale_data
            
        except Exception as e:
            print(f"Error extracting sale data: {e}")
            return None
    
    def _generate_twitter_keywords(self, nft: Dict, collection_slug: str) -> List[str]:
        """Generate relevant keywords for Twitter searching."""
        keywords = []
        
        # Collection name variations
        if nft.get("name"):
            keywords.append(nft["name"])
        
        if nft.get("identifier"):
            keywords.append(f"#{nft['identifier']}")
        
        # Collection slug as hashtag
        keywords.append("#" + collection_slug.replace("-", ""))
        
        return keywords
    
    async def save_sample_data(self, sales_data: List[Dict], filename: str = None):
        """Save collected sample data to JSON file."""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nft_samples_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(sales_data, f, indent=2, default=str)
        
        print(f"Saved {len(sales_data)} NFT sale samples to {filename}")
        return filename
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Example usage function
async def collect_nft_samples():
    """Collect sample NFT data for training."""
    collector = OpenSeaCollector()
    
    try:
        # Get trending collections
        collections = await collector.get_trending_collections(limit=3)
        print(f"Collecting data from collections: {collections}")
        
        # Collect sample data
        samples = await collector.collect_sample_data(collections, sales_per_collection=5)
        
        # Save to file
        filename = await collector.save_sample_data(samples)
        
        print(f"\nCollection complete!")
        print(f"Total samples collected: {len(samples)}")
        print(f"Data saved to: {filename}")
        
        return samples, filename
        
    finally:
        await collector.close()

if __name__ == "__main__":
    # Run the collection
    asyncio.run(collect_nft_samples()) 