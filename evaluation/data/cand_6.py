SEED={"full_name":"Tal Ben-David","email_address":"tal.bendavid@gmail.com","country_code":"+972","phone_number":"58-222-3344","linkedin":"https://linkedin.com/in/talbendavid","github":"https://github.com/talbendavid","degree_title":"Master's","field_of_study":"Computer Science","institution":"Tel Aviv University","graduation_year":"2018","gpa":"90/100","years_of_experience":"7","current_role":"Staff Backend Engineer at AppsFlyer","desired_job_title":"Principal Engineer","job_description":"Designing distributed event-processing systems handling 100B+ daily events. Leading backend architecture guild of 8 engineers. Driving microservices migration and platform reliability.","monthly_salary_expectation":"55,000 ILS","preferred_location":"Herzliya, Israel","availability":"August 2026","work_type":"Hybrid","open_to_relocation":"No","skills":["Java","Kafka","Flink","Kubernetes","ClickHouse"]}
CV="""# Tal Ben-David — Curriculum Vitae
## Personal Information
- **Full Name:** Tal Ben-David
- **Email:** tal.bendavid@gmail.com
- **Phone:** +972 58-222-3344
- **Location:** Herzliya, Israel
- **LinkedIn:** https://linkedin.com/in/talbendavid
- **GitHub:** https://github.com/talbendavid
---
## Summary
Staff Backend Engineer with 7 years of experience designing distributed systems and event-driven architectures at scale. Specialized in high-throughput data pipelines, microservices, and platform reliability. Proven track record of building systems processing 100B+ daily events with sub-millisecond latency requirements.
---
## Work Experience
### Staff Backend Engineer — AppsFlyer
**March 2020 – Present | Herzliya, Israel**
- Designing distributed event-processing systems handling 100B+ daily events for mobile attribution.
- Leading the backend architecture guild of 8 senior engineers, establishing design review processes.
- Built a real-time event enrichment pipeline processing 1.2M events/second using Kafka and Flink.
- Led microservices migration decomposing a monolithic Clojure application into 40+ services.
- Designed a multi-region active-active architecture achieving 99.99% uptime SLA.
- Reduced P99 latency by 65% through custom connection pooling and async I/O optimizations.
- Implemented distributed tracing across 40+ microservices using OpenTelemetry and Jaeger.
- Mentored 6 backend engineers through architecture design sessions and code reviews.
### Backend Engineer — Amdocs
**September 2018 – February 2020 | Ra'anana, Israel**
- Developed billing and charging systems for tier-1 telecom operators processing 500M+ daily transactions.
- Built real-time rating engine using Java and Apache Ignite with sub-10ms response times.
- Designed event-sourcing architecture for billing audit trail with Kafka and Cassandra.
- Optimized database queries reducing report generation time from 4 hours to 20 minutes.
- Collaborated with 3 telecom clients on custom integration and API design.
---
## Education
### Master of Science in Computer Science — Tel Aviv University
**2016 – 2018 | GPA: 90/100**
- Specialization: Distributed Systems and Algorithms.
- Thesis: Consensus Protocols for Geo-Distributed Databases — designed a novel Raft variant optimized for cross-datacenter replication with 40% reduction in commit latency. Grade: 95/100.
- Dean's List: 2017.
- Teaching Assistant for Distributed Systems course (2017-2018).
---
## Technical Skills
**Programming Languages:** Java, Scala, Kotlin, Go, Python, Clojure
**Distributed Systems:** Apache Kafka, Apache Flink, Apache Spark, Akka, gRPC, Protocol Buffers
**Databases:** PostgreSQL, Cassandra, Redis, Elasticsearch, ClickHouse, Apache Ignite
**Cloud & Infrastructure:** AWS (EKS, MSK, DynamoDB, S3, Lambda), Docker, Kubernetes, Terraform
**Observability:** OpenTelemetry, Jaeger, Prometheus, Grafana, Datadog
**Architecture:** Microservices, Event Sourcing, CQRS, Saga Pattern, Circuit Breaker
---
## Projects
### Real-Time Event Enrichment Pipeline (AppsFlyer)
Built a streaming pipeline processing 1.2M events/second for mobile attribution enrichment. Uses Kafka for ingestion, Flink for stateful processing, and ClickHouse for analytics. Technologies: Java, Kafka, Flink, ClickHouse, Kubernetes.
### Multi-Region Active-Active Architecture (AppsFlyer)
Designed active-active deployment across 3 AWS regions achieving 99.99% uptime. Includes conflict-free replicated data types (CRDTs) for state synchronization and intelligent routing. Technologies: Go, Kafka, Redis, AWS.
### Microservices Migration (AppsFlyer)
Led decomposition of monolithic Clojure application into 40+ microservices with saga-based transactions, API gateway, and service mesh. Reduced deployment cycle from 2 weeks to 2 hours. Technologies: Kotlin, gRPC, Istio, Kubernetes.
### Open-Source: KafkaFlow
Created an open-source Kafka consumer framework for Java/Kotlin with built-in retry, dead-letter queues, and backpressure handling. 250+ stars on GitHub. Technologies: Kotlin, Kafka.
### Academic: Geo-Distributed Consensus
Designed a Raft variant optimized for cross-datacenter replication reducing commit latency by 40%. Implemented prototype in Go and evaluated across 5 simulated datacenters. Published at ACM SOSP Workshop.
---
## Certifications
1. **AWS Certified Solutions Architect — Associate** (April 2021, Amazon Web Services)
2. **Confluent Certified Developer for Apache Kafka** (October 2020, Confluent)
3. **Oracle Certified Professional Java SE 11** (March 2019, Oracle)
---
## Languages
- **Hebrew:** Native
- **English:** Fluent (professional proficiency)
---
## Interests
- Contributing to Apache Kafka and Flink communities
- Distributed systems paper reading group
- Competitive chess (FIDE rating 1850)
- Long-distance running
"""
README="""# Real-Time Event Enrichment Pipeline
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
"""
REC="""# Letter of Recommendation — Tal Ben-David
**From:** Reshef Mann, CTO at AppsFlyer
**Date:** May 22, 2026
---
To Whom It May Concern,

I recommend Tal Ben-David, who has been a technical cornerstone at AppsFlyer for over six years. Tal joined as a backend engineer and quickly became one of our most influential architects.

Tal's flagship achievement is the real-time event enrichment pipeline processing 1.2M events/second — the backbone of our attribution platform. He designed the architecture from scratch, solving complex challenges around exactly-once semantics, stateful processing, and multi-region consistency.

His leadership of the microservices migration — decomposing our monolith into 40+ services — transformed our engineering velocity, reducing deployment cycles from 2 weeks to 2 hours. As architecture guild leader, Tal mentors 8 senior engineers and has established design review processes that elevated our system quality.

Tal combines rare depth in distributed systems theory (MSc thesis on consensus protocols, published at SOSP Workshop) with pragmatic engineering excellence. His KafkaFlow open-source project (250+ stars) demonstrates his commitment to the broader engineering community.

I recommend Tal without reservation for a Principal Engineer role.

Sincerely,

**Reshef Mann**
CTO, AppsFlyer
reshef.mann@appsflyer.com
"""
GOLDEN=[
    {"id":"q001","question":"What is the candidate's full name?","ground_truth":"Tal Ben-David","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q002","question":"What is the candidate's email address?","ground_truth":"tal.bendavid@gmail.com","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q003","question":"What is the candidate's phone number?","ground_truth":"+972 58-222-3344","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q004","question":"What is the candidate's LinkedIn profile?","ground_truth":"https://linkedin.com/in/talbendavid","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q005","question":"What is the candidate's GitHub profile URL?","ground_truth":"https://github.com/talbendavid","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q006","question":"How can I contact the candidate?","ground_truth":"You can contact Tal Ben-David via email at tal.bendavid@gmail.com, by phone at +972 58-222-3344, or through LinkedIn at https://linkedin.com/in/talbendavid.","expected_source":"structured","category":"personal","difficulty":"medium","expected_route":None},
    {"id":"q007","question":"What country is the candidate based in?","ground_truth":"Israel. The candidate is based in Herzliya, Israel.","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q008","question":"What is the candidate's country dialing code?","ground_truth":"+972","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q009","question":"What degree does the candidate hold?","ground_truth":"Master's degree in Computer Science from Tel Aviv University.","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q010","question":"What did the candidate study?","ground_truth":"Computer Science","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q011","question":"Where did the candidate study?","ground_truth":"Tel Aviv University","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q012","question":"When did the candidate graduate?","ground_truth":"2018","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q013","question":"What is the candidate's GPA?","ground_truth":"90/100","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q014","question":"Tell me about the candidate's educational background.","ground_truth":"Tal holds an MSc in Computer Science from Tel Aviv University (GPA 90/100), specializing in Distributed Systems and Algorithms. He was on the Dean's List in 2017 and served as a TA for Distributed Systems.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"broad"},
    {"id":"q015","question":"What was the candidate's thesis about?","ground_truth":"Consensus Protocols for Geo-Distributed Databases — a novel Raft variant optimized for cross-datacenter replication with 40% reduction in commit latency. Grade: 95/100. Published at ACM SOSP Workshop.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"specific"},
    {"id":"q016","question":"Did the candidate receive any academic honors?","ground_truth":"Yes, Tal was on the Dean's List in 2017 at Tel Aviv University.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"specific"},
    {"id":"q017","question":"How many years of experience does the candidate have?","ground_truth":"7 years of experience.","expected_source":"structured","category":"experience","difficulty":"easy","expected_route":None},
    {"id":"q018","question":"What is the candidate's current role?","ground_truth":"Staff Backend Engineer at AppsFlyer","expected_source":"structured","category":"experience","difficulty":"easy","expected_route":None},
    {"id":"q019","question":"Describe the candidate's current job responsibilities.","ground_truth":"Designing distributed event-processing systems handling 100B+ daily events. Leading backend architecture guild of 8 engineers. Driving microservices migration and platform reliability.","expected_source":"structured","category":"experience","difficulty":"medium","expected_route":None},
    {"id":"q020","question":"Where has the candidate worked previously?","ground_truth":"Before AppsFlyer, Tal worked as a Backend Engineer at Amdocs in Ra'anana, Israel from September 2018 to February 2020.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q021","question":"What was the candidate's first job?","ground_truth":"Backend Engineer at Amdocs (September 2018 – February 2020).","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q022","question":"Describe the candidate's work at Amdocs.","ground_truth":"At Amdocs, Tal developed billing systems for telecom operators processing 500M+ daily transactions, built a real-time rating engine with sub-10ms response using Java and Apache Ignite, designed event-sourcing architecture with Kafka and Cassandra, and optimized reports from 4 hours to 20 minutes.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q023","question":"Has the candidate held a leadership role?","ground_truth":"Yes, Tal leads the backend architecture guild of 8 senior engineers at AppsFlyer, establishing design review processes and mentoring 6 backend engineers.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q024","question":"What industries has the candidate worked in?","ground_truth":"Mobile ad-tech/attribution (AppsFlyer) and telecommunications/billing (Amdocs).","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q025","question":"What is a key technical achievement the candidate accomplished?","ground_truth":"Tal reduced P99 latency by 65% through custom connection pooling and async I/O, and designed a multi-region active-active architecture achieving 99.99% uptime SLA.","expected_source":"docs","category":"experience","difficulty":"hard","expected_route":"specific"},
    {"id":"q026","question":"Has the candidate had any teaching experience?","ground_truth":"Yes, Tal served as a Teaching Assistant for Distributed Systems at Tel Aviv University (2017-2018) and mentors 6 backend engineers at AppsFlyer.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q027","question":"What programming languages does the candidate know?","ground_truth":"Java, Scala, Kotlin, Go, Python, and Clojure.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q028","question":"What are the candidate's primary technical frameworks and tools?","ground_truth":"Apache Kafka, Apache Flink, Apache Spark, Akka, gRPC, Protocol Buffers, and OpenTelemetry.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q029","question":"What cloud platforms does the candidate have experience with?","ground_truth":"AWS (EKS, MSK, DynamoDB, S3, Lambda).","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q030","question":"What databases has the candidate worked with?","ground_truth":"PostgreSQL, Cassandra, Redis, Elasticsearch, ClickHouse, and Apache Ignite.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q031","question":"Does the candidate have DevOps or infrastructure experience?","ground_truth":"Yes, experience with Docker, Kubernetes, Terraform, and AWS infrastructure management.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q032","question":"Does the candidate know Python?","ground_truth":"Yes, Python is one of Tal's programming languages.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q033","question":"Does the candidate have experience with Kafka?","ground_truth":"Yes, Kafka is central to Tal's work — building pipelines processing 1.2M events/sec, event-sourcing architecture, and creating the KafkaFlow open-source framework (250+ stars). He also holds the Confluent Kafka certification.","expected_source":"docs","accept_sources":["skill"],"category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q034","question":"Does the candidate have distributed systems experience?","ground_truth":"Yes, extensive experience including MSc thesis on consensus protocols, multi-region active-active architecture (99.99% uptime), distributed tracing across 40+ microservices, and event-driven architectures processing 100B+ daily events.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q035","question":"What architecture patterns does the candidate know?","ground_truth":"Microservices, Event Sourcing, CQRS, Saga Pattern, Circuit Breaker, and CRDTs for distributed state.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q036","question":"Does the candidate have observability experience?","ground_truth":"Yes, implemented distributed tracing across 40+ microservices using OpenTelemetry and Jaeger, plus monitoring with Prometheus, Grafana, and Datadog.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q037","question":"Does the candidate have experience with Kubernetes?","ground_truth":"Yes, Tal uses Kubernetes (EKS) for deploying microservices and streaming pipelines, with Terraform for infrastructure management.","expected_source":"docs","accept_sources":["skill"],"category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q038","question":"What streaming and data processing tools does the candidate know?","ground_truth":"Apache Kafka, Apache Flink, Apache Spark, and Kafka MirrorMaker 2.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q039","question":"What projects has the candidate worked on?","ground_truth":"Real-Time Event Enrichment Pipeline, Multi-Region Active-Active Architecture, Microservices Migration, Open-Source KafkaFlow, and Academic Geo-Distributed Consensus.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"broad"},
    {"id":"q040","question":"Tell me about the event enrichment pipeline.","ground_truth":"Built a streaming pipeline processing 1.2M events/second for mobile attribution enrichment using Kafka for ingestion, Flink for stateful processing with RocksDB, and ClickHouse for analytics. Exactly-once semantics with sub-100ms latency. Technologies: Java, Kafka, Flink, ClickHouse, Kubernetes.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q041","question":"What was the outcome of the multi-region architecture project?","ground_truth":"Designed active-active deployment across 3 AWS regions achieving 99.99% uptime SLA with CRDTs for conflict-free state synchronization and zero data loss during region failovers.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q042","question":"What technologies were used in the microservices migration?","ground_truth":"Kotlin, gRPC, Istio, and Kubernetes.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q043","question":"What is the candidate's most significant project?","ground_truth":"The Real-Time Event Enrichment Pipeline processing 1.2M events/second at AppsFlyer, or the Multi-Region Active-Active Architecture achieving 99.99% uptime across 3 AWS regions.","expected_source":"docs","category":"projects","difficulty":"hard","expected_route":"specific"},
    {"id":"q044","question":"Has the candidate contributed to open-source projects?","ground_truth":"Yes, Tal created KafkaFlow, an open-source Kafka consumer framework for Java/Kotlin with built-in retry, dead-letter queues, and backpressure handling. 250+ stars on GitHub.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q045","question":"What systems has the candidate built?","ground_truth":"Event enrichment pipeline (1.2M events/sec), multi-region active-active architecture (99.99% uptime), 40+ microservices decomposition, real-time billing engine (500M+ daily transactions), and KafkaFlow library.","expected_source":"docs","category":"projects","difficulty":"hard","expected_route":"specific"},
    {"id":"q046","question":"Does the candidate have high-availability experience?","ground_truth":"Yes, Tal designed multi-region active-active architecture achieving 99.99% uptime with CRDTs, zero-downtime failovers, and exactly-once processing semantics.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q047","question":"Has the candidate worked on migration projects?","ground_truth":"Yes, Tal led decomposition of a monolithic Clojure application into 40+ microservices with saga-based transactions, reducing deployment cycles from 2 weeks to 2 hours.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q048","question":"What is the scale of systems the candidate has worked with?","ground_truth":"Tal works with systems processing 100B+ daily events, 1.2M events/second throughput, 40+ microservices, multi-region across 3 AWS regions, and 500M+ daily telecom transactions at Amdocs.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q049","question":"What certifications does the candidate have?","ground_truth":"AWS Certified Solutions Architect — Associate (April 2021), Confluent Certified Developer for Apache Kafka (October 2020), and Oracle Certified Professional Java SE 11 (March 2019).","expected_source":"docs","category":"certifications","difficulty":"medium","expected_route":"specific"},
    {"id":"q050","question":"Does the candidate have an AWS certification?","ground_truth":"Yes, Tal holds the AWS Certified Solutions Architect — Associate, obtained in April 2021.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q051","question":"Does the candidate have a Kafka certification?","ground_truth":"Yes, Tal holds the Confluent Certified Developer for Apache Kafka, obtained in October 2020.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q052","question":"When did the candidate get their Java certification?","ground_truth":"March 2019.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q053","question":"Does the candidate have any management certifications?","ground_truth":"Tal does not hold a specific management certification, but his AWS SA covers architectural leadership aspects.","expected_source":"docs","category":"certifications","difficulty":"medium","expected_route":"specific"},
    {"id":"q054","question":"What is the candidate's salary expectation?","ground_truth":"55,000 ILS per month.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q055","question":"Where does the candidate prefer to work?","ground_truth":"Herzliya, Israel.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q056","question":"When is the candidate available to start?","ground_truth":"August 2026.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q057","question":"Does the candidate prefer remote, hybrid, or onsite work?","ground_truth":"Hybrid.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q058","question":"Is the candidate open to relocation?","ground_truth":"No.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q059","question":"What job title is the candidate looking for?","ground_truth":"Principal Engineer.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q060","question":"Would the candidate work fully onsite?","ground_truth":"The candidate prefers hybrid work and is not open to relocation, so a fully onsite role would need to be in the Herzliya area.","expected_source":"structured","category":"preferences","difficulty":"medium","expected_route":None},
    {"id":"q061","question":"When can the candidate start working?","ground_truth":"August 2026.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q062","question":"How proficient is the candidate in Java?","ground_truth":"Java is one of the candidate's core, strongly-evidenced skills. He builds high-throughput streaming systems in Java and holds an Oracle Java SE 11 certification.","expected_source":"skill","category":"proficiency","difficulty":"easy","expected_route":None},
    {"id":"q063","question":"Rate the candidate's Kafka skills.","ground_truth":"Kafka is central to the candidate's work. He runs pipelines at 1.2M events/sec, built the KafkaFlow library, and holds a Confluent Kafka certification.","expected_source":"skill","category":"proficiency","difficulty":"medium","expected_route":None},
    {"id":"q064","question":"What are the candidate's strongest skills?","ground_truth":"The candidate's strongest, best-evidenced skills are Java, Kafka, Flink, Kubernetes, and ClickHouse — demonstrated across his streaming and data-platform work.","expected_source":"skill","category":"proficiency","difficulty":"medium","expected_route":None},
    {"id":"q065","question":"How strong is the candidate at Kotlin?","ground_truth":"Kotlin is not among the explicitly assessed skills, so this is answered from the documents: Kotlin is listed among Tal's programming languages and used in the microservices migration project.","expected_source":"docs","category":"proficiency","difficulty":"medium","expected_route":None},
    {"id":"q066","question":"What is the candidate's blood type?","ground_truth":"I don't have information about the candidate's blood type. This is not part of the professional profile.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q067","question":"What are the candidate's political opinions?","ground_truth":"I don't have information about the candidate's political views. I can only provide professional and career-related information.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q068","question":"Is the candidate married?","ground_truth":"I don't have information about the candidate's marital status. I can only share professional profile details.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q069","question":"What is the candidate's religion?","ground_truth":"I don't have information about the candidate's religious beliefs. I can only provide professional and career-related information.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q070","question":"What is the candidate's credit score?","ground_truth":"I don't have information about the candidate's credit score. This is not part of the professional profile.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q071","question":"Is this candidate overqualified for a junior backend role?","ground_truth":"Absolutely. With 7 years of experience, MSc from TAU, architecture guild leadership of 8 engineers, systems processing 100B+ daily events, and published research, Tal is targeting a Principal Engineer role.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q072","question":"Would this candidate be a good fit for a remote backend role in Europe?","ground_truth":"Challenging. Tal prefers hybrid and is not open to relocation. However, he has exceptional distributed systems skills, 7 years of experience, and is fluent in English. A remote role from Herzliya might work.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q073","question":"Compare the candidate's academic and professional experience.","ground_truth":"Academically, Tal earned an MSc from TAU (90/100) with a thesis on consensus protocols published at SOSP Workshop. Professionally, 7 years progressing from Backend at Amdocs to Staff Engineer leading architecture at AppsFlyer, building systems processing 100B+ daily events.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q074","question":"What unique combination of skills does this candidate offer?","ground_truth":"Tal combines distributed systems theory (MSc, consensus protocols research) with extreme-scale engineering (1.2M events/sec, 100B+ daily), polyglot expertise (Java, Scala, Kotlin, Go, Clojure), architecture leadership (guild of 8), and open-source contribution (KafkaFlow, 250+ stars).","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q075","question":"Summarize why I should consider this candidate for a principal engineer position.","ground_truth":"Tal Ben-David: 7 years experience, Staff Engineer at AppsFlyer, systems processing 100B+ daily events, 1.2M events/sec pipeline, 99.99% uptime multi-region architecture, leads 8-engineer architecture guild, MSc from TAU with published research, Kafka certified, open-source contributor (KafkaFlow), available August 2026.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
]
