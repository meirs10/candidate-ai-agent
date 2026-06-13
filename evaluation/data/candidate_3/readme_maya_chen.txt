Fiverr Design System

A comprehensive, accessible component library powering Fiverr's marketplace UI.

#Overview

The Fiverr Design System is a shared component library used by 80+ frontend engineers across 20+ product surfaces. Built with React, TypeScript, and Storybook, it provides 60+ accessible components with automated visual regression testing and comprehensive documentation.

#Architecture

The system uses a monorepo architecture with Turborepo, organizing components into three tiers: Primitives (atoms like Button, Input, Typography), Composites (molecules like SearchBar, Card, Modal), and Patterns (organisms like Navigation, DataTable, FormWizard). Each component follows the Compound Component pattern for maximum flexibility.

#Tech Stack

- Framework: React 18 with TypeScript
- Styling: CSS Modules + design tokens
- Documentation: Storybook 7
- Testing: Jest, React Testing Library, Chromatic
- Build: Turborepo, Rollup, esbuild
- CI/CD: GitHub Actions, npm registry
- Accessibility: axe-core, WCAG 2.1 AA

#Installation

```bash
npm install @fiverr/design-system
```

#Usage

Import components and use with TypeScript type safety. All components support theme customization via CSS custom properties and design tokens. Storybook provides interactive documentation and playground.

#Key Features

- 60+ fully accessible React components
- Automated visual regression testing with Chromatic
- Design token system with light and dark themes
- Compound component patterns for composability
- Full WCAG 2.1 AA compliance
- 40% reduction in UI development time

#Performance

All components are tree-shakeable with individual exports. Average component bundle size under 5KB gzipped. Storybook loads in under 3 seconds with lazy story loading.

#Contributing

Follow the contribution guide in CONTRIBUTING.md. All components must include accessibility tests, Storybook stories, and TypeScript types.

#License

MIT License
