# PyAsyncTracker

PyAsyncTracker is an asynchronous library for scraping torrent tracker data. It provides tools to fetch and analyze torrent seeders, leechers, and completed downloads across multiple trackers efficiently using modern asynchronous techniques.

## Features

- **Support UDP and HTTP Trackers**: Scrapes torrent data from both UDP and HTTP trackers.
- **Asynchronous Operations**: Leveraging Python's `asyncio` for non-blocking I/O.
- **Batch Processing**: Supports scraping multiple info hashes across multiple trackers efficiently.
- **Data Analysis Function**: Includes utility functions to analyze and summarize scraped data.

## Installation

Install PyAsyncTracker using pip:

```bash
pip install pyasynctracker
```

## Usage

### Scrape Info Hashes

Scrape torrent data asynchronously from multiple trackers for given info hashes.

```python
from pyasynctracker import scrape_info_hashes

async def main():
    info_hashes = ["2b66980093bc11806fab50cb3cb41835b95a0362", "706440a3f8fdac91591d6007c4314f3274317f85"]
    trackers = [
        "http://bttracker.debian.org:6969/announce",
        "udp://tracker.openbittorrent.com:80/announce",
        "udp://tracker.opentrackr.org:1337/announce",
    ]

    results = await scrape_info_hashes(info_hashes, trackers)
    print(results)
    # {
    #   '706440a3f8fdac91591d6007c4314f3274317f85': [
    #       {'tracker_url': 'http://bttracker.debian.org:6969/announce', 'seeders': 168, 'peers': 1, 'complete': 769}, 
    #       {'tracker_url': 'udp://tracker.opentrackr.org:1337/announce', 'seeders': 5, 'peers': 0, 'complete': 20}
    #    ],
    #   '2b66980093bc11806fab50cb3cb41835b95a0362': [
    #       {'tracker_url': 'http://bttracker.debian.org:6969/announce', 'seeders': 1022, 'peers': 2, 'complete': 14920}, 
    #       {'tracker_url': 'udp://tracker.opentrackr.org:1337/announce', 'seeders': 25, 'peers': 0, 'complete': 184}
    #    ]
    # }


# Run the async main function using asyncio
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Batch Scrape Info Hashes

Batch scrape info hashes based on a structured input of info hashes and their respective trackers. This function groups info hashes by their associated trackers and performs scraping in batches.

```python
from pyasynctracker import batch_scrape_info_hashes

async def main():
    data_list = [
        ("2b66980093bc11806fab50cb3cb41835b95a0362", ["http://bttracker.debian.org:6969/announce"]),
        ("706440a3f8fdac91591d6007c4314f3274317f85", ["udp://tracker.opentrackr.org:1337/announce"])
    ]

    results = await batch_scrape_info_hashes(data_list)
    print(results)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Find Maximum Seeders

Analyze the results from scraping functions to find the maximum number of seeders for each info hash.

```python
from pyasynctracker import find_max_seeders

# Assuming 'results' is populated from the scrape_info_hashes or batch_scrape_info_hashes functions
max_seeders = find_max_seeders(results)
print(max_seeders)

# {'2b66980093bc11806fab50cb3cb41835b95a0362': 1022, '706440a3f8fdac91591d6007c4314f3274317f85': 168}
```

## Contributing

Contributions to PyAsyncTracker are welcome! Please fork the repository and submit pull requests with your proposed changes. Ensure to follow coding standards and write tests for new features.

## License

PyAsyncTracker is released under the MIT License. See the [LICENSE](LICENSE) file for more details.
