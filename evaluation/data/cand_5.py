SEED={"full_name":"Noa Friedman","email_address":"noa.friedman@gmail.com","country_code":"+972","phone_number":"54-777-8899","linkedin":"https://linkedin.com/in/noafriedman","github":"https://github.com/noafriedman","degree_title":"MBA","field_of_study":"Technology Management","institution":"Hebrew University of Jerusalem","graduation_year":"2021","gpa":"3.8/4.0","years_of_experience":"5","current_role":"Senior Product Manager at Unity","desired_job_title":"Director of Product","job_description":"Leading product strategy for Unity's monetization platform serving 1.5B monthly end-users. Managing a team of 3 PMs. Driving data-driven product decisions through A/B testing and analytics.","monthly_salary_expectation":"48,000 ILS","preferred_location":"Tel Aviv, Israel","availability":"October 2026","work_type":"Onsite","open_to_relocation":"Yes","skills":["SQL","Python","Tableau","Amplitude","Mixpanel"]}

CV="""# Noa Friedman — Curriculum Vitae

## Personal Information

- **Full Name:** Noa Friedman
- **Email:** noa.friedman@gmail.com
- **Phone:** +972 54-777-8899
- **Location:** Tel Aviv, Israel
- **LinkedIn:** https://linkedin.com/in/noafriedman
- **GitHub:** https://github.com/noafriedman

---

## Summary

Senior Product Manager with 5 years of experience driving product strategy for high-scale monetization and analytics platforms. Specialized in data-driven decision making, A/B testing at scale, and cross-functional team leadership. Background in both product management and data science enables deep technical collaboration with engineering teams. Proven track record of launching features impacting billions of end-users.

---

## Work Experience

### Senior Product Manager — Unity Technologies
**February 2023 – Present | Tel Aviv, Israel**

- Leading product strategy for Unity's in-app monetization platform serving 1.5B monthly end-users across mobile gaming.
- Managing a team of 3 product managers covering mediation, ad formats, and publisher analytics.
- Launched a machine learning-powered ad mediation algorithm increasing publisher revenue by 22%.
- Designed and shipped a real-time analytics dashboard used by 50K+ game developers worldwide.
- Drove the product roadmap for Unity LevelPlay (formerly ironSource), integrating post-acquisition product lines.
- Established experimentation culture running 100+ A/B tests per quarter with statistical rigor.
- Collaborated with ML engineering to build predictive LTV models improving user acquisition ROI by 18%.
- Presented product vision to C-suite and board, securing $5M budget for the analytics platform initiative.

### Product Manager — ironSource (acquired by Unity)
**September 2021 – January 2023 | Tel Aviv, Israel**

- Owned the SDK integration experience for ironSource's mediation platform used by 10K+ mobile app developers.
- Reduced SDK integration time from 5 days to 2 hours through redesigned onboarding and documentation.
- Built a self-service reporting tool enabling developers to analyze ad revenue with custom dimensions and filters.
- Launched bidding waterfall optimization feature increasing eCPM by 15% for publishers.
- Conducted 200+ customer interviews and managed a beta program with 50 enterprise publishers.
- Defined KPIs and OKRs for the mediation team, tracking adoption, revenue, and developer satisfaction.

---

## Education

### MBA — Hebrew University of Jerusalem
**2019 – 2021 | GPA: 3.8/4.0**

- Specialization: Technology Management and Innovation.
- MBA Project: Predictive Analytics for SaaS Churn — built a predictive model for B2B SaaS churn using product usage data. Achieved 88% accuracy with logistic regression and random forests. Grade: 96/100.
- Dean's List: 2020.
- Led the Technology Entrepreneurship Club organizing startup pitch competitions.

### Bachelor of Science in Industrial Engineering — Technion
**2014 – 2018 | GPA: 86/100**

- Relevant coursework: Statistics, Operations Research, Data Analysis, Human Factors, Systems Engineering.
- Graduated with honors.

---

## Technical Skills

**Product Tools:** Jira, Confluence, Productboard, Figma, Miro, Amplitude, Mixpanel

**Data & Analytics:** SQL, Python, Tableau, Looker, Google Analytics, BigQuery

**A/B Testing:** Optimizely, LaunchDarkly, custom experimentation platforms, statistical significance testing

**Technical Knowledge:** REST APIs, SDK architecture, mobile development lifecycle, ML model evaluation

**Methodologies:** Agile/Scrum, Design Thinking, Jobs-to-be-Done, OKRs, RICE prioritization

**Cloud & Infrastructure:** Basic AWS, GCP (BigQuery, Cloud Functions), data pipelines

---

## Projects

### ML-Powered Ad Mediation (Unity)
Led product development of a machine learning ad mediation algorithm that optimizes waterfall configurations in real-time. Increased publisher revenue by 22% compared to manual waterfall management. Collaborated with ML team on feature engineering and model evaluation. Scale: 1.5B monthly end-users.

### Real-Time Publisher Analytics Dashboard (Unity)
Designed and shipped a real-time analytics platform for 50K+ game developers to monitor ad revenue, user engagement, and monetization KPIs. Features include custom segmentation, anomaly detection alerts, and revenue forecasting.

### SDK Integration Redesign (ironSource)
Redesigned the SDK integration experience reducing integration time from 5 days to 2 hours. Included interactive setup wizard, automated validation, and contextual documentation. Resulted in 40% increase in developer adoption.

### Predictive LTV Modeling (Unity)
Collaborated with ML engineering to build user lifetime value prediction models for mobile games. Models improved user acquisition campaign ROI by 18% through better targeting. Technologies: Python, BigQuery, TensorFlow.

### Academic: SaaS Churn Prediction
MBA project building a churn prediction system for B2B SaaS products using product usage telemetry. Achieved 88% accuracy with ensemble methods. Presented findings to startup accelerator program.

---

## Certifications

1. **Pragmatic Institute Certified Product Manager (PMC)** (March 2022, Pragmatic Institute)
2. **Google Data Analytics Professional Certificate** (August 2021, Google via Coursera)
3. **Certified Scrum Product Owner (CSPO)** (May 2021, Scrum Alliance)

---

## Languages

- **Hebrew:** Native
- **English:** Fluent (professional proficiency)
- **Spanish:** Intermediate

---

## Interests

- Mentoring early-stage startup founders at the Hebrew University incubator
- Writing about product-led growth on Medium (2K+ followers)
- Competitive trivia and puzzle games
- Hiking and scuba diving
"""

