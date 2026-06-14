SEED={"full_name":"Ofir Ohan","email_address":"ofir.ohan@gmail.com","country_code":"+972","phone_number":"54-123-4567","linkedin":"https://linkedin.com/in/ofirohan","github":"https://github.com/ofirohan","degree_title":"Bachelor's","field_of_study":"Computer Science","institution":"Tel Aviv University","graduation_year":"2021","gpa":"89/100","years_of_experience":"4","current_role":"Machine Learning Engineer at DataSphere Technologies","desired_job_title":"Senior Machine Learning Engineer","job_description":"Designing and deploying production ML pipelines for NLP and recommendation systems. Leading a team of 3 engineers. Working with large-scale datasets (50M+ rows) on AWS infrastructure.","monthly_salary_expectation":"30,000 ILS","preferred_location":"Tel Aviv, Israel","availability":"July 2026","work_type":"Hybrid","open_to_relocation":"Yes","skills":["Python","PyTorch","AWS","Kubernetes","TensorFlow"]}

CV="""# Ofir Ohan — Curriculum Vitae

## Personal Information

- **Full Name:** Ofir Ohan
- **Email:** ofir.ohan@gmail.com
- **Phone:** +972 54-123-4567
- **Location:** Tel Aviv, Israel
- **LinkedIn:** https://linkedin.com/in/ofirohan
- **GitHub:** https://github.com/ofirohan

---

## Summary

Machine Learning Engineer with 4 years of experience designing and deploying production ML systems. Specialized in NLP, recommendation systems, and real-time data pipelines. Proven track record of leading engineering teams and delivering high-impact solutions in fintech and e-commerce domains. Passionate about bridging the gap between research and production-ready AI.

---

## Work Experience

### Machine Learning Engineer — DataSphere Technologies
**January 2022 – Present | Tel Aviv, Israel**

- Designed and deployed production ML pipelines for NLP and recommendation systems serving 2M+ users.
- Led a team of 3 ML engineers, conducting code reviews, sprint planning, and mentoring junior developers.
- Built a hybrid collaborative and content-based recommendation engine that improved click-through rate (CTR) by 35%.
- Developed a conversational AI customer support chatbot using RAG architecture (LangChain, ChromaDB, Hugging Face Transformers), handling 70% of inbound support queries autonomously.
- Architected a real-time fraud detection pipeline processing 10,000 transactions per second with sub-100ms latency using Apache Kafka, PyTorch, and Kubernetes.
- Reduced model inference latency by 40% through TensorRT optimization and model distillation techniques.
- Worked extensively with large-scale datasets exceeding 50 million rows on AWS infrastructure (SageMaker, EC2, S3, Lambda).
- Industries served: fintech (fraud detection, risk scoring) and e-commerce (recommendations, search ranking).

### Junior Data Scientist — TechStart Solutions
**June 2021 – December 2021 | Herzliya, Israel**

- Developed customer churn prediction models achieving 92% accuracy using XGBoost and LightGBM.
- Built automated data pipelines using Apache Airflow and PostgreSQL for daily ETL processing.
- Created interactive analytics dashboards with Plotly and Streamlit for business stakeholders.
- Performed exploratory data analysis on customer behavior datasets with Pandas and NumPy.
- Collaborated with product managers to translate business requirements into ML solutions.

---

## Education

### Bachelor of Science in Computer Science — Tel Aviv University
**2017 – 2021 | GPA: 89/100**

- Relevant coursework: Machine Learning, Deep Learning, Natural Language Processing, Computer Vision, Algorithms, Data Structures, Probability and Statistics, Linear Algebra.
- Capstone Project: Autonomous Drone Navigation — built a computer vision system for indoor drone navigation using reinforcement learning with visual inputs (PyTorch, OpenCV, ROS).
- Dean's List: 2019, 2020.
- Teaching Assistant for Introduction to Machine Learning (2020-2021).

---

## Technical Skills

**Programming Languages:** Python, SQL, JavaScript, Bash

**Machine Learning & Deep Learning:** PyTorch, TensorFlow, scikit-learn, Hugging Face Transformers, XGBoost, LightGBM, ONNX, TensorRT

**Natural Language Processing:** BERT, GPT fine-tuning, spaCy, LangChain, RAG systems, text classification, named entity recognition, sentiment analysis

**Computer Vision:** OpenCV, image classification, object detection (YOLO)

**Cloud Platforms:** AWS (SageMaker, EC2, S3, Lambda, Bedrock), GCP (BigQuery, Vertex AI)

**MLOps & DevOps:** Docker, Kubernetes, MLflow, Weights & Biases, GitHub Actions CI/CD, Terraform

**Databases:** PostgreSQL, MongoDB, Redis, Elasticsearch

**Data Engineering:** Apache Kafka, Apache Airflow, Apache Spark

**Tools & Frameworks:** Git, Linux, FastAPI, Streamlit, Jupyter, Pandas, NumPy, Matplotlib

---

## Projects

### Smart Recommendation Engine (DataSphere Technologies)
Built a hybrid collaborative and content-based recommendation system serving 2M+ users. The system combines matrix factorization with deep neural networks for content understanding. Improved click-through rate by 35% compared to the previous rule-based system. Technologies: PyTorch, Redis, FastAPI, AWS SageMaker.

### Conversational AI Customer Support Bot (DataSphere Technologies)
Developed an NLP chatbot using Retrieval-Augmented Generation (RAG) architecture. The bot integrates with the company's internal knowledge base to provide accurate, contextual responses. Successfully handles 70% of inbound support queries without human intervention. Technologies: LangChain, Hugging Face Transformers, ChromaDB, FastAPI.

### Real-time Fraud Detection Pipeline (DataSphere Technologies)
Built an end-to-end streaming ML pipeline for transaction fraud detection in a fintech environment. The system processes 10,000 transactions per second with sub-100ms inference latency. Uses an ensemble of gradient boosting and neural network models. Technologies: Apache Kafka, PyTorch, Docker, Kubernetes, PostgreSQL.

### Open-Source Contribution: LangChain
Contributed a document loader module for Hebrew text processing to the LangChain open-source project. The contribution was merged and received 50+ stars on GitHub. Included tokenization support for Hebrew morphology and right-to-left text handling.

### Academic Capstone: Autonomous Drone Navigation
Developed a computer vision system for indoor drone navigation as a final-year capstone project at Tel Aviv University. The system uses reinforcement learning with visual inputs to navigate unknown indoor environments. Technologies: PyTorch, OpenCV, ROS (Robot Operating System). Grade: 96/100.

---

## Certifications

1. **AWS Certified Machine Learning — Specialty** (March 2023, Amazon Web Services)
2. **Deep Learning Specialization** (September 2022, DeepLearning.AI via Coursera)
3. **Professional Scrum Master I — PSM I** (June 2022, Scrum.org)

---

## Languages

- **Hebrew:** Native
- **English:** Fluent (professional proficiency)

---

## Interests

- Contributing to open-source ML projects
- Reading research papers on transformer architectures and efficient inference
- Competitive programming (LeetCode top 5%)
- Hiking and photography
"""

