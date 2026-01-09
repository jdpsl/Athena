# Athena Project Template Roadmap

This document outlines the current state and future plans for Athena's project initialization templates.

## Status Overview

- ✅ **Implemented**: Fully working templates
- 🚧 **Listed but Not Implemented**: Declared in tool but template missing
- 📋 **Planned**: High-value templates to add
- 🔥 **Priority**: Should be implemented soon
- ⭐ **Community Request**: Based on common use cases

---

## Current Templates (2)

### ✅ python-web
**Status**: Fully Implemented
**Stack**: FastAPI + pytest + ruff + black + GitHub Actions
**Use Case**: REST APIs, web services, microservices
**Features**:
- Async/await support
- Automatic API documentation (Swagger/ReDoc)
- Environment-based configuration
- Comprehensive test setup
- CI/CD workflow

### ✅ node-web
**Status**: Fully Implemented
**Stack**: Express.js + TypeScript
**Use Case**: Node.js web servers, REST APIs
**Features**:
- TypeScript with strict mode
- Express middleware setup
- Environment configuration
- Basic routing structure

---

## Listed but Not Implemented (3)

These are declared in the InitializeProject tool but will fail if used. **Priority: Complete these first.**

### 🚧 🔥 python-cli
**Priority**: HIGH
**Stack**: Click/Typer + pytest + rich
**Use Case**: Command-line tools, scripts, utilities
**Should Include**:
- Argument parsing (Click or Typer)
- Rich console output (colors, tables, progress bars)
- Configuration file support (YAML/TOML)
- Man page generation
- Shell completion
- PyPI packaging setup
- Example subcommands
- Test fixtures for CLI testing

### 🚧 🔥 python-lib
**Priority**: HIGH
**Stack**: Poetry/setuptools + pytest + sphinx
**Use Case**: Python libraries/packages for PyPI
**Should Include**:
- Modern pyproject.toml setup
- Sphinx documentation
- ReadTheDocs configuration
- Version management (bumpversion)
- PyPI publishing workflow
- Example module with docstrings
- Test coverage reporting
- Type stubs (py.typed)

### 🚧 🔥 node-cli
**Priority**: HIGH
**Stack**: Commander.js + TypeScript + Jest
**Use Case**: Node.js command-line tools
**Should Include**:
- Commander.js for argument parsing
- Chalk for colored output
- Inquirer for interactive prompts
- Configuration file support
- NPM/Yarn publishing setup
- Example subcommands
- Unit tests with Jest

---

## High-Priority Templates (10)

### 📋 🔥 python-django
**Priority**: VERY HIGH (Django is extremely popular)
**Stack**: Django + PostgreSQL + Celery + Redis
**Use Case**: Full-stack web applications, admin panels
**Should Include**:
- Django project structure
- PostgreSQL database setup
- Celery for background tasks
- Redis for caching
- Django REST framework (optional)
- User authentication setup
- Admin customization
- Docker Compose setup
- Environment-based settings

### 📋 🔥 python-flask
**Priority**: HIGH (Lightweight alternative to Django)
**Stack**: Flask + SQLAlchemy + pytest
**Use Case**: Lightweight web apps, APIs
**Should Include**:
- Flask blueprints structure
- SQLAlchemy ORM setup
- Flask-Migrate for migrations
- JWT authentication (Flask-JWT-Extended)
- CORS configuration
- Environment configuration
- Swagger/OpenAPI docs

### 📋 🔥 ⭐ react-app
**Priority**: VERY HIGH (Most popular frontend framework)
**Stack**: React + TypeScript + Vite + Vitest
**Use Case**: Single-page applications, web UIs
**Should Include**:
- Vite for fast builds (not CRA)
- TypeScript with strict mode
- React Router for routing
- TanStack Query for data fetching
- Zustand or Jotai for state management
- Tailwind CSS (optional but common)
- ESLint + Prettier
- Vitest + React Testing Library
- GitHub Pages deployment workflow