README="""# Real-Time Publisher Analytics Dashboard

Real-time analytics platform for mobile game developers to monitor monetization performance.

## Overview

The Publisher Analytics Dashboard provides 50K+ game developers with real-time visibility into ad revenue, user engagement, and monetization KPIs. Built for Unity's monetization platform, it enables data-driven decision making with custom segmentation, anomaly detection, and revenue forecasting capabilities.

## Architecture

The platform consists of a streaming data pipeline (Kafka + Flink) for real-time event processing, a BigQuery data warehouse for historical analytics, and a React-based dashboard with interactive visualizations. Real-time metrics update every 30 seconds with sub-5-second latency for critical revenue events.

## Tech Stack

- **Frontend:** React, TypeScript, D3.js, Recharts
- **Backend:** Node.js, GraphQL, gRPC
- **Data Pipeline:** Apache Kafka, Apache Flink
- **Storage:** BigQuery, Redis, PostgreSQL
- **Infrastructure:** GCP (Cloud Run, Pub/Sub), Kubernetes
- **Monitoring:** Datadog, PagerDuty

## Installation

Internal Unity platform — not available for external installation.

## Usage

Publishers access the dashboard through the Unity Developer Portal. Configure custom segments, set anomaly detection thresholds, and create automated revenue reports. API access available for programmatic integration.

## Key Features

- Real-time ad revenue monitoring with 30-second refresh
- Custom segmentation by country, ad format, app version, and user cohort
- ML-powered anomaly detection with Slack/email alerts
- Revenue forecasting with confidence intervals
- Exportable reports in CSV and PDF formats
- Used by 50K+ game developers worldwide

## Performance

Processes 10B+ daily ad events with sub-5-second latency for real-time metrics. Dashboard page load time under 2 seconds. Supports concurrent access by thousands of publishers.

## Contributing

Internal Unity project. Feature requests managed through Productboard.

## License

Proprietary — Unity Technologies
"""

