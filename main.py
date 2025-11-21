# Import requests library for making HTTP requests to fetch RSS feeds
import requests  # type: ignore
# Import feedparser library for parsing RSS and Atom feed formats
import feedparser  # type: ignore
# Import datetime for handling publication dates and timestamps
from datetime import datetime
# Import Optional type hint for fields that may not always be present
from typing import Optional
# Import Pydantic BaseModel and Field for data validation and model definition
from pydantic import BaseModel, Field  # type: ignore


# Pydantic model for individual RSS feed items/entries
# Each RSS feed contains multiple items (articles, posts, etc.)
# This model represents a single item with all its metadata
class FeedItem(BaseModel):
    """Model representing a single RSS feed item/entry (e.g., an article or blog post)."""
    # Title is required - every feed item should have a title
    title: str = Field(..., description="Title of the feed item")
    # Link to the full article/post (optional as some feeds may not include it)
    link: Optional[str] = Field(None, description="URL link to the full article")
    # Description or summary of the item content (optional)
    description: Optional[str] = Field(None, description="Description or summary of the item")
    # Publication date when the item was published (optional, not all feeds include dates)
    published: Optional[datetime] = Field(None, description="Publication date of the item")
    # Author name if available (optional, many feeds don't include author information)
    author: Optional[str] = Field(None, description="Author of the item")
    # Unique identifier for the item, typically a GUID or the item's link URL
    id: Optional[str] = Field(None, description="Unique identifier for the item")


# Pydantic model for the RSS feed itself
# This represents the entire feed with its metadata and collection of items
class RSSFeed(BaseModel):
    """Model representing an RSS feed with its metadata and collection of feed items."""
    # Title of the RSS feed (required - every feed should have a title)
    title: str = Field(..., description="Title of the RSS feed")
    # Link to the website or source of the feed (optional)
    link: Optional[str] = Field(None, description="URL link to the feed source")
    # Description of what the feed is about (optional)
    description: Optional[str] = Field(None, description="Description of the feed")
    # The URL where we fetched this feed from (required for tracking)
    feed_url: str = Field(..., description="URL where the feed was fetched from")
    # List of all feed items/articles in this feed (defaults to empty list if no items)
    items: list[FeedItem] = Field(default_factory=list, description="List of feed items")
    # Last time the feed was updated (optional, not all feeds provide this)
    updated: Optional[datetime] = Field(None, description="Last update time of the feed")


def parse_feed(content: str, feed_url: str) -> RSSFeed:
    """
    Parse RSS feed content (XML string) and map it to Pydantic models.
    
    This function takes raw RSS/Atom XML content and converts it into structured
    Pydantic models that can be easily used throughout the application.
    
    Args:
        content: The raw XML string content of the RSS feed
        feed_url: The URL where this feed was fetched from (for tracking purposes)
    
    Returns:
        RSSFeed: A validated Pydantic model containing the parsed feed data
    """
    # Parse the RSS/Atom feed XML content using feedparser
    # feedparser handles both RSS and Atom formats automatically
    parsed = feedparser.parse(content)
    
    # Extract feed-level metadata from the parsed feed
    # Use .get() with defaults to handle missing fields gracefully
    feed_title = parsed.feed.get("title", "Untitled Feed")
    feed_link = parsed.feed.get("link")
    feed_description = parsed.feed.get("description")
    
    # Parse the feed's last updated timestamp if available
    # feedparser provides dates in a parsed tuple format that we convert to datetime
    feed_updated = None
    if "updated_parsed" in parsed.feed and parsed.feed.updated_parsed:
        # Convert the parsed time tuple (year, month, day, hour, minute, second, ...)
        # to a Python datetime object using tuple unpacking
        feed_updated = datetime(*parsed.feed.updated_parsed[:6])
    
    # Map each feed entry (article/post) to a FeedItem Pydantic model
    # This creates a list of structured, validated feed items
    feed_items = []
    for entry in parsed.entries:
        # Parse the publication date for this entry
        # Some feeds use "published_parsed", others use "updated_parsed"
        # We check both and use whichever is available
        published = None
        if "published_parsed" in entry and entry.published_parsed:
            # Convert parsed time tuple to datetime object
            published = datetime(*entry.published_parsed[:6])
        elif "updated_parsed" in entry and entry.updated_parsed:
            # Fall back to updated_parsed if published_parsed is not available
            published = datetime(*entry.updated_parsed[:6])
        
        # Create a FeedItem Pydantic model instance from the entry data
        # This validates the data and ensures type safety
        item = FeedItem(
            title=entry.get("title", "Untitled"),  # Default to "Untitled" if no title
            link=entry.get("link"),  # May be None if not provided
            # Some feeds use "description", others use "summary" - try both
            description=entry.get("description") or entry.get("summary"),
            published=published,  # May be None if no date information
            author=entry.get("author"),  # May be None if author not specified
            # Use entry ID if available, otherwise fall back to the link as identifier
            id=entry.get("id") or entry.get("link"),
        )
        feed_items.append(item)
    
    # Create and return the RSSFeed Pydantic model containing all parsed data
    # This model validates all the data and provides a clean, structured interface
    return RSSFeed(
        title=feed_title,
        link=feed_link,
        description=feed_description,
        feed_url=feed_url,  # Store the original URL for reference
        items=feed_items,  # List of all parsed feed items
        updated=feed_updated,
    )