### 📋 🔥 ⭐ nextjs-app
**Priority**: VERY HIGH (React + SSR)
**Stack**: Next.js 14+ (App Router) + TypeScript + Tailwind
**Use Case**: Full-stack React apps with SSR/SSG
**Should Include**:
- App Router (Next.js 14+)
- TypeScript configuration
- Tailwind CSS
- Server Components examples
- API routes
- Authentication setup (NextAuth.js)
- Database setup (Prisma)
- Vercel deployment configuration

### 📋 🔥 node-nestjs
**Priority**: HIGH (Enterprise Node.js)
**Stack**: NestJS + TypeScript + TypeORM + PostgreSQL
**Use Case**: Enterprise-grade Node.js backends
**Should Include**:
- NestJS modular architecture
- TypeORM with PostgreSQL
- JWT authentication
- Swagger API documentation
- Environment configuration
- Docker setup
- E2E testing with Supertest
- Microservices examples

### 📋 🔥 python-data-science
**Priority**: HIGH (ML/AI is huge)
**Stack**: Jupyter + pandas + scikit-learn + matplotlib
**Use Case**: Data analysis, ML experiments
**Should Include**:
- Jupyter notebook setup
- Virtual environment (poetry or conda)
- Data directory structure
- Example notebooks
- Requirements for pandas, numpy, scikit-learn
- Visualization libraries (matplotlib, seaborn, plotly)
- .gitignore for data files
- DVC for data versioning

### 📋 ⭐ vue-app
**Priority**: MEDIUM-HIGH (Popular frontend alternative)
**Stack**: Vue 3 + TypeScript + Vite + Pinia
**Use Case**: Vue.js single-page applications
**Should Include**:
- Vue 3 with Composition API
- TypeScript
- Vite for builds
- Vue Router
- Pinia for state management
- Vitest + Vue Test Utils
- Tailwind CSS option

### 📋 ⭐ python-fastapi-fullstack
**Priority**: MEDIUM-HIGH (Complete solution)
**Stack**: FastAPI + PostgreSQL + Alembic + React + Docker
**Use Case**: Full-stack applications with separate frontend/backend
**Should Include**:
- FastAPI backend
- PostgreSQL with Alembic migrations
- React frontend (in separate directory)
- Docker Compose for local development
- JWT authentication
- User management system
- Admin panel
- Nginx reverse proxy
- Production-ready structure

### 📋 rust-cli
**Priority**: MEDIUM (Growing popularity)
**Stack**: Clap + Tokio + serde
**Use Case**: High-performance CLI tools
**Should Include**:
- Clap for argument parsing
- Tokio for async runtime
- Serde for serialization
- Error handling (anyhow/thiserror)
- Cargo.toml with metadata
- Cross-compilation setup
- GitHub release workflow

### 📋 go-web
**Priority**: MEDIUM (Popular for microservices)
**Stack**: Gin/Echo + GORM + PostgreSQL
**Use Case**: Go web services and APIs
**Should Include**:
- Gin or Echo framework
- GORM for database
- Environment configuration (viper)
- Structured logging (zap)
- Graceful shutdown
- Docker multi-stage build
- Kubernetes manifests

---

## Nice-to-Have Templates (15)

### Frontend Frameworks
- 📋 **svelte-app**: Svelte + SvelteKit + TypeScript
- 📋 **solid-app**: SolidJS + Solid Start (emerging, very fast)
- 📋 **angular-app**: Angular + TypeScript (enterprise)
- 📋 **astro-site**: Astro for content sites (blogs, docs)

### Mobile Development
- 📋 **react-native-app**: React Native + Expo + TypeScript
- 📋 **flutter-app**: Flutter + Dart for cross-platform mobile

### Full-Stack Meta-Frameworks
- 📋 **remix-app**: Remix (React full-stack framework)
- 📋 **nuxt-app**: Nuxt.js (Vue full-stack framework)
- 📋 **sveltekit-app**: SvelteKit (Svelte full-stack framework)

### Backend Alternatives
- 📋 **rust-web**: Actix-web or Axum
- 📋 **go-chi**: Chi router (lightweight Go web)
- 📋 **elixir-phoenix**: Phoenix framework (Elixir)

### Specialized
- 📋 **chrome-extension**: Chrome extension with manifest v3
- 📋 **vscode-extension**: VS Code extension with TypeScript
- 📋 **electron-app**: Electron desktop app

