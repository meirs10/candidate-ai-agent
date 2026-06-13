# Real-Time Event Enrichment Pipeline
High-throughput streaming pipeline for mobile attribution event enrichment.
## Overview
Processes 1.2M events/second for real-time mobile attribution enrichment at AppsFlyer. Ingests raw attribution events, enriches with device/geo/campaign metadata, applies fraud detection rules, and routes to analytics and reporting systems.
## Architecture
Three-stage pipeline: Kafka ingestion layer with 500+ partitions, Flink stateful processing with RocksDB state backend for sessionization and deduplication, and ClickHouse sink for real-time OLAP queries. Multi-region deployment with Kafka MirrorMaker 2 for cross-region replication.
## Tech Stack
- **Language:** Java 17, Kotlin
- **Streaming:** Apache Kafka, Apache Flink
- **Storage:** ClickHouse, Redis, S3
- **Infrastructure:** Kubernetes (EKS), Terraform
- **Monitoring:** Prometheus, Grafana, Datadog
- **Serialization:** Protocol Buffers, Avro
## Installation
```bash
git clone https://github.com/talbendavid/event-enrichment
cd event-enrichment
./gradlew build
helm install pipeline ./charts/pipeline
```
## Key Features
- 1.2M events/second throughput with sub-100ms end-to-end latency
- Exactly-once processing semantics with Kafka transactions
- Stateful sessionization with 24-hour windows
- Real-time fraud detection with rule engine
- Auto-scaling based on consumer lag metrics
- Multi-region active-active deployment
## Performance
Sustained throughput of 1.2M events/second. P99 end-to-end latency under 100ms. Handles 100B+ daily events across all pipelines. Zero data loss during region failovers.
## License
Proprietary — AppsFlyer
