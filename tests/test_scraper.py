import pytest
from pyasynctracker.scraper import scrape_info_hashes, batch_scrape_info_hashes


@pytest.mark.asyncio
async def test_scrape_info_hashes():
    info_hashes = ["2b66980093bc11806fab50cb3cb41835b95a0362"]
    trackers = ["http://bttracker.debian.org:6969/announce"]

    results = await scrape_info_hashes(info_hashes, trackers)
    assert isinstance(results, dict)
    assert all(key in results for key in info_hashes)
    for res in results.values():
        for tracker_data in res:
            assert 'tracker_url' in tracker_data
            assert 'seeders' in tracker_data
            assert 'peers' in tracker_data
            assert 'complete' in tracker_data


@pytest.mark.asyncio
async def test_batch_scrape_info_hashes():
    data_list = [
        ("2b66980093bc11806fab50cb3cb41835b95a0362", ["http://bttracker.debian.org:6969/announce"])
    ]
    results = await batch_scrape_info_hashes(data_list)
    assert isinstance(results, dict)
    assert all(key in results for key, _ in data_list)
