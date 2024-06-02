
def find_max_seeders(
    aggregated_results: dict[str, list[dict[str, int]]]
) -> dict[str, int]:
    """
    Find the maximum number of seeders for each info hash from the aggregated results.

    Args:
        aggregated_results (dict[str, list[dict[str, int]]]): A dictionary containing info hashes as keys and lists of dictionaries
                                                              containing tracker data as values.

    Returns:
        dict[str, int]: A dictionary with info hashes as keys and the maximum number of seeders for each info hash as values.
    """
    max_seeders = {}

    for info_hash, results in aggregated_results.items():
        max_seeder_count = max(
            (result.get("seeders", 0) for result in results), default=0
        )
        max_seeders[info_hash] = max_seeder_count if max_seeder_count > 0 else 0

    return max_seeders