##def test_sanity():
 #   """
#   Test the sanity of the RSS feed parsing function.
#   """
#   # Test the sanity of the RSS feed parsing function
#   # This tests the sanity of the RSS feed parsing function
#   # This tests the sanity of the RSS feed parsing function
#   assert 1==1
#
def main():
    """
    Main function that orchestrates the RSS feed scraping process.
    
    This function reads feed URLs from a file, fetches each feed, parses it,
    and maps it to Pydantic models for structured data access.
    """
    # Read feed URLs from the feeds.txt file
    # The file should contain one RSS feed URL per line
    # Open the file in read mode with UTF-8 encoding to handle international characters
    with open("feeds.txt", "r", encoding="utf-8") as f:
        # Read all lines, strip whitespace, and filter out empty lines
        # This creates a list of clean feed URLs ready to be processed
        feeds = [line.strip() for line in f if line.strip()]
    
    # Display how many feeds were found in the file
    # This gives the user feedback about what will be processed
    print(f"Found {len(feeds)} feed(s) to scrape\n")
    
    # Loop over each feed URL and fetch its contents
    # Process each feed one at a time to avoid overwhelming the network or servers
    for feed_url in feeds:
        print(f"Fetching: {feed_url}")
        try:
            # Use the requests library to make an HTTP GET request to fetch the RSS feed
            # timeout=10 means the request will wait up to 10 seconds for a response
            # This prevents the script from hanging indefinitely on slow or unresponsive servers
            response = requests.get(feed_url, timeout=10)
            
            # Check if the HTTP response indicates an error (4xx, 5xx status codes)
            # raise_for_status() will raise an exception if the status code indicates an error
            # This helps us catch issues like 404 (not found) or 500 (server error) early
            response.raise_for_status()
            
            # Extract the text content from the HTTP response
            # This is the raw RSS/XML feed content that we'll parse next
            content = response.text
            
            # Parse the raw XML content and map it to our Pydantic models
            # This converts the unstructured XML into structured, validated Python objects
            rss_feed = parse_feed(content, feed_url)
            
            # Display summary information about the successfully parsed feed
            # Show the feed title, number of items, and link if available
            print(f"  ✓ Success! Parsed feed: {rss_feed.title}")
            print(f"    Items: {len(rss_feed.items)}")
            if rss_feed.link:
                print(f"    Link: {rss_feed.link}")
            print()
            
            # Display a sample of the first few items from the feed
            # This gives the user a preview of what's in the feed without overwhelming output
            if rss_feed.items:
                print(f"    Sample items:")
                # Show only the first 3 items as a preview
                for item in rss_feed.items[:3]:
                    print(f"      - {item.title}")
                    # If the item has a publication date, display it in a readable format
                    if item.published:
                        print(f"        Published: {item.published.strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                
        except requests.RequestException as e:
            # Handle any errors that occur during the HTTP request
            # This includes network errors (connection timeout, DNS failure, etc.)
            # and HTTP errors (404, 500, etc.) that raise_for_status() caught
            print(f"  ✗ Error fetching {feed_url}: {e}\n")
        except Exception as e:
            # Handle any other errors that might occur during parsing or processing
            # This catches issues like malformed XML, validation errors, etc.
            print(f"  ✗ Error parsing feed {feed_url}: {e}\n")


if __name__ == "__main__":
    # Only run main() if this script is executed directly (not imported as a module)
    # This allows the script to be both run standalone and imported as a library
    # When imported, the code won't automatically execute, allowing other scripts to use the functions
    main()
