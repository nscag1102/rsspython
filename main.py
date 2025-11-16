import requests  # type: ignore

def main():
    # Read feeds from feeds.txt file
    # Open the file and read all non-empty lines, stripping whitespace
    with open("feeds.txt", "r", encoding="utf-8") as f:
        feeds = [line.strip() for line in f if line.strip()]
    
    # Display how many feeds were found
    print(f"Found {len(feeds)} feed(s) to scrape\n")
    
    # Loop over each feed URL and grab its contents
    for feed_url in feeds:
        print(f"Fetching: {feed_url}")
        try:
            # Use requests to fetch the RSS feed content
            # timeout=10 means wait up to 10 seconds for a response
            response = requests.get(feed_url, timeout=10)
            # Raise an exception if the HTTP status code indicates an error
            response.raise_for_status()
            # Get the text content of the response (the RSS/XML feed)
            content = response.text
            print(f"  Success! Content length: {len(content)} characters\n")
        except requests.RequestException as e:
            # Handle any errors that occur during the request (network errors, HTTP errors, etc.)
            print(f"  Error fetching {feed_url}: {e}\n")


if __name__ == "__main__":
    # Only run main() if this script is executed directly (not imported as a module)
    main()
