SEED={"full_name":"Maya Chen","email_address":"maya.chen@gmail.com","country_code":"+972","phone_number":"53-444-5566","linkedin":"https://linkedin.com/in/mayachen","github":"https://github.com/mayachen","degree_title":"Bachelor's","field_of_study":"Computer Science","institution":"Reichman University (IDC Herzliya)","graduation_year":"2022","gpa":"91/100","years_of_experience":"3","current_role":"Frontend Engineer at Fiverr","desired_job_title":"Senior Frontend Engineer","job_description":"Building high-performance React applications for Fiverr's marketplace platform. Leading the design system team. Implementing accessibility standards across 20+ product surfaces.","monthly_salary_expectation":"32,000 ILS","preferred_location":"Tel Aviv, Israel","availability":"July 2026","work_type":"Hybrid","open_to_relocation":"No","skills":["React","TypeScript","CSS3","Python","Docker"]}

CV="""# Maya Chen — Curriculum Vitae

## Personal Information

- **Full Name:** Maya Chen
- **Email:** maya.chen@gmail.com
- **Phone:** +972 53-444-5566
- **Location:** Tel Aviv, Israel
- **LinkedIn:** https://linkedin.com/in/mayachen
- **GitHub:** https://github.com/mayachen

---

## Summary

Frontend Engineer with 3 years of experience building performant, accessible web applications at scale. Specialized in React, TypeScript, and design systems. Passionate about web performance optimization, component-driven architecture, and inclusive design. Track record of improving Core Web Vitals and delivering pixel-perfect UIs in fast-paced product environments.

---

## Work Experience

### Frontend Engineer — Fiverr
**June 2022 – Present | Tel Aviv, Israel**

- Building high-performance React applications for Fiverr's marketplace serving 4M+ monthly active users.
- Leading the design system team, maintaining a shared component library used by 80+ frontend engineers.
- Improved Largest Contentful Paint (LCP) by 40% through code splitting, lazy loading, and image optimization.
- Implemented WCAG 2.1 AA accessibility standards across 20+ product surfaces, achieving full compliance audit pass.
- Built a real-time collaborative editing feature for gig descriptions using WebSockets and CRDT algorithms.
- Reduced JavaScript bundle size by 35% through tree shaking, dynamic imports, and dependency audit.
- Developed A/B testing framework enabling product teams to run 50+ experiments concurrently.
- Mentored 3 junior frontend developers through code reviews and pair programming sessions.

### Junior Frontend Developer — Wix.com
**January 2022 – May 2022 | Tel Aviv, Israel**

- Developed responsive UI components for Wix's template marketplace using React and Styled Components.
- Built interactive data visualization dashboards with D3.js for the analytics product.
- Implemented micro-frontend architecture for the Wix App Market using Module Federation.
- Contributed to the Wix Design System, creating 10+ reusable accessible components.
- Participated in design sprints and user research sessions with UX team.
- Wrote comprehensive unit and integration tests with Jest and React Testing Library.

---

## Education

### Bachelor of Science in Computer Science — Reichman University (IDC Herzliya)
**2018 – 2022 | GPA: 91/100**

- Relevant coursework: Web Technologies, UI/UX Design, Algorithms, Data Structures, Human-Computer Interaction, Mobile Development, Software Engineering.
- Capstone Project: AccessiCheck — an AI-powered web accessibility audit tool that crawls websites and generates WCAG compliance reports with auto-fix suggestions. Grade: 95/100.
- Dean's List: 2020, 2021.
- President of the Web Development Club (2020-2022).

---

## Technical Skills

**Programming Languages:** TypeScript, JavaScript, HTML5, CSS3, Python

**Frontend Frameworks:** React, Next.js, Vue.js, Svelte

**State Management:** Redux, Zustand, React Query, Apollo Client

**Styling:** CSS Modules, Styled Components, Tailwind CSS, Sass, CSS-in-JS

**Testing:** Jest, React Testing Library, Cypress, Playwright, Storybook

**Build Tools:** Webpack, Vite, esbuild, Turborepo

**Design Tools:** Figma, Storybook, Chromatic

**Backend & APIs:** Node.js, Express, GraphQL, REST, WebSockets

**Databases:** PostgreSQL, MongoDB, Redis

**DevOps:** Docker, GitHub Actions, Vercel, Netlify, AWS (S3, CloudFront, Lambda)

---

## Projects

### Fiverr Design System (Fiverr)
Led development of a shared component library used by 80+ frontend engineers. Built with React, TypeScript, and Storybook. Includes 60+ accessible components with automated visual regression testing via Chromatic. Reduced UI development time by 40%.

### Real-time Collaborative Editor (Fiverr)
Built a collaborative editing feature for gig descriptions using WebSockets, CRDT algorithms (Yjs), and React. Supports concurrent editing by multiple sellers with conflict resolution and presence indicators. Technologies: React, TypeScript, Yjs, WebSockets, Node.js.

### Web Performance Optimization Suite (Fiverr)
Developed an internal performance monitoring and optimization toolkit. Automated Core Web Vitals tracking, bundle analysis, and performance regression detection in CI. Improved LCP by 40% and reduced bundle size by 35%.

### Open-Source: ReactA11y Hooks
Created an open-source library of React hooks for common accessibility patterns (focus management, keyboard navigation, live regions, screen reader announcements). 300+ stars on GitHub. Technologies: React, TypeScript.

### Academic Capstone: AccessiCheck
Built an AI-powered accessibility audit tool that crawls websites and generates WCAG 2.1 compliance reports with actionable auto-fix suggestions using NLP. Technologies: Python, React, Playwright, GPT API. Grade: 95/100.

---

## Certifications

1. **Google Professional Cloud Developer** (March 2024, Google Cloud)
2. **Web Accessibility Specialist (WAS)** (November 2023, IAAP)
3. **Meta Frontend Developer Professional Certificate** (June 2022, Meta via Coursera)

---

## Languages

- **Hebrew:** Native
- **English:** Fluent (professional proficiency)
- **Mandarin:** Conversational (heritage speaker)

---

## Interests

- Contributing to accessibility-focused open-source projects
- Speaking at frontend meetups (React Israel, CSS Day)
- Digital illustration and generative art with p5.js
- Yoga and indoor climbing
"""

