---
name: react-vite-production-setup
description: A comprehensive workflow for initializing and configuring a production-ready
  React SPA using Vite, TypeScript, Tailwind CSS, and TanStack Query with a feature-based
  architecture.
metadata:
  skill_id: technical_skills/web_development/frontend/react/react-vite-production-setup
  version: 1.0.0
  type: technical
  weight: medium
---

# React Vite Production Setup

## Overview

A "production-ready" setup bridges the gap between a simple prototype and a maintainable application. This skill covers the configuration of a high-performance React Single Page Application (SPA) using Vite, TypeScript, Tailwind CSS, and TanStack Query. 

Unlike default boilerplates, this workflow enforces a **feature-based architecture**, optimizes **vendor chunking** for better caching, and establishes a robust **data-fetching layer** with sensible production defaults.

**Core principle:** Architecture should prevent technical debt by enforcing clear boundaries and optimized build outputs from day one.

## Capabilities

- **Scaffold Production Environments:** Initialize Vite projects with clean TypeScript templates and optimized package lockfiles.
- **Configure Path Aliases:** Map internal paths (e.g., `@/components`) to avoid brittle relative imports (`../../../../components`).
- **Optimize Build Outputs:** Implement manual chunking to separate large libraries (React, TanStack) from application code.
- **Setup Type-Safe Styling:** Integrate Tailwind CSS via PostCSS with full TypeScript support for configuration files.
- **Orchestrate Data Layers:** Configure TanStack Query with production-safe retry logic and stale-time defaults.
- **Implement Feature-Based Directory Structure:** Organize code into self-contained "features" to improve scalability and team isolation.

## Dependencies

- **TypeScript** — Provides the static analysis required for enterprise-scale refactoring and documentation.
- **React Core** — The underlying UI library; understanding hooks and components is essential for the provider-based setup.
- **Node Package Managers (npm/pnpm)** — Necessary for managing the dependency graph and executing Vite build scripts.

## When to Use

**Use when:**
- Starting a new React SPA intended for long-term maintenance.
- Building an application with complex data requirements (caching, synchronization).
- Working in a team where clear architectural boundaries (Features) are needed to prevent merge conflicts.
- Performance (Lighthouse scores, bundle size) is a critical requirement.

**When NOT to use:**
- Building a static site without complex interactivity (use Astro or Next.js SSG instead).
- Creating a single-purpose landing page where TanStack Query and complex architecture would be overkill.
- Learning React basics for the first time; start with a simpler setup to avoid configuration fatigue.

## Quick Reference

| Problem | Solution | Keywords |
| ------- | -------- | -------- |
| Brittle relative imports | Setup `@/*` path aliases in Vite/TS | `resolve.alias`, `paths` |
| Large bundle sizes | Manual vendor chunking | `build.rollupOptions` |
| Prop drilling data | TanStack Query Provider | `QueryClient`, `staleTime` |
| Folder spaghetti | Feature-based directory pattern | `src/features`, `index.ts` |
| Global style pollution | Tailwind CSS + PostCSS | `tailwind.config.js` |

## Core Patterns

### Path Alias Configuration

**The problem:** Importing components from deeply nested directories leads to `import { Button } from "../../../components/ui/Button"` which breaks easily during refactoring.

**❌ Common mistake (Relative paths):**
```typescript
// src/features/auth/components/LoginForm.tsx
import { Button } from "../../../components/ui/Button"; 
import { useAuth } from "../../../hooks/useAuth";
```

**✅ Production pattern (Path aliases):**
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});

// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Key insight:** Path aliases make code portable. You can move a file to a different folder level without updating dozens of import statements.

### Feature-Based Architecture

**The problem:** Large apps often have folders like `/components` or `/hooks` containing hundreds of unrelated files, making it hard to find code related to a specific business domain.

**✅ Production pattern:**
Organize by business domain inside `src/features/`. Each feature is self-contained.

```text
src/
  features/
    auth/
      api/         # API calls (TanStack Query hooks)
      components/  # Feature-specific components
      types/       # TS interfaces for auth
      index.ts     # The "Barrel Export"
    products/
      ...
  components/      # Truly global/shared components (UI kit)
```

**Key insight:** The `index.ts` in each feature acts as a public API. Only export what other parts of the app need. This prevents "leaky abstractions."

---

## Configuration Deep Dives

### 1. Vite Manual Chunking
To prevent one large `index.js` file, we split vendors into their own chunks. This allows browsers to cache libraries like React even when your app code changes.

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-utils': ['tanstack/react-query', 'axios'],
        },
      },
    },
  },
});
```

### 2. TanStack Query Production Defaults
By default, React Query fetches aggressively. For production, we define safer defaults.

```typescript
// src/lib/react-query.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

## Common Mistakes

| Mistake | Why It's Wrong | Fix |
| ------- | -------------- | --- |
| Importing from `src/features/feature-a/components/...` | Violates the barrel export pattern; creates tight coupling. | Only import from the feature's `index.ts`. |
| Putting all types in a global `types.ts` | Hard to manage and leads to name collisions. | Keep types inside the feature folder they belong to. |
| Forgetting `tsc` in build script | Vite uses esbuild which strips types but doesn't check them. | Add `tsc --noEmit` to your `build` script in `package.json`. |
| Default exports for components | Harder to track via "Find Usages" and auto-imports. | Use named exports exclusively. |

## Red Flags

- Your `vite.config.ts` has no `resolve.alias` configuration.
- Your `src/components` folder has more than 20 files that aren't generic UI elements.
- You see `../../../../` in more than 10% of your import statements.
- You are not using a `QueryClientProvider` at the root of your application.

**All of these mean: Revisit your approach before proceeding.**

---

## Validation

```bash
# 1. Type Check the whole project
npm run type-check # usually maps to 'tsc --noEmit'

# 2. Build and Analyze Chunks
npm run build

# 3. Verify path aliases work by running a dev server
npm run dev
```