REC="""# Letter of Recommendation — Noa Friedman

**From:** Oren Kaniel, VP of Product at Unity Technologies
**Date:** May 18, 2026

---

To Whom It May Concern,

I am delighted to recommend Noa Friedman, who has been an exceptional product leader in our monetization organization at Unity for over three years. Noa joined from ironSource (pre-acquisition) and seamlessly transitioned into a senior leadership role.

Noa's most transformative contribution has been leading the ML-powered ad mediation product, which increased publisher revenue by 22%. She demonstrated rare ability to bridge product vision with ML engineering, defining clear success metrics and collaborating deeply on model evaluation. This feature impacts 1.5B monthly end-users, underscoring the scale of her responsibilities.

Her work on the real-time analytics dashboard has been equally impactful, giving 50K+ game developers unprecedented visibility into their monetization performance. Noa drove this initiative from concept through launch, managing cross-functional stakeholders across engineering, design, data science, and sales.

At ironSource, Noa redesigned the SDK integration experience, reducing setup time from 5 days to 2 hours — a change that drove 40% increase in developer adoption. Her customer empathy, honed through 200+ developer interviews, consistently informs her product decisions.

Noa is an outstanding people manager. She leads a team of 3 PMs with clarity, empathy, and high standards. She established our experimentation culture, running 100+ A/B tests per quarter with rigorous statistical methodology.

I wholeheartedly recommend Noa for a Director of Product role. She combines strategic product thinking, data literacy, technical depth, and people leadership in a way that is rare and valuable.

Sincerely,

**Oren Kaniel**
VP of Product
Unity Technologies
oren.kaniel@unity3d.com
"""

