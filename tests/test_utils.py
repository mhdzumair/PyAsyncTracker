from pyasynctracker.utils import find_max_seeders


def test_find_max_seeders():
    results = {
        '2b66980093bc11806fab50cb3cb41835b95a0362': [
            {'tracker_url': 'http://bttracker.debian.org:6969/announce', 'seeders': 1022, 'peers': 2, 'complete': 14920}
        ]
    }
    max_seeders = find_max_seeders(results)
    assert max_seeders['2b66980093bc11806fab50cb3cb41835b95a0362'] == 1022