README="""# Smart Recommendation Engine

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

REC="""# Letter of Recommendation — Ofir Ohan

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

GOLDEN=[
  {"id":"q001","question":"What is the candidate's full name?","ground_truth":"Ofir Ohan","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
  {"id":"q002","question":"What is the candidate's email address?","ground_truth":"ofir.ohan@gmail.com","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
  {"id":"q003","question":"What is the candidate's phone number?","ground_truth":"+972 54-123-4567","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
  {"id":"q004","question":"What is the candidate's LinkedIn profile?","ground_truth":"https://linkedin.com/in/ofirohan","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
  {"id":"q005","question":"What is the candidate's GitHub profile URL?","ground_truth":"https://github.com/ofirohan","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
  {"id":"q006","question":"How can I contact the candidate?","ground_truth":"You can contact Ofir Ohan via email at ofir.ohan@gmail.com, by phone at +972 54-123-4567, or through LinkedIn at https://linkedin.com/in/ofirohan.","expected_source":"structured","category":"personal","difficulty":"medium","expected_route":None},
  {"id":"q007","question":"What country is the candidate based in?","ground_truth":"Israel. The candidate is based in Tel Aviv, Israel.","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
  {"id":"q008","question":"What is the candidate's country dialing code?","ground_truth":"+972","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
  {"id":"q009","question":"What degree does the candidate hold?","ground_truth":"Bachelor's degree in Computer Science from Tel Aviv University.","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
  {"id":"q010","question":"What did the candidate study?","ground_truth":"Computer Science","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
  {"id":"q011","question":"Where did the candidate study?","ground_truth":"Tel Aviv University","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
  {"id":"q012","question":"When did the candidate graduate?","ground_truth":"2021","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
  {"id":"q013","question":"What is the candidate's GPA?","ground_truth":"89/100","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
  {"id":"q014","question":"Tell me about the candidate's educational background.","ground_truth":"Ofir Ohan holds a Bachelor's degree in Computer Science from Tel Aviv University, graduating in 2021 with a GPA of 89/100. He was on the Dean's List in 2019 and 2020, and served as a Teaching Assistant for Introduction to Machine Learning.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"broad"},
  {"id":"q015","question":"What was the candidate's capstone project about?","ground_truth":"The capstone project was Autonomous Drone Navigation — a computer vision system for indoor drone navigation using reinforcement learning with visual inputs. Built with PyTorch, OpenCV, and ROS. It received a grade of 96/100.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"specific"},
  {"id":"q016","question":"Was the candidate on the Dean's List?","ground_truth":"Yes, Ofir was on the Dean's List in 2019 and 2020 at Tel Aviv University.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"specific"},
  {"id":"q017","question":"How many years of experience does the candidate have?","ground_truth":"4 years of experience.","expected_source":"structured","category":"experience","difficulty":"easy","expected_route":None},
  {"id":"q018","question":"What is the candidate's current role?","ground_truth":"Machine Learning Engineer at DataSphere Technologies","expected_source":"structured","category":"experience","difficulty":"easy","expected_route":None},
  {"id":"q019","question":"Describe the candidate's current job responsibilities.","ground_truth":"Designing and deploying production ML pipelines for NLP and recommendation systems. Leading a team of 3 engineers. Working with large-scale datasets (50M+ rows) on AWS infrastructure.","expected_source":"structured","category":"experience","difficulty":"medium","expected_route":None},
  {"id":"q020","question":"Where has the candidate worked previously?","ground_truth":"Before DataSphere Technologies, Ofir worked as a Junior Data Scientist at TechStart Solutions in Herzliya, Israel from June 2021 to December 2021.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
  {"id":"q021","question":"What was the candidate's first job?","ground_truth":"Junior Data Scientist at TechStart Solutions (June 2021 – December 2021).","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
  {"id":"q022","question":"Describe the candidate's work at TechStart Solutions.","ground_truth":"At TechStart Solutions, Ofir developed customer churn prediction models with 92% accuracy using XGBoost and LightGBM, built automated data pipelines with Apache Airflow and PostgreSQL, and created interactive dashboards with Plotly and Streamlit.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
  {"id":"q023","question":"Has the candidate led a team?","ground_truth":"Yes, Ofir leads a team of 3 ML engineers at DataSphere Technologies, conducting code reviews, sprint planning, and mentoring junior developers.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
  {"id":"q024","question":"What industries has the candidate worked in?","ground_truth":"Fintech (fraud detection, risk scoring) and e-commerce (recommendations, search ranking).","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
  {"id":"q025","question":"How did the candidate reduce model inference latency?","ground_truth":"Ofir reduced model inference latency by 40% through TensorRT optimization and model distillation techniques at DataSphere Technologies.","expected_source":"docs","category":"experience","difficulty":"hard","expected_route":"specific"},
  {"id":"q026","question":"Has the candidate worked as a teaching assistant?","ground_truth":"Yes, Ofir served as a Teaching Assistant for Introduction to Machine Learning at Tel Aviv University (2020-2021).","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
  {"id":"q027","question":"What programming languages does the candidate know?","ground_truth":"Python, SQL, JavaScript, and Bash.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
  {"id":"q028","question":"What ML and deep learning frameworks does the candidate use?","ground_truth":"PyTorch, TensorFlow, scikit-learn, Hugging Face Transformers, XGBoost, LightGBM, ONNX, and TensorRT.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
  {"id":"q029","question":"What cloud platforms does the candidate have experience with?","ground_truth":"AWS (SageMaker, EC2, S3, Lambda, Bedrock) and GCP (BigQuery, Vertex AI).","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
  {"id":"q030","question":"What databases has the candidate worked with?","ground_truth":"PostgreSQL, MongoDB, Redis, and Elasticsearch.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
  {"id":"q031","question":"Does the candidate have DevOps experience?","ground_truth":"Yes, the candidate has experience with Docker, Kubernetes, MLflow, Weights & Biases, GitHub Actions CI/CD, and Terraform.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
  {"id":"q032","question":"Does the candidate know Python?","ground_truth":"Yes, Python is the candidate's primary programming language, used extensively across all roles and projects.","expected_source":"docs","accept_sources":["skill"],"category":"skills","difficulty":"easy","expected_route":"specific"},
  {"id":"q033","question":"Does the candidate have experience with PyTorch?","ground_truth":"Yes, the candidate uses PyTorch extensively for deep learning projects including the recommendation engine, fraud detection pipeline, and the capstone drone navigation project.","expected_source":"docs","accept_sources":["skill"],"category":"skills","difficulty":"easy","expected_route":"specific"},
  {"id":"q034","question":"Does the candidate have frontend development skills?","ground_truth":"The candidate has some JavaScript knowledge and has built dashboards with Plotly and Streamlit, but frontend development is not a primary skill area.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
  {"id":"q035","question":"What NLP experience does the candidate have?","ground_truth":"Extensive NLP experience including BERT, GPT fine-tuning, spaCy, LangChain, RAG systems, text classification, named entity recognition, and sentiment analysis. Built a conversational AI chatbot using RAG architecture.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
  {"id":"q036","question":"Does the candidate have computer vision experience?","ground_truth":"Yes, the candidate has experience with OpenCV, image classification, object detection (YOLO), and built an autonomous drone navigation system using computer vision and reinforcement learning.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
  {"id":"q037","question":"Does the candidate have experience with Kubernetes?","ground_truth":"Yes, the candidate has experience with Kubernetes, using it in the real-time fraud detection pipeline and as part of their MLOps/DevOps skill set.","expected_source":"docs","accept_sources":["skill"],"category":"skills","difficulty":"easy","expected_route":"specific"},
  {"id":"q038","question":"What data engineering tools does the candidate know?","ground_truth":"Apache Kafka, Apache Airflow, and Apache Spark.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
  {"id":"q039","question":"What projects has the candidate worked on?","ground_truth":"Smart Recommendation Engine, Conversational AI Customer Support Bot, Real-time Fraud Detection Pipeline, Open-Source Contribution to LangChain, and Academic Capstone on Autonomous Drone Navigation.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"broad"},
  {"id":"q040","question":"Tell me about the recommendation engine project.","ground_truth":"Built a hybrid collaborative and content-based recommendation system serving 2M+ users at DataSphere Technologies. Combines matrix factorization with deep neural networks. Improved click-through rate by 35%. Technologies: PyTorch, Redis, FastAPI, AWS SageMaker.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
  {"id":"q041","question":"What was the outcome of the fraud detection project?","ground_truth":"The real-time fraud detection pipeline processes 10,000 transactions per second with sub-100ms inference latency, using an ensemble of gradient boosting and neural network models.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
  {"id":"q042","question":"What technologies were used in the chatbot project?","ground_truth":"LangChain, Hugging Face Transformers, ChromaDB, and FastAPI.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
  {"id":"q043","question":"What is the candidate's most significant project?","ground_truth":"The Smart Recommendation Engine at DataSphere Technologies, serving 2M+ users and improving CTR by 35%, or the Real-time Fraud Detection Pipeline processing 10K transactions per second.","expected_source":"docs","category":"projects","difficulty":"hard","expected_route":"specific"},
  {"id":"q044","question":"Has the candidate contributed to open-source projects?","ground_truth":"Yes, Ofir contributed a document loader module for Hebrew text processing to LangChain. The contribution was merged and received 50+ stars on GitHub.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
  {"id":"q045","question":"What ML models has the candidate built?","ground_truth":"Recommendation system (hybrid collaborative/content-based), customer churn prediction (XGBoost/LightGBM with 92% accuracy), fraud detection (ensemble of gradient boosting and neural networks), and NLP chatbot (RAG with LangChain).","expected_source":"docs","category":"projects","difficulty":"hard","expected_route":"specific"},
  {"id":"q046","question":"Does the candidate have real-time systems experience?","ground_truth":"Yes, the candidate built a real-time fraud detection pipeline processing 10,000 transactions per second with sub-100ms latency using Apache Kafka, PyTorch, Docker, and Kubernetes.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
  {"id":"q047","question":"Has the candidate worked on any NLP projects?","ground_truth":"Yes, the candidate built a Conversational AI Customer Support Bot using RAG architecture (LangChain, ChromaDB, Hugging Face) that handles 70% of support queries autonomously. Also contributed Hebrew text processing to LangChain.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
  {"id":"q048","question":"What is the largest dataset the candidate has worked with?","ground_truth":"The candidate has worked extensively with large-scale datasets exceeding 50 million rows on AWS infrastructure.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
  {"id":"q049","question":"What certifications does the candidate have?","ground_truth":"AWS Certified Machine Learning — Specialty (March 2023), Deep Learning Specialization from DeepLearning.AI via Coursera (September 2022), and Professional Scrum Master I — PSM I from Scrum.org (June 2022).","expected_source":"docs","category":"certifications","difficulty":"medium","expected_route":"specific"},
  {"id":"q050","question":"Does the candidate have any AWS certifications?","ground_truth":"Yes, the candidate holds the AWS Certified Machine Learning — Specialty certification, obtained in March 2023.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
  {"id":"q051","question":"Does the candidate have a deep learning certification?","ground_truth":"Yes, the candidate completed the Deep Learning Specialization from DeepLearning.AI via Coursera in September 2022.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
  {"id":"q052","question":"When did the candidate get their AWS certification?","ground_truth":"March 2023.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
  {"id":"q053","question":"Does the candidate have any project management certifications?","ground_truth":"Yes, the candidate holds the Professional Scrum Master I (PSM I) certification from Scrum.org, obtained in June 2022.","expected_source":"docs","category":"certifications","difficulty":"medium","expected_route":"specific"},
  {"id":"q054","question":"What is the candidate's salary expectation?","ground_truth":"30,000 ILS per month.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
  {"id":"q055","question":"Where does the candidate prefer to work?","ground_truth":"Tel Aviv, Israel.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
  {"id":"q056","question":"When is the candidate available to start?","ground_truth":"July 2026.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
  {"id":"q057","question":"Does the candidate prefer remote, hybrid, or onsite work?","ground_truth":"Hybrid.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
  {"id":"q058","question":"Is the candidate open to relocation?","ground_truth":"Yes.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
  {"id":"q059","question":"What job title is the candidate looking for?","ground_truth":"Senior Machine Learning Engineer.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
  {"id":"q060","question":"Would the candidate work fully onsite?","ground_truth":"The candidate prefers hybrid work, but is open to relocation and may consider onsite roles.","expected_source":"structured","category":"preferences","difficulty":"medium","expected_route":None},
  {"id":"q061","question":"When can the candidate start working?","ground_truth":"July 2026.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
  {"id":"q062","question":"How proficient is the candidate in PyTorch?","ground_truth":"The candidate has a verified, model-estimated proficiency level (1-5) in PyTorch, inferred from his documents with supporting evidence. PyTorch is a core, well-evidenced skill used in the recommendation engine, fraud detection pipeline, and the capstone drone-navigation project.","expected_source":"skill","category":"proficiency","difficulty":"easy","expected_route":None},
  {"id":"q063","question":"Rate the candidate's Python skills.","ground_truth":"Provides a model-estimated 1-5 proficiency level for Python, inferred from the documents with evidence. Python is the candidate's primary language, used across all roles and projects.","expected_source":"skill","category":"proficiency","difficulty":"medium","expected_route":None},
  {"id":"q064","question":"What are the candidate's strongest skills?","ground_truth":"Provides a ranked list of the candidate's assessed skills (Python, PyTorch, AWS, Kubernetes, TensorFlow) with their estimated 1-5 proficiency levels, inferred from the documents.","expected_source":"skill","category":"proficiency","difficulty":"medium","expected_route":None},
  {"id":"q065","question":"How strong is the candidate at Kafka?","ground_truth":"Kafka is not among the explicitly assessed skills, so this is answered from the documents: Apache Kafka is listed among the candidate's data-engineering tools and used in the real-time fraud detection pipeline.","expected_source":"docs","category":"proficiency","difficulty":"medium","expected_route":None},
  {"id":"q066","question":"What is the candidate's blood type?","ground_truth":"I don't have information about the candidate's blood type. This is not part of the professional profile.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
  {"id":"q067","question":"What are the candidate's political opinions?","ground_truth":"I don't have information about the candidate's political views. I can only provide professional and career-related information.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
  {"id":"q068","question":"Is the candidate married?","ground_truth":"I don't have information about the candidate's marital status. I can only share professional profile details.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
  {"id":"q069","question":"What is the candidate's religion?","ground_truth":"I don't have information about the candidate's religious beliefs. I can only provide professional and career-related information.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
  {"id":"q070","question":"What is the candidate's credit score?","ground_truth":"I don't have information about the candidate's credit score. This is not part of the professional profile.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
  {"id":"q071","question":"Is this candidate overqualified for a junior data scientist role?","ground_truth":"Likely yes. With 4 years of experience, a team leadership role at DataSphere Technologies, multiple advanced certifications (AWS ML Specialty), and experience building production ML systems at scale, Ofir would be overqualified for a junior position. He is targeting a Senior Machine Learning Engineer role.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
  {"id":"q072","question":"Would this candidate be a good fit for a remote ML role in Europe?","ground_truth":"Potentially yes. The candidate prefers hybrid work but is open to relocation. He has strong ML skills (PyTorch, TensorFlow, NLP, recommendation systems), 4 years of experience, and is fluent in English. His current preferred location is Tel Aviv but his openness to relocation suggests flexibility.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
  {"id":"q073","question":"Compare the candidate's academic and professional experience.","ground_truth":"Academically, Ofir earned a BSc in Computer Science from Tel Aviv University with a GPA of 89/100, was on the Dean's List, and completed a capstone on autonomous drone navigation. Professionally, he has 4 years of industry experience, progressing from Junior Data Scientist at TechStart to ML Engineer leading a team at DataSphere Technologies, building production systems serving millions of users.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
  {"id":"q074","question":"What unique combination of skills does this candidate offer?","ground_truth":"Ofir combines deep ML/NLP expertise (PyTorch, RAG systems, LangChain) with production engineering skills (Kubernetes, Docker, real-time pipelines), cloud infrastructure (AWS, GCP), and team leadership experience. He also bridges research and production, with academic work in reinforcement learning and computer vision alongside production-grade recommendation and fraud detection systems.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
  {"id":"q075","question":"Summarize why I should consider this candidate for a senior ML engineer position.","ground_truth":"Ofir Ohan is a strong candidate for a senior ML engineer role: 4 years of experience building production ML systems, leads a team of 3 engineers, expertise in NLP and recommendation systems serving 2M+ users, built real-time pipelines processing 10K transactions/second, holds AWS ML Specialty certification, BSc in CS from Tel Aviv University (GPA 89/100), contributes to open source (LangChain), and is available from July 2026.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
]
