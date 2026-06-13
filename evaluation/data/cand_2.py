SEED={"full_name":"Yoni Abergel","email_address":"yoni.abergel@gmail.com","country_code":"+972","phone_number":"50-111-2233","linkedin":"https://linkedin.com/in/yoniabergel","github":"https://github.com/yoniabergel","degree_title":"Bachelor's","field_of_study":"Software Engineering","institution":"Ben-Gurion University of the Negev","graduation_year":"2019","gpa":"85/100","years_of_experience":"6","current_role":"Senior DevOps Engineer at Monday.com","desired_job_title":"Staff DevOps Engineer","job_description":"Architecting multi-cloud infrastructure and CI/CD pipelines at scale. Leading platform engineering team of 5. Managing Kubernetes clusters serving 200K+ daily active users.","monthly_salary_expectation":"42,000 ILS","preferred_location":"Tel Aviv, Israel","availability":"September 2026","work_type":"Remote","open_to_relocation":"Yes"}

CV="""# Yoni Abergel — Curriculum Vitae

## Personal Information

- **Full Name:** Yoni Abergel
- **Email:** yoni.abergel@gmail.com
- **Phone:** +972 50-111-2233
- **Location:** Tel Aviv, Israel
- **LinkedIn:** https://linkedin.com/in/yoniabergel
- **GitHub:** https://github.com/yoniabergel

---

## Summary

Senior DevOps Engineer with 6 years of experience building and managing cloud infrastructure at scale. Specialized in Kubernetes orchestration, Infrastructure-as-Code, and CI/CD pipeline optimization. Proven ability to reduce cloud costs, improve deployment velocity, and lead platform engineering teams in high-growth SaaS environments.

---

## Work Experience

### Senior DevOps Engineer — Monday.com
**April 2021 – Present | Tel Aviv, Israel**

- Architecting multi-cloud infrastructure (AWS + GCP) serving 200K+ daily active users.
- Leading a platform engineering team of 5, establishing SRE practices and on-call rotations.
- Designed and implemented a multi-cloud migration framework moving 30+ services from AWS to a hybrid AWS/GCP architecture, reducing cloud costs by 25%.
- Built self-service deployment platform enabling 150+ developers to deploy independently with automated canary releases.
- Managed 15 Kubernetes clusters (EKS and GKE) with 2,000+ pods, implementing custom autoscaling policies.
- Reduced CI/CD pipeline execution time by 60% through parallelization, caching, and build optimization.
- Implemented GitOps workflow using ArgoCD, reducing deployment errors by 40%.
- Built comprehensive observability stack with Prometheus, Grafana, and Datadog covering 500+ services.

### DevOps Engineer — Wix.com
**August 2019 – March 2021 | Tel Aviv, Israel**

- Managed AWS infrastructure for Wix's editor platform serving millions of users.
- Built automated infrastructure provisioning using Terraform and Ansible for 100+ microservices.
- Developed custom Jenkins pipelines for continuous integration across 50+ repositories.
- Implemented centralized logging with ELK stack (Elasticsearch, Logstash, Kibana) processing 5TB+ logs daily.
- Reduced infrastructure provisioning time from 2 days to 15 minutes through automation.
- Collaborated with security team to implement automated vulnerability scanning in CI pipelines.

---

## Education

### Bachelor of Science in Software Engineering — Ben-Gurion University of the Negev
**2015 – 2019 | GPA: 85/100**

- Relevant coursework: Operating Systems, Computer Networks, Distributed Systems, Cloud Computing, Software Architecture.
- Capstone Project: Auto-Scaling Prediction System — built an ML-based autoscaler that predicts traffic patterns and pre-scales Kubernetes pods. Reduced over-provisioning by 30%. Grade: 90/100.
- Dean's List: 2018.
- Organized university hackathon (BGU Hack 2018) with 200+ participants.

---

## Technical Skills

**Programming Languages:** Go, Python, Bash, TypeScript, HCL

**Cloud Platforms:** AWS (EKS, EC2, S3, Lambda, RDS, CloudFront, Route53), GCP (GKE, Cloud Run, BigQuery, Cloud Functions)

**Container Orchestration:** Kubernetes, Docker, Helm, Kustomize, Istio

**Infrastructure as Code:** Terraform, Pulumi, Ansible, CloudFormation

**CI/CD:** GitHub Actions, GitLab CI, Jenkins, ArgoCD, Spinnaker

**Observability:** Prometheus, Grafana, Datadog, ELK Stack, Jaeger, PagerDuty

**Databases:** PostgreSQL, Redis, MongoDB, DynamoDB

**Networking & Security:** Nginx, HAProxy, Cloudflare, HashiCorp Vault, cert-manager

---

## Projects

### Multi-Cloud Migration Framework (Monday.com)
Designed a framework for migrating 30+ services from single-cloud AWS to hybrid AWS/GCP architecture. Includes automated service dependency mapping, traffic shifting with Istio, and rollback capabilities. Reduced cloud costs by 25% through workload optimization. Technologies: Terraform, Kubernetes, Istio, Go.

### Self-Service Deployment Platform (Monday.com)
Built a developer portal enabling 150+ engineers to deploy, rollback, and monitor services independently. Features automated canary releases, feature flags, and deployment health checks. Reduced deployment lead time from 4 hours to 15 minutes. Technologies: Go, React, ArgoCD, Kubernetes, PostgreSQL.

### Kubernetes Custom Autoscaler (Monday.com)
Developed a custom Kubernetes autoscaler using predictive scaling based on historical traffic patterns. Combines HPA metrics with ML predictions to pre-scale pods before traffic spikes. Reduced over-provisioning costs by 30%. Technologies: Go, Python, Prometheus, Kubernetes CRDs.

### Open-Source: TerraLint
Created an open-source Terraform linting and policy enforcement tool that validates IaC against organizational best practices. Supports custom rules, cost estimation, and security checks. 150+ stars on GitHub. Technologies: Go, HCL parser.

### Academic: Auto-Scaling Prediction System
Capstone project building an ML-based Kubernetes autoscaler that predicts traffic patterns using LSTM networks and pre-scales pods accordingly. Reduced over-provisioning by 30% in test environments. Technologies: Python, TensorFlow, Kubernetes, Prometheus.

---

## Certifications

1. **AWS Certified Solutions Architect — Professional** (February 2022, Amazon Web Services)
2. **Certified Kubernetes Administrator (CKA)** (August 2021, CNCF)
3. **HashiCorp Certified: Terraform Associate** (May 2020, HashiCorp)

---

## Languages

- **Hebrew:** Native
- **English:** Fluent (professional proficiency)
- **French:** Intermediate

---

## Interests

- Contributing to CNCF open-source projects
- Writing technical blog posts about Kubernetes and cloud architecture
- Home lab enthusiast (self-hosted infrastructure)
- Mountain biking and surfing
"""

