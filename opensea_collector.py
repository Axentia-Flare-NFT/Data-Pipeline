import asyncio
import httpx
import json
import datetime
from typing import List, Dict, Optional
import time
import os
from dotenv import load_dotenv

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
            url = f"{self.base_url}/chain/ethereum/contract/{collection_slug}/nfts/{identifier}"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
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