README="""# Fiverr Design System

A comprehensive, accessible component library powering Fiverr's marketplace UI.

## Overview

The Fiverr Design System is a shared component library used by 80+ frontend engineers across 20+ product surfaces. Built with React, TypeScript, and Storybook, it provides 60+ accessible components with automated visual regression testing and comprehensive documentation.

## Architecture

The system uses a monorepo architecture with Turborepo, organizing components into three tiers: Primitives (atoms like Button, Input, Typography), Composites (molecules like SearchBar, Card, Modal), and Patterns (organisms like Navigation, DataTable, FormWizard). Each component follows the Compound Component pattern for maximum flexibility.

## Tech Stack

- **Framework:** React 18 with TypeScript
- **Styling:** CSS Modules + design tokens
- **Documentation:** Storybook 7
- **Testing:** Jest, React Testing Library, Chromatic
- **Build:** Turborepo, Rollup, esbuild
- **CI/CD:** GitHub Actions, npm registry
- **Accessibility:** axe-core, WCAG 2.1 AA

## Installation

```bash
npm install @fiverr/design-system
```

## Usage

Import components and use with TypeScript type safety. All components support theme customization via CSS custom properties and design tokens. Storybook provides interactive documentation and playground.

## Key Features

- 60+ fully accessible React components
- Automated visual regression testing with Chromatic
- Design token system with light and dark themes
- Compound component patterns for composability
- Full WCAG 2.1 AA compliance
- 40% reduction in UI development time

## Performance

All components are tree-shakeable with individual exports. Average component bundle size under 5KB gzipped. Storybook loads in under 3 seconds with lazy story loading.

## Contributing

Follow the contribution guide in CONTRIBUTING.md. All components must include accessibility tests, Storybook stories, and TypeScript types.

## License

MIT License
"""