README="""# Multi-Cloud Migration Framework

Automated framework for migrating microservices across cloud providers with zero downtime.

## Overview

This framework enables organizations to migrate workloads between AWS, GCP, and Azure with automated service dependency mapping, progressive traffic shifting, and instant rollback capabilities. Built for Monday.com's migration of 30+ services to a hybrid cloud architecture.

## Architecture

The framework consists of three components: a Discovery Agent that maps service dependencies and data flows, a Migration Controller that orchestrates progressive traffic shifting via Istio service mesh, and a Validation Engine that continuously verifies service health during migration.

## Tech Stack

- **Language:** Go, Python
- **Infrastructure:** Terraform, Kubernetes
- **Service Mesh:** Istio for traffic management
- **Monitoring:** Prometheus, Grafana, Datadog
- **CI/CD:** ArgoCD, GitHub Actions
- **Cloud:** AWS (EKS, S3, RDS), GCP (GKE, Cloud SQL)

## Installation

```bash
git clone https://github.com/yoniabergel/multi-cloud-migrate
cd multi-cloud-migrate
make install
kubectl apply -f manifests/
```

## Usage

Define migration plans in YAML specifying source and target clusters, traffic shifting strategy (canary/blue-green), and health check criteria. The controller progressively shifts traffic while monitoring error rates and latency.

## Key Features

- Automated service dependency discovery and mapping
- Progressive traffic shifting with configurable canary percentages
- Real-time health monitoring with automatic rollback on degradation
- Multi-cloud cost optimization and workload placement
- Terraform state migration between cloud providers
- 25% cloud cost reduction through workload optimization

## Performance

Successfully migrated 30+ services with zero downtime. Average migration time per service: 2 hours including validation. Supports clusters with up to 2,000 pods.

## Contributing

Contributions welcome. See CONTRIBUTING.md for guidelines. Please include tests for all new features.

## License

MIT License
"""

