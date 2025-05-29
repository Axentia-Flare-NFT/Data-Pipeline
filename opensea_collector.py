import asyncio
import httpx
import json
import datetime
from typing import List, Dict, Optional
import time
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class OpenSeaCollector:
    """
    Collects NFT data from OpenSea API for training data collection.
    Falls back to mock data if API access is limited.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.opensea.io/api/v2"
        
        # Use provided API key or load from environment
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
            print("⚠️  No OpenSea API key found. Will use mock data if needed.")
        
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)
        self.use_mock_data = False
    
    async def get_collection_stats(self, collection_slug: str) -> Dict:
        """Get basic stats for a collection."""
        try:
            url = f"{self.base_url}/collections/{collection_slug}/stats"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                print(f"⚠️  OpenSea API requires authentication. Using mock data for {collection_slug}")
                self.use_mock_data = True
                return self._get_mock_collection_stats(collection_slug)
            else:
                print(f"Error fetching collection stats for {collection_slug}: {e}")
                return {}
        except Exception as e:
            print(f"Error fetching collection stats for {collection_slug}: {e}")
            return {}
    
    async def get_collection_events(self, collection_slug: str, event_type: str = "sale", 
                                  limit: int = 50, after: Optional[str] = None) -> Dict:
        """
        Get recent sale events for a collection.
        
        Args:
            collection_slug: OpenSea collection slug
            event_type: Type of event ('sale', 'transfer', etc.)
            limit: Number of events to fetch (max 100)
            after: Cursor for pagination
        """
        try:
            url = f"{self.base_url}/events/collection/{collection_slug}"
            params = {
                "event_type": event_type,
                "limit": min(limit, 100)
            }
            if after:
                params["after"] = after
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                if not self.use_mock_data:
                    print(f"⚠️  OpenSea API requires authentication. Using mock data for {collection_slug}")
                    self.use_mock_data = True
                return self._get_mock_collection_events(collection_slug, limit)
            else:
                print(f"Error fetching events for {collection_slug}: {e}")
                return {}
        except Exception as e:
            print(f"Error fetching events for {collection_slug}: {e}")
            return {}
    
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
    
    def _get_mock_collection_stats(self, collection_slug: str) -> Dict:
        """Generate realistic mock collection stats."""
        mock_stats = {
            "boredapeyachtclub": {
                "collection": {"name": "Bored Ape Yacht Club"},
                "total": {
                    "floor_price": 12.5,
                    "volume": 645123.4,
                    "num_owners": 6420
                }
            },
            "mutant-ape-yacht-club": {
                "collection": {"name": "Mutant Ape Yacht Club"},
                "total": {
                    "floor_price": 4.2,
                    "volume": 123456.7,
                    "num_owners": 8901
                }
            },
            "cryptopunks": {
                "collection": {"name": "CryptoPunks"},
                "total": {
                    "floor_price": 85.0,
                    "volume": 987654.3,
                    "num_owners": 3456
                }
            },
            "azuki": {
                "collection": {"name": "Azuki"},
                "total": {
                    "floor_price": 8.7,
                    "volume": 234567.8,
                    "num_owners": 5432
                }
            },
            "pudgypenguins": {
                "collection": {"name": "Pudgy Penguins"},
                "total": {
                    "floor_price": 6.3,
                    "volume": 156789.2,
                    "num_owners": 4321
                }
            }
        }
        
        return mock_stats.get(collection_slug, {
            "collection": {"name": collection_slug.replace("-", " ").title()},
            "total": {
                "floor_price": random.uniform(1.0, 50.0),
                "volume": random.uniform(10000, 500000),
                "num_owners": random.randint(1000, 10000)
            }
        })
    
    def _get_mock_collection_events(self, collection_slug: str, limit: int) -> Dict:
        """Generate realistic mock sale events."""
        base_time = datetime.datetime.now(datetime.timezone.utc)
        events = []
        
        collection_stats = self._get_mock_collection_stats(collection_slug)
        floor_price = collection_stats.get("total", {}).get("floor_price", 10.0)
        
        for i in range(limit):
            # Generate sale timestamp (recent sales within last 7 days)
            hours_ago = random.uniform(1, 168)  # 1 hour to 7 days ago
            sale_time = base_time - datetime.timedelta(hours=hours_ago)
            
            # Generate sale price around floor price with variation
            price_multiplier = random.uniform(0.8, 3.0)  # 80% to 300% of floor
            sale_price_eth = floor_price * price_multiplier
            sale_price_wei = int(sale_price_eth * 1e18)
            
            # Generate token ID
            token_id = str(random.randint(1, 10000))
            
            event = {
                "event_timestamp": sale_time.isoformat().replace('+00:00', 'Z'),
                "nft": {
                    "identifier": token_id,
                    "name": f"{collection_stats['collection']['name']} #{token_id}",
                    "opensea_url": f"https://opensea.io/assets/ethereum/{collection_slug}/{token_id}"
                },
                "payment": {
                    "quantity": str(sale_price_wei)
                },
                "to_account": {
                    "address": f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
                },
                "from_account": {
                    "address": f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
                },
                "transaction": f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
            }
            events.append(event)
        
        return {"asset_events": events}
    
    async def get_nft_details(self, collection_slug: str, identifier: str) -> Dict:
        """Get detailed information about a specific NFT."""
        try:
            url = f"{self.base_url}/chain/ethereum/contract/{collection_slug}/nfts/{identifier}"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching NFT details for {collection_slug}/{identifier}: {e}")
            return {}
    
    async def collect_sample_data(self, collection_slugs: List[str], 
                                sales_per_collection: int = 20) -> List[Dict]:
        """
        Collect sample NFT sale data from multiple collections.
        
        Returns a list of sale events with relevant metadata for Twitter searching.
        """
        all_sales = []
        
        for collection_slug in collection_slugs:
            print(f"Collecting data for collection: {collection_slug}")
            
            # Get collection stats first
            stats = await self.get_collection_stats(collection_slug)
            
            # Get recent sales
            events_data = await self.get_collection_events(
                collection_slug, 
                event_type="sale", 
                limit=sales_per_collection
            )
            
            if "asset_events" in events_data:
                for event in events_data["asset_events"]:
                    try:
                        sale_data = self._extract_sale_data(event, collection_slug, stats)
                        if sale_data:
                            all_sales.append(sale_data)
                    except Exception as e:
                        print(f"Error processing event: {e}")
                        continue
            
            # Rate limiting - be respectful to OpenSea API
            await asyncio.sleep(0.5)
        
        return all_sales
    
    def _extract_sale_data(self, event: Dict, collection_slug: str, stats: Dict) -> Optional[Dict]:
        """Extract relevant data from a sale event."""
        try:
            if not event.get("nft") or not event.get("payment"):
                return None
            
            nft = event["nft"]
            payment = event["payment"]
            
            # Extract timestamps - handle different formats from OpenSea API
            event_timestamp = event.get("event_timestamp")
            if event_timestamp:
                # Handle both string and integer timestamps
                if isinstance(event_timestamp, str):
                    # If it's already a string, parse it
                    sale_time = datetime.datetime.fromisoformat(event_timestamp.replace('Z', '+00:00'))
                elif isinstance(event_timestamp, (int, float)):
                    # If it's a Unix timestamp, convert it
                    sale_time = datetime.datetime.fromtimestamp(event_timestamp, tz=datetime.timezone.utc)
                else:
                    print(f"Unknown timestamp format: {type(event_timestamp)} - {event_timestamp}")
                    return None
            else:
                return None
            
            # Calculate 24h before for Twitter search
            search_start = sale_time - datetime.timedelta(hours=24)
            
            # Extract collection name from stats or use collection slug
            collection_name = collection_slug.replace("-", " ").title()
            if stats and "total" in stats:
                # For OpenSea API v2, there's no nested 'collection' object
                # Use the collection slug converted to a readable name
                pass
            
            sale_data = {
                # Identifiers
                "collection_slug": collection_slug,
                "collection_name": collection_name,
                "nft_identifier": nft.get("identifier"),
                "nft_name": nft.get("name"),
                "token_id": nft.get("identifier"),
                
                # Sale information
                "sale_price_wei": payment.get("quantity"),
                "sale_price_eth": float(payment.get("quantity", 0)) / 1e18 if payment.get("quantity") else 0,
                "sale_timestamp": sale_time.isoformat(),
                "sale_timestamp_unix": int(sale_time.timestamp()),
                
                # Twitter search parameters
                "twitter_search_start": search_start.isoformat(),
                "twitter_search_end": sale_time.isoformat(),
                "twitter_keywords": self._generate_twitter_keywords(nft, collection_slug, collection_name),
                
                # Additional metadata
                "buyer": event.get("buyer", {}).get("address") if isinstance(event.get("buyer"), dict) else event.get("buyer"),
                "seller": event.get("seller", {}).get("address") if isinstance(event.get("seller"), dict) else event.get("seller"),
                "transaction_hash": event.get("transaction"),
                "opensea_url": nft.get("opensea_url"),
                
                # Collection context from stats
                "floor_price": stats.get("total", {}).get("floor_price") if stats else None,
                "total_volume": stats.get("total", {}).get("volume") if stats else None,
                "num_owners": stats.get("total", {}).get("num_owners") if stats else None,
            }
            
            return sale_data
            
        except Exception as e:
            print(f"Error extracting sale data: {e}")
            return None
    
    def _generate_twitter_keywords(self, nft: Dict, collection_slug: str, collection_name: str) -> List[str]:
        """Generate relevant keywords for Twitter searching."""
        keywords = []
        
        # Collection name variations
        if collection_name:
            keywords.append(collection_name)
            # Add hashtag version
            hashtag = "#" + collection_name.replace(" ", "").replace("-", "")
            keywords.append(hashtag)
        
        # Collection slug as hashtag
        keywords.append("#" + collection_slug.replace("-", ""))
        
        # NFT specific
        if nft.get("name"):
            keywords.append(nft["name"])
        
        if nft.get("identifier"):
            keywords.append(f"#{nft['identifier']}")
        
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