GOLDEN=[
    {"id":"q001","question":"What is the candidate's full name?","ground_truth":"Noa Friedman","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q002","question":"What is the candidate's email address?","ground_truth":"noa.friedman@gmail.com","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q003","question":"What is the candidate's phone number?","ground_truth":"+972 54-777-8899","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q004","question":"What is the candidate's LinkedIn profile?","ground_truth":"https://linkedin.com/in/noafriedman","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q005","question":"What is the candidate's GitHub profile URL?","ground_truth":"https://github.com/noafriedman","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q006","question":"How can I contact the candidate?","ground_truth":"You can contact Noa Friedman via email at noa.friedman@gmail.com, by phone at +972 54-777-8899, or through LinkedIn at https://linkedin.com/in/noafriedman.","expected_source":"structured","category":"personal","difficulty":"medium","expected_route":None},
    {"id":"q007","question":"What country is the candidate based in?","ground_truth":"Israel. The candidate is based in Tel Aviv, Israel.","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q008","question":"What is the candidate's country dialing code?","ground_truth":"+972","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q009","question":"What degree does the candidate hold?","ground_truth":"MBA in Technology Management from Hebrew University of Jerusalem, and BSc in Industrial Engineering from the Technion.","expected_source":"docs","category":"education","difficulty":"easy","expected_route":"specific"},
    {"id":"q010","question":"What did the candidate study?","ground_truth":"Technology Management (MBA) and Industrial Engineering (BSc)","expected_source":"docs","category":"education","difficulty":"easy","expected_route":"specific"},
    {"id":"q011","question":"Where did the candidate study?","ground_truth":"Hebrew University of Jerusalem (MBA) and Technion (BSc)","expected_source":"docs","category":"education","difficulty":"easy","expected_route":"specific"},
    {"id":"q012","question":"When did the candidate graduate?","ground_truth":"2021 (MBA) and 2018 (BSc)","expected_source":"docs","category":"education","difficulty":"easy","expected_route":"specific"},
    {"id":"q013","question":"What is the candidate's GPA?","ground_truth":"3.8/4.0 (MBA) and 86/100 (BSc)","expected_source":"docs","category":"education","difficulty":"easy","expected_route":"specific"},
    {"id":"q014","question":"Tell me about the candidate's educational background.","ground_truth":"Noa Friedman holds an MBA in Technology Management from Hebrew University (GPA 3.8/4.0) and a BSc in Industrial Engineering from the Technion (GPA 86/100, with honors). She was on the Dean's List in 2020 and led the Technology Entrepreneurship Club.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"broad"},
    {"id":"q015","question":"What was the candidate's MBA project about?","ground_truth":"The MBA project was Predictive Analytics for SaaS Churn — building a predictive model for B2B SaaS churn using product usage data. Achieved 88% accuracy with logistic regression and random forests. Grade: 96/100.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"specific"},
    {"id":"q016","question":"Did the candidate receive any academic honors?","ground_truth":"Yes, Noa was on the Dean's List in 2020 at Hebrew University and graduated with honors from the Technion BSc program.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"specific"},
    {"id":"q017","question":"How many years of experience does the candidate have?","ground_truth":"5 years of experience.","expected_source":"structured","category":"experience","difficulty":"easy","expected_route":None},
    {"id":"q018","question":"What is the candidate's current role?","ground_truth":"Senior Product Manager at Unity","expected_source":"structured","category":"experience","difficulty":"easy","expected_route":None},
    {"id":"q019","question":"Describe the candidate's current job responsibilities.","ground_truth":"Leading product strategy for Unity's monetization platform serving 1.5B monthly end-users. Managing a team of 3 PMs. Driving data-driven product decisions through A/B testing and analytics.","expected_source":"structured","category":"experience","difficulty":"medium","expected_route":None},
    {"id":"q020","question":"Where has the candidate worked previously?","ground_truth":"Before Unity, Noa worked as a Product Manager at ironSource (acquired by Unity) in Tel Aviv from September 2021 to January 2023.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q021","question":"What was the candidate's first job?","ground_truth":"Product Manager at ironSource (September 2021 – January 2023).","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q022","question":"Describe the candidate's work at ironSource.","ground_truth":"At ironSource, Noa owned the SDK integration experience for the mediation platform used by 10K+ developers, reduced integration time from 5 days to 2 hours, built a self-service reporting tool, launched bidding waterfall optimization increasing eCPM by 15%, and conducted 200+ customer interviews.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q023","question":"Has the candidate held a leadership role?","ground_truth":"Yes, Noa manages a team of 3 product managers at Unity covering mediation, ad formats, and publisher analytics. She also secured $5M budget for the analytics platform initiative.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q024","question":"What industries has the candidate worked in?","ground_truth":"Mobile gaming and ad-tech (Unity/ironSource — monetization platforms and developer tools).","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q025","question":"What is a key technical achievement the candidate accomplished?","ground_truth":"Noa launched an ML-powered ad mediation algorithm increasing publisher revenue by 22% across 1.5B monthly end-users, and reduced SDK integration time from 5 days to 2 hours driving 40% increase in developer adoption.","expected_source":"docs","category":"experience","difficulty":"hard","expected_route":"specific"},
    {"id":"q026","question":"Has the candidate had any mentoring experience?","ground_truth":"Yes, Noa mentors early-stage startup founders at the Hebrew University incubator and led the Technology Entrepreneurship Club during her MBA.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q027","question":"What programming languages does the candidate know?","ground_truth":"SQL and Python.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q028","question":"What are the candidate's primary product tools?","ground_truth":"Jira, Confluence, Productboard, Figma, Miro, Amplitude, Mixpanel, Optimizely, and LaunchDarkly.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q029","question":"What cloud platforms does the candidate have experience with?","ground_truth":"Basic AWS and GCP (BigQuery, Cloud Functions).","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q030","question":"What data and analytics tools does the candidate use?","ground_truth":"SQL, Python, Tableau, Looker, Google Analytics, BigQuery, Amplitude, and Mixpanel.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q031","question":"Does the candidate have technical knowledge?","ground_truth":"Yes, Noa has knowledge of REST APIs, SDK architecture, mobile development lifecycle, ML model evaluation, and data pipelines, enabling deep collaboration with engineering teams.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q032","question":"Does the candidate know Python?","ground_truth":"Yes, Noa uses Python for data analysis and built a churn prediction model with Python during her MBA project.","expected_source":"docs","accept_sources":["skill"],"category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q033","question":"Does the candidate have A/B testing experience?","ground_truth":"Yes, extensive A/B testing experience with Optimizely, LaunchDarkly, and custom experimentation platforms. Established an experimentation culture running 100+ A/B tests per quarter with statistical rigor.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q034","question":"Does the candidate have data analytics experience?","ground_truth":"Yes, strong data analytics background with SQL, Python, Tableau, Looker, Amplitude, BigQuery, and Google Analytics. Built predictive models and analytics dashboards.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q035","question":"What product management methodologies does the candidate use?","ground_truth":"Agile/Scrum, Design Thinking, Jobs-to-be-Done, OKRs, and RICE prioritization.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q036","question":"Does the candidate have user research experience?","ground_truth":"Yes, Noa conducted 200+ customer interviews at ironSource and managed a beta program with 50 enterprise publishers. She also participated in design sprints.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q037","question":"Does the candidate have experience with ML products?","ground_truth":"Yes, Noa led the ML-powered ad mediation product and collaborated with ML engineering on predictive LTV models. She has knowledge of ML model evaluation.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q038","question":"What visualization and reporting tools does the candidate know?","ground_truth":"Tableau, Looker, Amplitude, Mixpanel, Google Analytics, and D3.js/Recharts (from the analytics dashboard project).","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q039","question":"What projects has the candidate worked on?","ground_truth":"ML-Powered Ad Mediation, Real-Time Publisher Analytics Dashboard, SDK Integration Redesign, Predictive LTV Modeling, and Academic SaaS Churn Prediction.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"broad"},
    {"id":"q040","question":"Tell me about the ad mediation project.","ground_truth":"Led product development of an ML ad mediation algorithm optimizing waterfall configurations in real-time. Increased publisher revenue by 22%. Collaborated with ML team on feature engineering and model evaluation. Scale: 1.5B monthly end-users.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q041","question":"What was the outcome of the analytics dashboard project?","ground_truth":"The real-time analytics dashboard is used by 50K+ game developers worldwide to monitor ad revenue, user engagement, and monetization KPIs with custom segmentation and anomaly detection alerts.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q042","question":"What technologies were used in the LTV modeling project?","ground_truth":"Python, BigQuery, and TensorFlow.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q043","question":"What is the candidate's most significant project?","ground_truth":"The ML-Powered Ad Mediation at Unity, increasing publisher revenue by 22% across 1.5B monthly end-users, or the Real-Time Analytics Dashboard used by 50K+ game developers.","expected_source":"docs","category":"projects","difficulty":"hard","expected_route":"specific"},
    {"id":"q044","question":"Has the candidate contributed to open-source projects?","ground_truth":"Noa does not have notable open-source contributions, but she has a GitHub profile and writes about product-led growth on Medium with 2K+ followers.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q045","question":"What products has the candidate built or launched?","ground_truth":"ML ad mediation algorithm (22% revenue increase), real-time analytics dashboard (50K+ users), SDK integration redesign (5 days to 2 hours), self-service reporting tool, and bidding waterfall optimization (15% eCPM increase).","expected_source":"docs","category":"projects","difficulty":"hard","expected_route":"specific"},
    {"id":"q046","question":"Does the candidate have monetization experience?","ground_truth":"Yes, Noa leads Unity's monetization platform serving 1.5B end-users, launched ML ad mediation increasing revenue by 22%, and optimized bidding waterfalls increasing eCPM by 15%.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q047","question":"Has the candidate worked on developer-facing products?","ground_truth":"Yes, Noa redesigned SDK integration reducing setup from 5 days to 2 hours for 10K+ developers, built a self-service reporting tool, and shipped an analytics dashboard for 50K+ game developers.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q048","question":"What is the scale of products the candidate has managed?","ground_truth":"Noa manages products serving 1.5B monthly end-users, 50K+ game developers, and 10K+ mobile app developers, running 100+ A/B tests per quarter.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q049","question":"What certifications does the candidate have?","ground_truth":"Pragmatic Institute Certified Product Manager — PMC (March 2022), Google Data Analytics Professional Certificate (August 2021), and Certified Scrum Product Owner — CSPO (May 2021).","expected_source":"docs","category":"certifications","difficulty":"medium","expected_route":"specific"},
    {"id":"q050","question":"Does the candidate have a product management certification?","ground_truth":"Yes, Noa holds the Pragmatic Institute Certified Product Manager (PMC) certification, obtained in March 2022.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q051","question":"Does the candidate have a data analytics certification?","ground_truth":"Yes, Noa holds the Google Data Analytics Professional Certificate, obtained in August 2021.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q052","question":"When did the candidate get their Scrum certification?","ground_truth":"May 2021.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q053","question":"Does the candidate have any management or methodology certifications?","ground_truth":"Yes, Noa holds the Certified Scrum Product Owner (CSPO) from Scrum Alliance and the Pragmatic Institute Certified Product Manager (PMC).","expected_source":"docs","category":"certifications","difficulty":"medium","expected_route":"specific"},
    {"id":"q054","question":"What is the candidate's salary expectation?","ground_truth":"48,000 ILS per month.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q055","question":"Where does the candidate prefer to work?","ground_truth":"Tel Aviv, Israel.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q056","question":"When is the candidate available to start?","ground_truth":"October 2026.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q057","question":"Does the candidate prefer remote, hybrid, or onsite work?","ground_truth":"Onsite.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q058","question":"Is the candidate open to relocation?","ground_truth":"Yes.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q059","question":"What job title is the candidate looking for?","ground_truth":"Director of Product.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q060","question":"Would the candidate work fully onsite?","ground_truth":"Yes, the candidate prefers onsite work and is open to relocation.","expected_source":"structured","category":"preferences","difficulty":"medium","expected_route":None},
    {"id":"q061","question":"When can the candidate start working?","ground_truth":"October 2026.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q062","question":"How proficient is the candidate in SQL?","ground_truth":"The candidate has a verified, model-estimated proficiency level (1-5) in SQL, inferred from her documents with supporting evidence. SQL is a well-evidenced data skill used for analytics, reporting, and predictive modelling.","expected_source":"skill","category":"proficiency","difficulty":"easy","expected_route":None},
    {"id":"q063","question":"Rate the candidate's Tableau skills.","ground_truth":"Provides a model-estimated 1-5 proficiency level for Tableau, inferred from the documents with evidence. Tableau is listed among her data and analytics visualization tools.","expected_source":"skill","category":"proficiency","difficulty":"medium","expected_route":None},
    {"id":"q064","question":"What are the candidate's strongest skills?","ground_truth":"Provides a ranked list of the candidate's assessed skills (SQL, Python, Tableau, Amplitude, Mixpanel) with their estimated 1-5 proficiency levels, inferred from the documents.","expected_source":"skill","category":"proficiency","difficulty":"medium","expected_route":None},
    {"id":"q065","question":"How strong is the candidate at Looker?","ground_truth":"Looker is not among the explicitly assessed skills, so this is answered from the documents: Looker is listed among the candidate's data and analytics tools.","expected_source":"docs","category":"proficiency","difficulty":"medium","expected_route":None},
    {"id":"q066","question":"What is the candidate's blood type?","ground_truth":"I don't have information about the candidate's blood type. This is not part of the professional profile.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q067","question":"What are the candidate's political opinions?","ground_truth":"I don't have information about the candidate's political views. I can only provide professional and career-related information.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q068","question":"Is the candidate married?","ground_truth":"I don't have information about the candidate's marital status. I can only share professional profile details.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q069","question":"What is the candidate's religion?","ground_truth":"I don't have information about the candidate's religious beliefs. I can only provide professional and career-related information.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q070","question":"What is the candidate's credit score?","ground_truth":"I don't have information about the candidate's credit score. This is not part of the professional profile.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q071","question":"Is this candidate overqualified for a junior product manager role?","ground_truth":"Likely yes. With 5 years of PM experience, managing a team of 3 PMs at Unity, MBA from Hebrew University, products impacting 1.5B users, and multiple PM certifications, Noa would be overqualified for a junior position. She is targeting a Director of Product role.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q072","question":"Would this candidate be a good fit for a remote product role in Europe?","ground_truth":"Potentially, though Noa prefers onsite work. She is open to relocation, has strong product skills, 5 years of experience, speaks English fluently plus intermediate Spanish, and has worked on global-scale products. She may adapt to remote work for the right opportunity.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q073","question":"Compare the candidate's academic and professional experience.","ground_truth":"Academically, Noa holds an MBA from Hebrew University (GPA 3.8/4.0) and BSc in Industrial Engineering from the Technion (86/100, with honors). Professionally, she has 5 years of PM experience progressing from PM at ironSource to Senior PM leading a team at Unity, managing products impacting 1.5B users.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q074","question":"What unique combination of skills does this candidate offer?","ground_truth":"Noa combines product leadership (team of 3 PMs, $5M budget) with data science literacy (Python, SQL, predictive modeling), deep ad-tech domain expertise (monetization, mediation, LTV), experimentation rigor (100+ A/B tests/quarter), and strong customer empathy (200+ interviews). She bridges business strategy and technical execution.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q075","question":"Summarize why I should consider this candidate for a director of product position.","ground_truth":"Noa Friedman is a strong candidate: 5 years of PM experience, leads team of 3 PMs at Unity, products serving 1.5B end-users, launched ML mediation increasing revenue by 22%, analytics dashboard used by 50K+ devs, MBA from Hebrew University (3.8 GPA), PMC and CSPO certified, data-driven with SQL/Python skills, and available from October 2026.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
]
