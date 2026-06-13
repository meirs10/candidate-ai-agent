import json
from pathlib import Path

# Load existing Ofir data
_DATA_DIR = Path(__file__).parent
_existing_seed = json.loads((_DATA_DIR / "candidate_seed.json").read_text(encoding="utf-8"))
_existing_cv = (_DATA_DIR / "synthetic_resume.md").read_text(encoding="utf-8")
_existing_golden = json.loads((_DATA_DIR / "golden_dataset.json").read_text(encoding="utf-8"))

SEED = _existing_seed

CV = _existing_cv

README = """# Smart Recommendation Engine

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
"""

REC = """# Letter of Recommendation — Ofir Ohan

**From:** Dr. Yael Stern, Director of Engineering at DataSphere Technologies
**Date:** May 10, 2026

---

To Whom It May Concern,

I am writing to enthusiastically recommend Ofir Ohan, who has been an outstanding member of our ML engineering team at DataSphere Technologies for over four years. Ofir joined us as an ML engineer and has consistently exceeded expectations in every aspect of his work.

Ofir's most significant contribution has been the development of our Smart Recommendation Engine, which serves over 2 million users and improved click-through rates by 35%. He designed the hybrid architecture combining collaborative filtering with deep content understanding, demonstrating both research depth and engineering pragmatism. This system processes millions of requests daily with sub-50ms latency.

Equally impressive is his work on the real-time fraud detection pipeline, which processes 10,000 transactions per second with sub-100ms inference latency. Ofir architected the entire streaming ML pipeline using Kafka and PyTorch, showing his ability to deliver under strict performance constraints.

As a team leader, Ofir has been instrumental in growing our ML team. He leads 3 engineers with a focus on code quality, mentoring, and knowledge sharing. He conducts thorough code reviews, runs sprint planning, and has created onboarding materials that significantly reduced ramp-up time for new hires. His contribution to LangChain's open-source project (Hebrew text processing) reflects his commitment to the broader community.

I recommend Ofir without hesitation for a Senior Machine Learning Engineer role. He is a rare engineer who combines deep ML expertise with production engineering skills and strong leadership abilities.

Sincerely,

**Dr. Yael Stern**
Director of Engineering
DataSphere Technologies
yael.stern@datasphere.io
"""

GOLDEN = _existing_golden