REC="""# Letter of Recommendation — Maya Chen

**From:** Lior Barak, Frontend Team Lead at Fiverr
**Date:** May 25, 2026

---

To Whom It May Concern,

I am delighted to recommend Maya Chen, who has been an exceptional member of our frontend engineering team at Fiverr for the past three years. Maya joined us straight from university and has rapidly become one of our most impactful engineers.

Maya's standout achievement has been leading our design system initiative. She built and maintains a component library used by 80+ engineers, with 60+ accessible components that have reduced UI development time by 40%. Her deep knowledge of accessibility standards led to our marketplace achieving full WCAG 2.1 AA compliance across 20+ product surfaces.

Her work on web performance has been equally impressive. Maya improved our Largest Contentful Paint by 40% and reduced JavaScript bundle size by 35%, directly impacting user experience for 4M+ monthly active users. She also built our real-time collaborative editor using cutting-edge CRDT algorithms.

Maya is a natural mentor and community builder. She regularly mentors junior developers, speaks at frontend meetups, and contributes to open-source accessibility tools. Her ReactA11y Hooks library has gained 300+ stars on GitHub and is used by teams outside Fiverr.

I strongly recommend Maya for a senior frontend engineering role. She combines deep technical expertise with a passion for accessible, performant web experiences and genuine leadership ability.

Sincerely,

**Lior Barak**
Frontend Team Lead
Fiverr
lior.barak@fiverr.com
"""

