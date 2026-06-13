# Smart Recommendation Engine

A hybrid collaborative and content-based recommendation system serving 2M+ users.

## Overview

The Smart Recommendation Engine combines matrix factorization with deep neural networks for content understanding to deliver personalized recommendations at scale. Built for DataSphere Technologies' e-commerce platform, it improved click-through rate by 35% compared to the previous rule-based system.

## Architecture

The system has three main components: a Collaborative Filtering module using matrix factorization (ALS) for user-item interaction patterns, a Content-Based module using a transformer-based encoder for item feature understanding, and a Hybrid Ranker that combines both signals using a learned weighting model. Real-time inference is served via FastAPI with Redis caching for sub-50ms response times.

## Tech Stack

- **Deep Learning:** PyTorch for model training and inference
- **Serving:** FastAPI with Redis caching
- **Training Infrastructure:** AWS SageMaker for distributed training
- **Feature Store:** Redis for real-time features, S3 for batch features
- **Monitoring:** Weights & Biases for experiment tracking, Prometheus for serving metrics
- **Data Pipeline:** Apache Spark for feature engineering, Apache Airflow for orchestration

## Installation

```bash
git clone https://github.com/ofirohan/smart-recsys
cd smart-recsys
pip install -r requirements.txt
python setup.py install
```

## Usage

The system exposes a REST API for real-time recommendations. Configure user and item feature sources in config.yaml. Training pipelines run on SageMaker with configurable hyperparameters.

## Key Features

- Hybrid collaborative + content-based recommendation
- Real-time inference with sub-50ms latency via Redis caching
- A/B testing framework for model comparison
- Distributed training on AWS SageMaker
- Automatic model retraining on data drift detection
- 35% improvement in click-through rate over rule-based baseline

## Performance

Serving 2M+ users with sub-50ms p99 latency. Model training completes in 4 hours on 4x V100 GPUs. Daily retraining pipeline runs automatically via Airflow with drift detection.

## Contributing

Contributions welcome. Please follow the ML engineering guidelines in CONTRIBUTING.md. All model changes require offline evaluation before deployment.

## License

Proprietary — DataSphere Technologies
