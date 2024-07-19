import pytest
from pyasynctracker import scrape_info_hashes, batch_scrape_info_hashes


@pytest.mark.asyncio
async def test_scrape_info_hashes():
    info_hashes = ['bceb15ae55e17ae765af504a8f645595b936aefa']
    trackers = ["udp://tracker.opentrackr.org:1337/announce", "https://tracker1.ctix.cn:443/announce", "udp://open.demonii.com:1337/announce", "https://tracker.loligirl.cn:443/announce", "udp://open.stealth.si:80/announce", "udp://tracker.torrent.eu.org:451/announce", "udp://tracker-udp.gbitt.info:80/announce", "udp://exodus.desync.com:6969/announce", "https://tracker.gbitt.info:443/announce", "http://tracker.gbitt.info:80/announce", "http://bvarf.tracker.sh:2086/announce", "udp://tracker.tryhackx.org:6969/announce", "udp://tracker.tiny-vps.com:6969/announce", "udp://tracker.picotorrent.one:6969/announce", "udp://tracker.0x7c0.com:6969/announce"]

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