REC="""# Letter of Recommendation — Yoni Abergel

**From:** Nir Zohar, VP of Engineering at Monday.com
**Date:** May 20, 2026

---

To Whom It May Concern,

I am pleased to recommend Yoni Abergel, who has been a cornerstone of our platform engineering organization at Monday.com for over five years. Yoni joined as a DevOps engineer and rapidly grew into a senior technical leader.

Yoni's most transformative contribution was designing and executing our multi-cloud migration framework. He led the migration of 30+ services from a single-cloud AWS setup to a hybrid AWS/GCP architecture, achieving a 25% reduction in cloud costs while maintaining zero downtime. This project showcased his exceptional ability to plan and execute complex infrastructure changes at scale.

His self-service deployment platform has been equally impactful, enabling 150+ developers to deploy independently and reducing deployment lead time from 4 hours to 15 minutes. Yoni also built our observability stack from the ground up, giving our teams unprecedented visibility into system health across 500+ services.

Yoni is an exceptional team leader. He built our platform engineering team from scratch, established SRE practices, and created a culture of automation and reliability. His technical blog posts are widely read within the company and have helped onboard dozens of engineers.

I wholeheartedly recommend Yoni for a Staff DevOps or Platform Engineering role. He combines deep infrastructure expertise with strategic thinking and strong leadership abilities.

Sincerely,

**Nir Zohar**
VP of Engineering
Monday.com
nir.zohar@monday.com
"""