GOLDEN=[
    {"id":"q001","question":"What is the candidate's full name?","ground_truth":"Maya Chen","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q002","question":"What is the candidate's email address?","ground_truth":"maya.chen@gmail.com","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q003","question":"What is the candidate's phone number?","ground_truth":"+972 53-444-5566","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q004","question":"What is the candidate's LinkedIn profile?","ground_truth":"https://linkedin.com/in/mayachen","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q005","question":"What is the candidate's GitHub profile URL?","ground_truth":"https://github.com/mayachen","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q006","question":"How can I contact the candidate?","ground_truth":"You can contact Maya Chen via email at maya.chen@gmail.com, by phone at +972 53-444-5566, or through LinkedIn at https://linkedin.com/in/mayachen.","expected_source":"structured","category":"personal","difficulty":"medium","expected_route":None},
    {"id":"q007","question":"What country is the candidate based in?","ground_truth":"Israel. The candidate is based in Tel Aviv, Israel.","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q008","question":"What is the candidate's country dialing code?","ground_truth":"+972","expected_source":"structured","category":"personal","difficulty":"easy","expected_route":None},
    {"id":"q009","question":"What degree does the candidate hold?","ground_truth":"Bachelor's degree in Computer Science from Reichman University (IDC Herzliya).","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q010","question":"What did the candidate study?","ground_truth":"Computer Science","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q011","question":"Where did the candidate study?","ground_truth":"Reichman University (IDC Herzliya)","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q012","question":"When did the candidate graduate?","ground_truth":"2022","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q013","question":"What is the candidate's GPA?","ground_truth":"91/100","expected_source":"structured","category":"education","difficulty":"easy","expected_route":None},
    {"id":"q014","question":"Tell me about the candidate's educational background.","ground_truth":"Maya Chen holds a Bachelor's degree in Computer Science from Reichman University, graduating in 2022 with a GPA of 91/100. She was on the Dean's List in 2020 and 2021, and served as President of the Web Development Club.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"broad"},
    {"id":"q015","question":"What was the candidate's capstone project about?","ground_truth":"The capstone project was AccessiCheck — an AI-powered web accessibility audit tool that crawls websites and generates WCAG compliance reports with auto-fix suggestions using NLP. Built with Python, React, Playwright, GPT API. Grade: 95/100.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"specific"},
    {"id":"q016","question":"Did the candidate receive any academic honors?","ground_truth":"Yes, Maya was on the Dean's List in 2020 and 2021 at Reichman University.","expected_source":"docs","category":"education","difficulty":"medium","expected_route":"specific"},
    {"id":"q017","question":"How many years of experience does the candidate have?","ground_truth":"3 years of experience.","expected_source":"structured","category":"experience","difficulty":"easy","expected_route":None},
    {"id":"q018","question":"What is the candidate's current role?","ground_truth":"Frontend Engineer at Fiverr","expected_source":"structured","category":"experience","difficulty":"easy","expected_route":None},
    {"id":"q019","question":"Describe the candidate's current job responsibilities.","ground_truth":"Building high-performance React applications for Fiverr's marketplace platform. Leading the design system team. Implementing accessibility standards across 20+ product surfaces.","expected_source":"structured","category":"experience","difficulty":"medium","expected_route":None},
    {"id":"q020","question":"Where has the candidate worked previously?","ground_truth":"Before Fiverr, Maya worked as a Junior Frontend Developer at Wix.com in Tel Aviv from January 2022 to May 2022.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q021","question":"What was the candidate's first job?","ground_truth":"Junior Frontend Developer at Wix.com (January 2022 – May 2022).","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q022","question":"Describe the candidate's work at Wix.","ground_truth":"At Wix, Maya developed responsive UI components for the template marketplace using React and Styled Components, built D3.js data visualization dashboards, implemented micro-frontend architecture using Module Federation, and contributed 10+ components to the Wix Design System.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q023","question":"Has the candidate held a leadership role?","ground_truth":"Yes, Maya leads the design system team at Fiverr maintaining a shared component library used by 80+ engineers. She also mentors 3 junior frontend developers.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q024","question":"What industries has the candidate worked in?","ground_truth":"Online marketplace/freelancing platform (Fiverr) and web publishing/website builder (Wix.com).","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q025","question":"What is a key technical achievement the candidate accomplished?","ground_truth":"Maya improved Largest Contentful Paint by 40% through code splitting and optimization, and reduced JavaScript bundle size by 35%, directly impacting UX for 4M+ monthly active users.","expected_source":"docs","category":"experience","difficulty":"hard","expected_route":"specific"},
    {"id":"q026","question":"Has the candidate had any teaching or mentoring experience?","ground_truth":"Yes, Maya mentors 3 junior frontend developers through code reviews and pair programming at Fiverr. She was also President of the Web Development Club at Reichman University and speaks at frontend meetups.","expected_source":"docs","category":"experience","difficulty":"medium","expected_route":"specific"},
    {"id":"q027","question":"What programming languages does the candidate know?","ground_truth":"TypeScript, JavaScript, HTML5, CSS3, and Python.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q028","question":"What are the candidate's primary technical frameworks and tools?","ground_truth":"React, Next.js, Vue.js, Svelte, Redux, Zustand, React Query, Apollo Client, Storybook, and Chromatic.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q029","question":"What cloud platforms does the candidate have experience with?","ground_truth":"AWS (S3, CloudFront, Lambda), Vercel, and Netlify.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q030","question":"What databases has the candidate worked with?","ground_truth":"PostgreSQL, MongoDB, and Redis.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q031","question":"Does the candidate have DevOps experience?","ground_truth":"Yes, Maya has experience with Docker, GitHub Actions, Vercel, Netlify, and AWS deployment. She also built performance regression detection in CI pipelines.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q032","question":"Does the candidate know Python?","ground_truth":"Yes, Python is one of Maya's programming languages, used in her AccessiCheck capstone project for web crawling and NLP-based accessibility analysis.","expected_source":"docs","accept_sources":["skill"],"category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q033","question":"Does the candidate have experience with React?","ground_truth":"Yes, React is Maya's primary framework. She builds high-performance React applications at Fiverr, leads the React-based design system with 60+ components, and created the ReactA11y Hooks open-source library.","expected_source":"docs","accept_sources":["skill"],"category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q034","question":"Does the candidate have testing experience?","ground_truth":"Yes, extensive testing experience with Jest, React Testing Library, Cypress, Playwright, and Storybook with Chromatic for automated visual regression testing.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q035","question":"What accessibility experience does the candidate have?","ground_truth":"Extensive accessibility expertise including WCAG 2.1 AA implementation across 20+ product surfaces, WAS certification from IAAP, AccessiCheck capstone project, and ReactA11y Hooks open-source library with 300+ GitHub stars.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q036","question":"Does the candidate have design system experience?","ground_truth":"Yes, Maya leads Fiverr's design system with 60+ accessible React components, Storybook documentation, Chromatic visual regression testing, and design tokens. Also contributed 10+ components to Wix's design system.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q037","question":"Does the candidate have experience with build tools?","ground_truth":"Yes, Maya has experience with Webpack, Vite, esbuild, Turborepo, and Rollup. She reduced bundle size by 35% through tree shaking and dynamic imports.","expected_source":"docs","category":"skills","difficulty":"easy","expected_route":"specific"},
    {"id":"q038","question":"What backend and API skills does the candidate have?","ground_truth":"Node.js, Express, GraphQL, REST, and WebSockets.","expected_source":"docs","category":"skills","difficulty":"medium","expected_route":"specific"},
    {"id":"q039","question":"What projects has the candidate worked on?","ground_truth":"Fiverr Design System, Real-time Collaborative Editor, Web Performance Optimization Suite, Open-Source ReactA11y Hooks, and Academic Capstone AccessiCheck.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"broad"},
    {"id":"q040","question":"Tell me about the design system project.","ground_truth":"Led development of a shared React component library used by 80+ engineers with 60+ accessible components, Storybook documentation, Chromatic visual regression testing, and design token system. Reduced UI development time by 40%. Technologies: React, TypeScript, Storybook, Turborepo.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q041","question":"What was the outcome of the collaborative editor project?","ground_truth":"Built a real-time collaborative editing feature for gig descriptions supporting concurrent editing by multiple sellers using CRDT algorithms (Yjs) with conflict resolution and presence indicators.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q042","question":"What technologies were used in the performance optimization project?","ground_truth":"Code splitting, lazy loading, tree shaking, dynamic imports, Core Web Vitals tracking, and CI-integrated bundle analysis.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q043","question":"What is the candidate's most significant project?","ground_truth":"The Fiverr Design System used by 80+ engineers with 60+ accessible components reducing UI development time by 40%, or the web performance work improving LCP by 40% for 4M+ users.","expected_source":"docs","category":"projects","difficulty":"hard","expected_route":"specific"},
    {"id":"q044","question":"Has the candidate contributed to open-source projects?","ground_truth":"Yes, Maya created ReactA11y Hooks, an open-source library of React hooks for accessibility patterns (focus management, keyboard navigation, live regions). It has 300+ stars on GitHub.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q045","question":"What systems has the candidate built?","ground_truth":"Design system with 60+ components for 80+ engineers, real-time collaborative editor with CRDT, web performance optimization toolkit, A/B testing framework for 50+ concurrent experiments, and ReactA11y Hooks library.","expected_source":"docs","category":"projects","difficulty":"hard","expected_route":"specific"},
    {"id":"q046","question":"Does the candidate have web performance experience?","ground_truth":"Yes, Maya improved LCP by 40%, reduced bundle size by 35%, and built an internal performance monitoring toolkit with automated Core Web Vitals tracking and regression detection in CI.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q047","question":"Has the candidate worked on real-time applications?","ground_truth":"Yes, Maya built a real-time collaborative editing feature using WebSockets and CRDT algorithms (Yjs) with concurrent editing support and presence indicators.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q048","question":"What is the scale of systems the candidate has worked with?","ground_truth":"Maya works on Fiverr's marketplace serving 4M+ monthly active users, maintains a design system used by 80+ engineers, and built an A/B testing framework supporting 50+ concurrent experiments.","expected_source":"docs","category":"projects","difficulty":"medium","expected_route":"specific"},
    {"id":"q049","question":"What certifications does the candidate have?","ground_truth":"Google Professional Cloud Developer (March 2024), Web Accessibility Specialist — WAS (November 2023, IAAP), and Meta Frontend Developer Professional Certificate (June 2022).","expected_source":"docs","category":"certifications","difficulty":"medium","expected_route":"specific"},
    {"id":"q050","question":"Does the candidate have a Google Cloud certification?","ground_truth":"Yes, Maya holds the Google Professional Cloud Developer certification, obtained in March 2024.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q051","question":"Does the candidate have an accessibility certification?","ground_truth":"Yes, Maya holds the Web Accessibility Specialist (WAS) certification from IAAP, obtained in November 2023.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q052","question":"When did the candidate get their Meta certification?","ground_truth":"June 2022.","expected_source":"docs","category":"certifications","difficulty":"easy","expected_route":"specific"},
    {"id":"q053","question":"Does the candidate have any management certifications?","ground_truth":"Maya does not hold a specific management certification, though her Google Professional Cloud Developer covers architectural design aspects.","expected_source":"docs","category":"certifications","difficulty":"medium","expected_route":"specific"},
    {"id":"q054","question":"What is the candidate's salary expectation?","ground_truth":"32,000 ILS per month.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q055","question":"Where does the candidate prefer to work?","ground_truth":"Tel Aviv, Israel.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q056","question":"When is the candidate available to start?","ground_truth":"July 2026.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q057","question":"Does the candidate prefer remote, hybrid, or onsite work?","ground_truth":"Hybrid.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q058","question":"Is the candidate open to relocation?","ground_truth":"No.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q059","question":"What job title is the candidate looking for?","ground_truth":"Senior Frontend Engineer.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q060","question":"Would the candidate work fully onsite?","ground_truth":"The candidate prefers hybrid work and is not open to relocation, so a fully onsite role would need to be in the Tel Aviv area.","expected_source":"structured","category":"preferences","difficulty":"medium","expected_route":None},
    {"id":"q061","question":"When can the candidate start working?","ground_truth":"July 2026.","expected_source":"structured","category":"preferences","difficulty":"easy","expected_route":None},
    {"id":"q062","question":"How proficient is the candidate in React?","ground_truth":"The candidate has a verified, model-estimated proficiency level (1-5) in React, inferred from her documents with supporting evidence. React is a core, strongly-evidenced skill — she leads a React design system of 60+ components and built the ReactA11y Hooks library.","expected_source":"skill","category":"proficiency","difficulty":"easy","expected_route":None},
    {"id":"q063","question":"Rate the candidate's TypeScript skills.","ground_truth":"Provides a model-estimated 1-5 proficiency level for TypeScript, inferred from the documents with evidence. TypeScript is well-evidenced — used across her React applications and the Fiverr design system.","expected_source":"skill","category":"proficiency","difficulty":"medium","expected_route":None},
    {"id":"q064","question":"What are the candidate's strongest skills?","ground_truth":"Provides a ranked list of the candidate's assessed skills (React, TypeScript, CSS3, Python, Docker) with their estimated 1-5 proficiency levels, inferred from the documents.","expected_source":"skill","category":"proficiency","difficulty":"medium","expected_route":None},
    {"id":"q065","question":"How strong is the candidate at PostgreSQL?","ground_truth":"PostgreSQL is not among the explicitly assessed skills, so this is answered from the documents: PostgreSQL is listed among the databases Maya has worked with.","expected_source":"docs","category":"proficiency","difficulty":"medium","expected_route":None},
    {"id":"q066","question":"What is the candidate's blood type?","ground_truth":"I don't have information about the candidate's blood type. This is not part of the professional profile.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q067","question":"What are the candidate's political opinions?","ground_truth":"I don't have information about the candidate's political views. I can only provide professional and career-related information.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q068","question":"Is the candidate married?","ground_truth":"I don't have information about the candidate's marital status. I can only share professional profile details.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q069","question":"What is the candidate's religion?","ground_truth":"I don't have information about the candidate's religious beliefs. I can only provide professional and career-related information.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q070","question":"What is the candidate's credit score?","ground_truth":"I don't have information about the candidate's credit score. This is not part of the professional profile.","expected_source":"none","category":"negative","difficulty":"easy","expected_route":None},
    {"id":"q071","question":"Is this candidate overqualified for a junior frontend role?","ground_truth":"Likely yes. With 3 years of experience, design system leadership for 80+ engineers, web performance expertise impacting 4M+ users, WAS certification, and mentoring experience, Maya would be overqualified for a junior position. She is targeting a Senior Frontend Engineer role.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q072","question":"Would this candidate be a good fit for a remote frontend role in Europe?","ground_truth":"Potentially challenging. Maya prefers hybrid work and is not open to relocation. However, she has strong React and TypeScript skills, accessibility expertise, 3 years of experience, and is fluent in English. A remote role from Tel Aviv might work if the company allows it.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q073","question":"Compare the candidate's academic and professional experience.","ground_truth":"Academically, Maya earned a BSc in Computer Science from Reichman University with a 91/100 GPA, was on the Dean's List, and built AccessiCheck as her capstone. Professionally, she has 3 years of experience progressing from Junior Frontend at Wix to Frontend Engineer leading a design system at Fiverr, building for 4M+ users.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q074","question":"What unique combination of skills does this candidate offer?","ground_truth":"Maya combines deep React/TypeScript expertise with design system architecture, web accessibility specialization (WAS certified), web performance optimization (40% LCP improvement), real-time collaboration (CRDT/WebSockets), and open-source leadership. She bridges design and engineering.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
    {"id":"q075","question":"Summarize why I should consider this candidate for a senior frontend engineer position.","ground_truth":"Maya Chen is a strong candidate: 3 years of experience at Fiverr and Wix, leads design system used by 80+ engineers, improved LCP by 40% for 4M+ MAU, WCAG 2.1 AA compliance across 20+ surfaces, WAS certified, built real-time collaborative editor, open-source contributor (ReactA11y Hooks, 300+ stars), BSc from Reichman (GPA 91/100), and available from July 2026.","expected_source":"docs","category":"complex","difficulty":"hard","expected_route":"broad"},
]