---

## Template Creation Guidelines

When creating new templates, ensure they include:

### Must-Haves
- ✅ Professional README.md with all sections
- ✅ Appropriate .gitignore
- ✅ LICENSE file
- ✅ Configuration files (language-specific)
- ✅ Test setup and example tests
- ✅ Linting and formatting configuration
- ✅ CI/CD workflow (GitHub Actions)
- ✅ Environment variables example (.env.example)

### Should-Haves
- ✅ Docker/Docker Compose setup
- ✅ Pre-commit hooks configuration
- ✅ Code quality badges in README
- ✅ Contributing guidelines
- ✅ Security best practices
- ✅ Error handling examples
- ✅ Logging setup

### Nice-to-Haves
- ✅ Documentation site setup (Sphinx, Docusaurus, etc.)
- ✅ Deployment guides (Vercel, Heroku, AWS, etc.)
- ✅ Performance monitoring setup
- ✅ Database migration examples
- ✅ API documentation generation
- ✅ Internationalization (i18n) setup

---

## Implementation Priority Order

### Phase 1: Complete Declared Templates (URGENT)
1. 🔥 python-cli
2. 🔥 python-lib
3. 🔥 node-cli

**Why**: These are already listed in the tool but don't work. This is a bug that needs fixing.

### Phase 2: Critical Frontend (HIGH PRIORITY)
4. 🔥 react-app
5. 🔥 nextjs-app

**Why**: Frontend development is extremely common, React dominates market share.

### Phase 3: Popular Backend Alternatives (HIGH PRIORITY)
6. 🔥 python-django
7. 🔥 python-flask
8. 🔥 node-nestjs

**Why**: These are the most requested backend frameworks after FastAPI/Express.

### Phase 4: Specialized but Valuable (MEDIUM PRIORITY)
9. python-data-science
10. python-fastapi-fullstack
11. vue-app
12. rust-cli
13. go-web

**Why**: Covers important use cases and languages.

### Phase 5: Extended Ecosystem (LOWER PRIORITY)
14-29. All "Nice-to-Have" templates

**Why**: These serve specific niches but still add value.

---

## Competitive Analysis

### vs Claude Code
Claude Code has hidden templates. We can't see exactly what they support, but based on user reports:
- ✅ Python projects (probably FastAPI, Flask, Django)
- ✅ Node.js projects (probably Express, Next.js)
- ✅ React projects
- ❓ Unknown others

**Athena's Advantage**:
- Visible templates (users can see and modify)
- Custom templates (~/.athena/templates/)
- Community can contribute
- Works with weaker models (templates do the heavy lifting)

### vs create-react-app, create-next-app, etc.
These are single-purpose tools.

**Athena's Advantage**:
- One tool for ALL project types
- Consistent structure across languages
- AI-powered customization during creation
- Integrated with full AI assistant

### vs Yeoman, Cookiecutter
These require pre-made templates and manual selection.

**Athena's Advantage**:
- Natural language ("create a FastAPI project for user management")
- AI understands intent and customizes on the fly
- No need to browse/search templates
- Can research latest best practices during creation

---

## Community Contributions

To make Athena's template system thrive, we should:

1. **Template Gallery**: Web page showing all available templates
2. **Template CLI**: `athena templates list`, `athena templates info python-web`
3. **Template Validation**: Tool to validate custom templates before use
4. **Template Sharing**: NPM-style registry for community templates
5. **Template Generator**: Tool to create new templates from existing projects

---

## Metrics to Track

Once templates are in use, track:
- **Most popular templates** (usage count)
- **Template success rate** (projects created vs errors)
- **User customization patterns** (which variables are commonly changed)
- **Community template adoption** (custom templates in ~/.athena/templates/)

---

## Next Steps

1. ✅ **Complete Phase 1** (python-cli, python-lib, node-cli)
2. Create template contribution guide
3. Build template validation tool
4. Add `athena templates list` command
5. Create template gallery website
6. Launch Phase 2 (React + Next.js templates)

---

**Last Updated**: 2026-01-08
**Total Templates**: 2 implemented, 3 listed, 24 planned = **29 total envisioned**
