# Edge Node Service

A containerised HTTP service that simulates an edge node processing sensor readings locally.

The service accepts sensor readings over HTTP, processes them immediately on the node, and returns a compact result containing updated running statistics and alert flags. A second instance of the same service runs under simulated wide-area network conditions using `tc netem`, allowing direct comparison between local edge processing and a remote-style deployment.

## Status

Completed practical task submission.

## Quick start

### Requirements

- Docker Desktop
- Docker Compose
- Python 3.12+ (only needed if you want to run the benchmark script outside containers)

### Start the full stack

```bash
docker compose up --build

edge-node on http://127.0.0.1:8000
edge-remote on http://127.0.0.1:8001
prometheus on http://127.0.0.1:9090
grafana on http://127.0.0.1:3000
API
Health check
curl http://127.0.0.1:8000/health
Submit a sensor reading
curl -s -X POST http://127.0.0.1:8000/data \
  -H "Content-Type: application/json" \
  -d "{\"sensor_id\":\"temp-99\",\"value\":24.7,\"timestamp\":\"2024-01-15T10:30:00Z\"}" | python -m json.tool
Example payload
{
  "sensor_id": "temp-99",
  "value": 24.7,
  "timestamp": "2024-01-15T10:30:00Z"
}
Example response
{
  "sensor_id": "temp-99",
  "input_value": 24.7,
  "received_timestamp": "2024-01-15T10:30:00Z",
  "processed_at": "2026-04-19T18:23:28.946966Z",
  "count": 1,
  "running_mean": 24.7,
  "min_value": 24.7,
  "max_value": 24.7,
  "anomaly": false,
  "threshold_alert": false
}
What the service does

For each sensor_id, the service keeps simple in-memory statistics:

reading count
running mean
minimum value seen
maximum value seen
anomaly flag
threshold alert flag

The processing is intentionally simple. The goal of the task is showing why processing on the edge can reduce latency compared with sending the same data to a remote environment.

Architecture

The project uses:

FastAPI for a lightweight HTTP service
Docker + Docker Compose for reproducible local deployment
Prometheus + Grafana for observability
Python benchmark script for repeatable latency measurements
tc netem in the simulated remote container to add network delay and jitter
Service layout
edge-node — local edge service
edge-remote — same service, but with artificial network delay applied using tc netem
prometheus — metrics collection
grafana — dashboard visualisation

I used Python and FastAPI because they are quick to build with, easy to read, and suitable for a lightweight HTTP edge service. Docker Compose made it easy to run both the local and simulated remote versions with the same application code, which isolates the network effect. The processing logic is deliberately minimal so the latency comparison reflects the edge-vs-remote difference rather than model complexity.

Prometheus and Grafana are included as observability tools so the service can expose and inspect request-level metrics. The main latency comparison reported in this README, however, comes directly from the benchmark script output.

Reproducing the latency experiment

The key idea is to compare the same processing logic in two places:

local edge service on port 8000
simulated remote service on port 8001

The remote service uses tc netem to add delay and jitter to its network interface.

Benchmark commands

Local edge:

python scripts/benchmark.py --url http://127.0.0.1:8000/data --requests 100 --concurrency 10

Simulated remote:

python scripts/benchmark.py --url http://127.0.0.1:8001/data --requests 100 --concurrency 10
Hardware / environment

Benchmarks were run on:

CPU: Intel Core Ultra 5 125U, 12 cores, 14 logical processors
RAM: 16 GB
OS: Microsoft Windows 11 Pro
System type: x64
Docker: v4.69.0
Python: 3.12.7
Results
Local edge (http://127.0.0.1:8000/data)
Throughput: 196.11 req/s
P50 latency: 45.17 ms
P95 latency: 71.05 ms
P99 latency: 83.80 ms
Simulated remote (http://127.0.0.1:8001/data)
Throughput: 52.40 req/s
P50 latency: 177.93 ms
P95 latency: 255.72 ms
P99 latency: 285.07 ms
Raw benchmark output

Local:

=== Benchmark results ===
URL:           http://127.0.0.1:8000/data
Requests:      100
Concurrency:   10
Sensor ID:     temp-01
Success:       100
Failure:       0
Total time:    0.510 s
Throughput:    196.11 req/s

=== Latency (ms) ===
Min:           16.47
Mean:          46.62
Median:        45.17
P50:           45.17
P95:           71.05
P99:           83.80
Max:           84.78

Remote:

=== Benchmark results ===
URL:           http://127.0.0.1:8001/data
Requests:      100
Concurrency:   10
Sensor ID:     temp-01
Success:       100
Failure:       0
Total time:    1.908 s
Throughput:    52.40 req/s

=== Latency (ms) ===
Min:           137.64
Mean:          184.12
Median:        177.93
P50:           177.93
P95:           255.72
P99:           285.07
Max:           287.18
Interpretation

The experiment shows a clear edge-computing benefit. When the same sensor processing runs locally, latency is much lower and throughput is much higher than when the same request is sent to a simulated remote environment with added network delay.

In this run, the local edge service achieved 196.11 requests per second with a median latency of 45.17 ms, while the simulated remote service dropped to 52.40 requests per second with a median latency of 177.93 ms. This shows that even simple sensor processing benefits from being performed close to the data source instead of being sent over a slower network path.

Retrospective

The biggest challenge was keeping the project aligned with the actual task while also building a benchmark that was easy to reproduce. At one point the project drifted in a different direction, so I had to refocus it on sensor data, local processing, and a clear local vs remote comparison. Another important part was making sure both environments used the same code, so that the difference in results came from network conditions and not from different logic.

Next steps

If I had more time, I would test with a wider range of sensor data, add clearer charts for the benchmark results, and try more `tc netem` profiles such as packet loss or different delay settings. I would also add automated tests and CI checks to make the project easier to validate.
Notes
The benchmark script generates synthetic sensor readings automatically.
The local and remote services run the same code.
The remote service is slower because of artificial delay and jitter added with tc netem.
Prometheus and Grafana are included for observability, but the latency numbers reported above come from the benchmark script output.