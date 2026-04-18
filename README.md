# Edge Node Service

A containerised edge sensor-processing service that demonstrates the latency
benefits of edge computing versus a simulated cloud deployment.

The service ingests sensor telemetry over HTTP, performs local statistical
processing, and returns a compact summary. A second instance of the same
service runs under simulated wide-area network conditions (added latency and
jitter via `tc netem`) to represent a cloud deployment. A benchmark harness
compares the two under identical workloads.

## Status

🚧 Work in progress.

## Quick start

```bash
docker compose up --build