import asyncio
import binascii
import logging
import random
import struct
from collections import defaultdict
from urllib import parse

import aiodns
import aiohttp
import bencodepy


async def scrape_info_hashes(
        info_hashes: list[str], tracker_list: list[str], timeout: int = 10
) -> dict[str, list[dict]]:
    """
    Asynchronously scrape seeders, peers, and completion counts for given info hashes from specified trackers.

    Args:
        info_hashes (list[str]): A list of info hashes to scrape.
        tracker_list (list[str]): A list of tracker URLs to use for scraping.
        timeout (int): Timeout in seconds for each request.

    Returns:
        dict[str, list[dict]]: A dictionary with info hashes as keys and lists of dictionaries containing
                               tracker data as values.
    """
    tasks = [scrape_tracker(tracker, info_hashes, timeout) for tracker in tracker_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    aggregated_results = {}

    for result in results:
        if isinstance(result, dict):
            for hash_key, data in result.items():
                if hash_key not in aggregated_results:
                    aggregated_results[hash_key] = []
                aggregated_results[hash_key].append(data)
        else:
            logging.error(f"Error in scraping tracker {result}")

    return aggregated_results


async def batch_scrape_info_hashes(
        data_list: list[tuple[str, list[str]]], timeout: int = 10
) -> dict[str, list[dict]]:
    """
    Batch scrape info hashes based on a list of data where each entry contains an info hash and associated trackers.
    This method groups info hashes by their associated trackers and performs scraping in batches.

    Args:
        data_list (list[tuple[str, list[str]]]): A list of tuples, each containing an info hash and a list of tracker URLs.
        timeout (int): Timeout in seconds for each request.

    Returns:
        dict[str, list[dict]]: A dictionary with info hashes as keys and lists of dictionaries containing
                               aggregated results from each tracker as values.
    """
    # Dictionary to hold sets of tracker URLs and their corresponding info hashes
    tracker_sets_to_hashes = defaultdict(set)
    for info_hash, trackers in data_list:
        tracker_set = frozenset(trackers)
        tracker_sets_to_hashes[tracker_set].add(info_hash)

    all_results = {}
    scrape_tasks = []

    for trackers, info_hashes in tracker_sets_to_hashes.items():
        task = scrape_info_hashes(list(info_hashes), list(trackers), timeout)
        scrape_tasks.append(task)

    scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)

    for results in scrape_results:
        if isinstance(results, dict):
            for hash_key, result in results.items():
                if hash_key not in all_results:
                    all_results[hash_key] = []
                all_results[hash_key].extend(result)
        else:
            logging.error(f"Error in scraping process: {results}")

    return all_results


async def scrape_tracker(tracker: str, info_hashes: list[str], timeout: int):
    parsed = parse.urlparse(tracker)
    if parsed.scheme == "udp":
        return await scrape_udp(parsed, info_hashes, timeout)
    elif parsed.scheme in ["http", "https"]:
        return await scrape_http(parsed, info_hashes, timeout)
    else:
        raise ValueError(f"Unsupported scheme: {parsed.scheme} for {tracker}")


async def scrape_http(parsed_tracker, info_hashes: list[str], timeout: int):
    qs = [
        ("info_hash", binascii.a2b_hex(info_hash.encode("utf-8")))
        for info_hash in info_hashes
    ]
    qs = parse.urlencode(qs, doseq=True)
    url = parse.urlunsplit(
        (
            parsed_tracker.scheme,
            parsed_tracker.netloc,
            parsed_tracker.path.replace("announce", "scrape"),
            qs,
            "",
        )
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    raise RuntimeError(f"{response.status} status code returned")
                content = await response.read()
                decoded_dict = bencodepy.decode(content)
                result = {}
                for byte_hash, stats in decoded_dict[b"files"].items():
                    readable_hash = binascii.b2a_hex(byte_hash).decode("utf-8")
                    if readable_hash in [
                        binascii.b2a_hex(
                            binascii.a2b_hex(info_hash.encode("utf-8"))
                        ).decode("utf-8")
                        for info_hash in info_hashes
                    ]:
                        result[readable_hash] = {
                            "tracker_url": parsed_tracker.geturl(),
                            "seeders": stats[b"complete"],
                            "peers": stats[b"incomplete"],
                            "complete": stats[b"downloaded"],
                        }
                return result
        except Exception as e:
            logging.error(f"Error occurred for {parsed_tracker.geturl()}: {e}")
            return {}


class UDPTrackerClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, message, response_handler, error_handler):
        self.message = message
        self.response_handler = response_handler
        self.error_handler = error_handler
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        self.transport.sendto(self.message)

    def datagram_received(self, data, addr):
        asyncio.create_task(self.response_handler(data))

    def error_received(self, exc):
        self.error_handler(exc)

    def connection_lost(self, exc):
        if exc:
            self.error_handler(exc)