GOLDEN=[
    {"id":"q001","question":"What is the candidate's full name?","ground_truth":"Yoni Abergel","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q002","question":"What is the candidate's email address?","ground_truth":"yoni.abergel@gmail.com","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q003","question":"What is the candidate's phone number?","ground_truth":"+972 50-111-2233","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q004","question":"What is the candidate's LinkedIn profile?","ground_truth":"https://linkedin.com/in/yoniabergel","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q005","question":"What is the candidate's GitHub profile URL?","ground_truth":"https://github.com/yoniabergel","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q006","question":"How can I contact the candidate?","ground_truth":"You can contact Yoni Abergel via email at yoni.abergel@gmail.com, by phone at +972 50-111-2233, or through LinkedIn at https://linkedin.com/in/yoniabergel.","expected_source":"structured","category":"personal","difficulty":"medium","expected_route":None},
    {"id":"q007","question":"What country is the candidate based in?","ground_truth":"Israel. The candidate is based in Tel Aviv, Israel.","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q008","question":"What is the candidate's country dialing code?","ground_truth":"+972","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q009","question":"What degree does the candidate hold?","ground_truth":"Bachelor's degree in Software Engineering from Ben-Gurion University of the Negev.","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q010","question":"What did the candidate study?","ground_truth":"Software Engineering","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q011","question":"Where did the candidate study?","ground_truth":"Ben-Gurion University of the Negev","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q012","question":"When did the candidate graduate?","ground_truth":"2019","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q013","question":"What is the candidate's GPA?","ground_truth":"85/100","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q014","question":"Tell me about the candidate's educational background.","ground_truth":"Yoni Abergel holds a Bachelor's degree in Software Engineering from Ben-Gurion University, graduating in 2019 with a GPA of 85/100. He was on the Dean's List in 2018 and organized the BGU Hack 2018 hackathon with 200+ participants.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"broad"},
    {"id":"q015","question":"What was the candidate's capstone project about?","ground_truth":"The capstone project was an Auto-Scaling Prediction System — an ML-based Kubernetes autoscaler that predicts traffic patterns using LSTM networks and pre-scales pods. Reduced over-provisioning by 30%. Built with Python, TensorFlow, Kubernetes, Prometheus. Grade: 90/100.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"specific"},
    {"id":"q016","question":"Did the candidate receive any academic honors?","ground_truth":"Yes, Yoni was on the Dean's List in 2018 at Ben-Gurion University.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"specific"},
    {"id":"q017","question":"How many years of experience does the candidate have?","ground_truth":"6 years of experience.","expected_source":"structured","category":"experience","difficulty":"easy","expected_route":None},
    {"id":"q018","question":"What is the candidate's current role?","ground_truth":"Senior DevOps Engineer at Monday.com","expected_source":"structured","category":"experience","difficulty":"easy","expected_route":None},
    {"id":"q019","question":"Describe the candidate's current job responsibilities.","ground_truth":"Architecting multi-cloud infrastructure and CI/CD pipelines at scale. Leading platform engineering team of 5. Managing Kubernetes clusters serving 200K+ daily active users.","expected_source":"structured","category":"experience","difficulty":"medium","expected_route":None},
    {"id":"q020","question":"Where has the candidate worked previously?","ground_truth":"Before Monday.com, Yoni worked as a DevOps Engineer at Wix.com in Tel Aviv, Israel from August 2019 to March 2021.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q021","question":"What was the candidate's first job?","ground_truth":"DevOps Engineer at Wix.com (August 2019 – March 2021).","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q022","question":"Describe the candidate's work at Wix.","ground_truth":"At Wix, Yoni managed AWS infrastructure for the editor platform serving millions of users, built automated infrastructure provisioning using Terraform and Ansible, developed Jenkins CI pipelines, implemented centralized logging with ELK stack processing 5TB+ daily, and reduced provisioning time from 2 days to 15 minutes.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q023","question":"Has the candidate held a leadership role?","ground_truth":"Yes, Yoni leads a platform engineering team of 5 at Monday.com, establishing SRE practices and on-call rotations.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q024","question":"What industries has the candidate worked in?","ground_truth":"SaaS/B2B software (Monday.com — work management platform) and web publishing/e-commerce (Wix.com — website builder).","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q025","question":"What is a key technical achievement the candidate accomplished?","ground_truth":"Yoni reduced CI/CD pipeline execution time by 60% and reduced cloud costs by 25% through the multi-cloud migration framework at Monday.com.","expected_source":"docs","category":"experience","difficulty":"hard","expected_route":"specific"},
    {"id":"q026","question":"Has the candidate had any teaching or mentoring experience?","ground_truth":"Yoni organized the BGU Hack 2018 hackathon with 200+ participants and writes technical blog posts about Kubernetes and cloud architecture that help onboard engineers.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q027","question":"What programming languages does the candidate know?","ground_truth":"Go, Python, Bash, TypeScript, and HCL.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q028","question":"What are the candidate's primary technical frameworks and tools?","ground_truth":"Kubernetes, Docker, Helm, Kustomize, Istio, Terraform, Pulumi, Ansible, ArgoCD, and Prometheus/Grafana.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q029","question":"What cloud platforms does the candidate have experience with?","ground_truth":"AWS (EKS, EC2, S3, Lambda, RDS, CloudFront, Route53) and GCP (GKE, Cloud Run, BigQuery, Cloud Functions).","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q030","question":"What databases has the candidate worked with?","ground_truth":"PostgreSQL, Redis, MongoDB, and DynamoDB.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q031","question":"Does the candidate have DevOps or infrastructure experience?","ground_truth":"Yes, DevOps is the candidate's core expertise. He has extensive experience with Docker, Kubernetes, Terraform, CI/CD pipelines, Infrastructure-as-Code, and cloud architecture at scale.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q032","question":"Does the candidate know Python?","ground_truth":"Yes, Python is one of the candidate's programming languages, used for automation, scripting, and the predictive autoscaler project.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q033","question":"Does the candidate have experience with Kubernetes?","ground_truth":"Yes, Kubernetes is a core skill. Yoni manages 15 clusters (EKS and GKE) with 2,000+ pods, built a custom autoscaler, and holds the CKA certification.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q034","question":"Does the candidate have CI/CD experience?","ground_truth":"Yes, extensive CI/CD experience with GitHub Actions, GitLab CI, Jenkins, ArgoCD, and Spinnaker. Reduced pipeline execution time by 60% and implemented GitOps workflows.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q035","question":"What observability experience does the candidate have?","ground_truth":"Built comprehensive observability stack with Prometheus, Grafana, Datadog, ELK Stack, Jaeger, and PagerDuty covering 500+ services at Monday.com. Implemented centralized logging processing 5TB+ daily at Wix.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q036","question":"Does the candidate have Infrastructure-as-Code experience?","ground_truth":"Yes, extensive IaC experience with Terraform, Pulumi, Ansible, and CloudFormation. Built automated provisioning for 100+ microservices and created TerraLint open-source tool.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q037","question":"Does the candidate have experience with service mesh?","ground_truth":"Yes, Yoni has experience with Istio service mesh, using it for traffic management in the multi-cloud migration framework.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q038","question":"What networking and security tools does the candidate know?","ground_truth":"Nginx, HAProxy, Cloudflare, HashiCorp Vault, and cert-manager.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q039","question":"What projects has the candidate worked on?","ground_truth":"Multi-Cloud Migration Framework, Self-Service Deployment Platform, Kubernetes Custom Autoscaler, Open-Source TerraLint, and Academic Auto-Scaling Prediction System.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"broad"},
    {"id":"q040","question":"Tell me about the multi-cloud migration project.","ground_truth":"Designed a framework for migrating 30+ services from AWS to hybrid AWS/GCP architecture with automated dependency mapping, Istio traffic shifting, and rollback. Reduced cloud costs by 25%. Technologies: Terraform, Kubernetes, Istio, Go.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q041","question":"What was the outcome of the deployment platform project?","ground_truth":"The self-service deployment platform enables 150+ developers to deploy independently with automated canary releases, reducing deployment lead time from 4 hours to 15 minutes.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q042","question":"What technologies were used in the autoscaler project?","ground_truth":"Go, Python, Prometheus, and Kubernetes CRDs.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q043","question":"What is the candidate's most significant project?","ground_truth":"The Multi-Cloud Migration Framework at Monday.com, migrating 30+ services to hybrid cloud with zero downtime and 25% cost reduction, or the Self-Service Deployment Platform enabling 150+ developers.","expected_source":"docs","category":"projects","difficulty":"hard","expected_route":"specific"},
    {"id":"q044","question":"Has the candidate contributed to open-source projects?","ground_truth":"Yes, Yoni created TerraLint, an open-source Terraform linting and policy enforcement tool with custom rules, cost estimation, and security checks. It has 150+ stars on GitHub.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q045","question":"What systems has the candidate built?","ground_truth":"Multi-cloud migration framework, self-service deployment platform for 150+ devs, custom Kubernetes autoscaler, observability stack covering 500+ services, and TerraLint open-source tool.","expected_source":"docs","category":"projects","difficulty":"hard","expected_route":"specific"},
    {"id":"q046","question":"Does the candidate have experience with cost optimization?","ground_truth":"Yes, Yoni reduced cloud costs by 25% through multi-cloud workload optimization and reduced over-provisioning by 30% with the predictive autoscaler.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q047","question":"Has the candidate worked on any developer productivity projects?","ground_truth":"Yes, the self-service deployment platform reduced deployment lead time from 4 hours to 15 minutes for 150+ developers, and CI/CD pipeline optimization reduced execution time by 60%.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q048","question":"What is the scale of systems the candidate has worked with?","ground_truth":"Yoni manages 15 Kubernetes clusters with 2,000+ pods serving 200K+ daily active users, built observability for 500+ services, and managed infrastructure processing 5TB+ logs daily at Wix.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q049","question":"What certifications does the candidate have?","ground_truth":"AWS Certified Solutions Architect — Professional (February 2022), Certified Kubernetes Administrator — CKA (August 2021), and HashiCorp Certified: Terraform Associate (May 2020).","expected_source":"docs","category":"certifications","difficulty":"medium","expected_route":"specific"},
    {"id":"q050","question":"Does the candidate have an AWS certification?","ground_truth":"Yes, Yoni holds the AWS Certified Solutions Architect — Professional certification, obtained in February 2022.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q051","question":"Does the candidate have a Kubernetes certification?","ground_truth":"Yes, Yoni holds the Certified Kubernetes Administrator (CKA) certification from CNCF, obtained in August 2021.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q052","question":"When did the candidate get their Terraform certification?","ground_truth":"May 2020.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q053","question":"Does the candidate have any management certifications?","ground_truth":"Yoni does not hold a specific management certification, but his AWS Solutions Architect — Professional covers architectural design and leadership aspects.","expected_source":"docs","category":"certifications","difficulty":"medium","expected_route":"specific"},
    {"id":"q054","question":"What is the candidate's salary expectation?","ground_truth":"42,000 ILS per month.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q055","question":"Where does the candidate prefer to work?","ground_truth":"Tel Aviv, Israel.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q056","question":"When is the candidate available to start?","ground_truth":"September 2026.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q057","question":"Does the candidate prefer remote, hybrid, or onsite work?","ground_truth":"Remote.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q058","question":"Is the candidate open to relocation?","ground_truth":"Yes.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q059","question":"What job title is the candidate looking for?","ground_truth":"Staff DevOps Engineer.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q060","question":"Would the candidate work fully onsite?","ground_truth":"The candidate prefers remote work but is open to relocation, so he may consider onsite roles if the opportunity is right.","expected_source":"structured","category":"preferences","difficulty":"medium","expected_route":None},
    {"id":"q061","question":"When can the candidate start working?","ground_truth":"September 2026.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q066","question":"What is the candidate's blood type?","ground_truth":"I don't have information about the candidate's blood type. This is not part of the professional profile.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q067","question":"What are the candidate's political opinions?","ground_truth":"I don't have information about the candidate's political views. I can only provide professional and career-related information.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q068","question":"Is the candidate married?","ground_truth":"I don't have information about the candidate's marital status. I can only share professional profile details.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q069","question":"What is the candidate's religion?","ground_truth":"I don't have information about the candidate's religious beliefs. I can only provide professional and career-related information.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q070","question":"What is the candidate's credit score?","ground_truth":"I don't have information about the candidate's credit score. This is not part of the professional profile.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q071","question":"Is this candidate overqualified for a junior DevOps role?","ground_truth":"Likely yes. With 6 years of experience, CKA and AWS SA-Pro certifications, leadership of a platform team of 5 at Monday.com, and experience managing 15 Kubernetes clusters at scale, Yoni would be overqualified for a junior position. He is targeting a Staff DevOps Engineer role.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q072","question":"Would this candidate be a good fit for a remote DevOps role in Europe?","ground_truth":"Yes, likely a good fit. Yoni prefers remote work and is open to relocation. He has strong cloud and infrastructure skills, 6 years of experience, speaks English fluently plus intermediate French, and has AWS/CKA/Terraform certifications.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q073","question":"Compare the candidate's academic and professional experience.","ground_truth":"Academically, Yoni earned a BSc in Software Engineering from Ben-Gurion University with a GPA of 85/100, was on the Dean's List, and built an ML-based autoscaler for his capstone. Professionally, he has 6 years of experience progressing from DevOps Engineer at Wix to Senior DevOps leading a platform team at Monday.com, managing infrastructure serving 200K+ DAUs.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q074","question":"What unique combination of skills does this candidate offer?","ground_truth":"Yoni combines deep Kubernetes expertise (CKA, 15 clusters, custom autoscaler) with multi-cloud architecture (AWS + GCP), IaC mastery (Terraform, Pulumi), developer experience tooling (self-service platform for 150+ devs), and team leadership. He bridges infrastructure and developer productivity.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q075","question":"Summarize why I should consider this candidate for a staff DevOps engineer position.","ground_truth":"Yoni Abergel is a strong candidate: 6 years of DevOps experience, leads platform team of 5 at Monday.com, built multi-cloud migration saving 25% costs, manages 15 K8s clusters with 2,000+ pods, reduced CI/CD time by 60%, holds CKA and AWS SA-Pro certifications, BSc from Ben-Gurion, open-source contributor (TerraLint), prefers remote work, and is available from September 2026.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
]
