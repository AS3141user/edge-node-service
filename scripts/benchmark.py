#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

import requests


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]

    k = (len(sorted_values) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)

    if f == c:
        return sorted_values[f]

    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def build_payload(i: int, sensor_id: str, base_value: float) -> dict[str, object]:
    timestamp = datetime.now(timezone.utc) + timedelta(seconds=i)
    value = base_value + (i % 10) * 0.5

    return {
        "sensor_id": sensor_id,
        "value": value,
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
    }


def single_request(url: str, payload: dict[str, object], timeout: float) -> tuple[bool, float, int]:
    start = time.perf_counter()

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=timeout,
        )
        latency_ms = (time.perf_counter() - start) * 1000.0
        return response.ok, latency_ms, response.status_code
    except requests.RequestException:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return False, latency_ms, 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the edge-node /data endpoint.")
    parser.add_argument("--url", default="http://127.0.0.1:8000/data", help="Processing endpoint URL")
    parser.add_argument("--requests", type=int, default=100, help="Total number of requests")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds")
    parser.add_argument("--sensor-id", default="temp-01", help="Sensor ID to use in generated payloads")
    parser.add_argument("--base-value", type=float, default=24.0, help="Starting sensor value")
    args = parser.parse_args()

    latencies: list[float] = []
    success_count = 0
    failure_count = 0
    status_counts: dict[int, int] = {}

    payloads = [build_payload(i, args.sensor_id, args.base_value) for i in range(args.requests)]

    overall_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(single_request, args.url, payload, args.timeout)
            for payload in payloads
        ]

        for future in as_completed(futures):
            ok, latency_ms, status_code = future.result()
            latencies.append(latency_ms)
            status_counts[status_code] = status_counts.get(status_code, 0) + 1

            if ok:
                success_count += 1
            else:
                failure_count += 1

    total_time_s = time.perf_counter() - overall_start

    latencies_sorted = sorted(latencies)
    throughput = len(latencies) / total_time_s if total_time_s > 0 else 0.0

    print("\n=== Benchmark results ===")
    print(f"URL:           {args.url}")
    print(f"Requests:      {args.requests}")
    print(f"Concurrency:   {args.concurrency}")
    print(f"Sensor ID:     {args.sensor_id}")
    print(f"Success:       {success_count}")
    print(f"Failure:       {failure_count}")
    print(f"Total time:    {total_time_s:.3f} s")
    print(f"Throughput:    {throughput:.2f} req/s")

    if latencies_sorted:
        print("\n=== Latency (ms) ===")
        print(f"Min:           {min(latencies_sorted):.2f}")
        print(f"Mean:          {statistics.mean(latencies_sorted):.2f}")
        print(f"Median:        {statistics.median(latencies_sorted):.2f}")
        print(f"P50:           {percentile(latencies_sorted, 0.50):.2f}")
        print(f"P95:           {percentile(latencies_sorted, 0.95):.2f}")
        print(f"P99:           {percentile(latencies_sorted, 0.99):.2f}")
        print(f"Max:           {max(latencies_sorted):.2f}")

    print("\n=== Status codes ===")
    for code, count in sorted(status_counts.items()):
        label = "EXCEPTION" if code == 0 else str(code)
        print(f"{label}: {count}")


if __name__ == "__main__":
    main()