async def resolve_hostname(hostname):
    resolver = aiodns.DNSResolver()
    try:
        result = await resolver.query(hostname, "A")
        return result[0].host
    except Exception as e:
        return str(e)


async def send_udp_request(parsed_tracker, message, response_handler, error_handler, timeout):
    loop = asyncio.get_running_loop()
    resolver = aiodns.DNSResolver(loop=loop)
    try:
        query = await resolver.query(parsed_tracker.hostname, "A")
        ip = query[0].host
    except Exception as e:
        error_handler(f"DNS resolution failed for {parsed_tracker.geturl()} - {e}")
        return

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPTrackerClientProtocol(message, response_handler, error_handler),
        remote_addr=(ip, parsed_tracker.port),
    )
    try:
        await asyncio.wait_for(asyncio.sleep(timeout), timeout=timeout)  # Timeout for response
    except asyncio.TimeoutError:
        error_handler(f"Timeout while waiting for response from {parsed_tracker.geturl()}")
    finally:
        if transport.is_closing():
            transport.abort()
        else:
            try:
                transport.close()
            except RuntimeError:
                pass


def udp_create_connection_request():
    connection_id = 0x41727101980  # default connection id
    action = 0  # action (0 = give me a new connection id)
    transaction_id = random.randint(0, 0xFFFFFFFF)
    # Use 'II' for unsigned ints to handle the full range of possible transaction_ids
    buf = struct.pack("!qII", connection_id, action, transaction_id)
    return buf, transaction_id


def udp_create_scrape_request(connection_id, info_hashes):
    base_size = 16  # Basic overhead for connection ID, action, and transaction ID in bytes
    max_packet_size = 508  # Maximum safe UDP packet size in bytes
    action = 2  # Action code for 'scrape'
    transaction_id = random.randint(0, 0xFFFFFFFF)

    # Start assembling the packet
    packet = struct.pack("!qII", connection_id, action, transaction_id)
    included_hashes = []

    for info_hash in info_hashes:
        hash_bytes = binascii.a2b_hex(info_hash)
        # Check if adding this hash would exceed the max packet size considering base_size
        if len(packet) + len(hash_bytes) + base_size > max_packet_size:
            break  # Stop adding hashes if the packet would become too large
        packet += hash_bytes
        included_hashes.append(info_hash)

    if not included_hashes:
        raise ValueError("No hashes could be included in the packet without exceeding the size limit.")

    return packet, included_hashes, transaction_id


async def scrape_udp(parsed_tracker: parse.ParseResult, info_hashes: list[str], timeout: int):
    con_req, con_trans_id = udp_create_connection_request()
    results = {}
    remaining_hashes = list(info_hashes)  # Start with all hashes

    async def on_con_response(data):
        action, trans_id, connection_id = struct.unpack_from("!IIq", data)
        if action != 0 or trans_id != con_trans_id:
            logging.error(f"Invalid connection response from {parsed_tracker.geturl()}")
            return

        nonlocal remaining_hashes  # Reference the non-local variable defined in outer scope

        while remaining_hashes:
            try:
                scrape_req, included_hashes, trans_id = udp_create_scrape_request(connection_id, remaining_hashes)
                remaining_hashes = [h for h in remaining_hashes if h not in included_hashes]  # Update remaining_hashes safely
                await send_udp_request(parsed_tracker, scrape_req, lambda response: on_scrape_response(response, included_hashes, trans_id), on_error, timeout)
            except ValueError as e:
                logging.error(f"Error creating UDP scrape request: {e}")
                break

    async def on_scrape_response(data, included_hashes, trans_id):
        action, resp_trans_id = struct.unpack_from("!II", data)
        if action != 2 or resp_trans_id != trans_id:
            logging.error(f"Invalid scrape response from {parsed_tracker.geturl()}")
            return

        offset = 8  # Skip action and transaction ID
        expected_length_per_hash = 12  # 4 bytes each for seeds, completed, leeches
        local_results = {}

        for info_hash in included_hashes:
            if offset + expected_length_per_hash > len(data):
                logging.error(f"Not enough data to unpack results for hash: {info_hash}. Data: {data} Data length: {len(data)}, required: {offset + expected_length_per_hash}")
                continue  # Use continue to process next hashes if possible

            seeds, completed, leeches = struct.unpack_from("!iii", data, offset)
            readable_hash = binascii.b2a_hex(binascii.a2b_hex(info_hash)).decode("utf-8")
            local_results[readable_hash] = {
                "tracker_url": parsed_tracker.geturl(),
                "seeders": seeds,
                "peers": leeches,
                "complete": completed,
            }
            offset += expected_length_per_hash

        results.update(local_results)

    def on_error(error_message):
        logging.error(f"Error: {error_message}")

    # Perform the initial connection request
    await send_udp_request(parsed_tracker, con_req, on_con_response, on_error, timeout)
    return results
