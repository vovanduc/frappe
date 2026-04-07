# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Frappe is a metadata-driven, full-stack low-code web framework in Python and JavaScript. It uses MariaDB/PostgreSQL on the server side with a tightly integrated client-side library. It powers ERPNext (700+ DocTypes). Version 17.x (develop branch).

Frappe is always run through the **Bench CLI** — never standalone. All `bench` commands require a site context.

## Common Commands

### Development
```bash
bench serve                              # Start dev server
bench build                              # Build JS/CSS assets
bench watch                              # Watch and rebuild on changes
bench --site [site] console              # Interactive Python console
bench --site [site] execute [method]     # Run a Python method
bench --site [site] migrate              # Run database migrations
bench --site [site] clear-cache          # Clear Redis cache
```

### Testing
```bash
bench --site [site] run-tests --app frappe                    # Full test suite
bench --site [site] run-tests --module frappe.tests.test_api  # Test a module
bench --site [site] run-tests --doctype "ToDo"                # Test a DocType
bench --site [site] run-tests --test test_method_name         # Single test
bench --site [site] run-tests --failfast                      # Stop on first failure
bench --site [site] run-parallel-tests --app frappe --total-builds 4 --build-number 1
bench --site [site] run-ui-tests --app frappe                 # Cypress UI tests
```

### Linting & Formatting
```bash
# Pre-commit handles everything — ruff (Python), prettier (JS/Vue/SCSS), eslint, commitlint
pre-commit run --all-files

# Individual tools
ruff check .                    # Python lint
ruff format .                   # Python format
npx prettier --write .          # JS/Vue format
npx eslint .                    # JS lint
```

**Python style:** line-length 110, tabs for indentation, target Python 3.14. Ruff config in `pyproject.toml`.

### Commit Convention
Conventional commits enforced by commitlint: `type(scope): subject`
Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `deprecate`

## Architecture

### Core Abstraction: DocType & Document

Everything in frappe revolves around **DocTypes** — metadata-defined models. Each DocType has:
- A JSON definition (`[app]/[module]/doctype/[name]/[name].json`) describing fields, permissions, naming rules
- A Python controller (`[name].py`) extending `frappe.model.document.Document` with lifecycle hooks
- Optional JS controller (`[name].js`) for client-side behavior

**Document lifecycle hooks** (in order): `before_insert` → `validate` → `before_save` → `on_update` → `after_insert` → `on_submit` → `on_cancel` → `on_trash`

### Request Flow
1. `frappe/app.py` — WSGI application (Werkzeug-based), sets up request context
2. `frappe/handler.py` — Dispatches API calls, RPC, file uploads
3. `frappe/auth.py` — Authentication (password, OAuth, LDAP, 2FA)
4. `frappe/sessions.py` — Redis-backed session management
5. `frappe/client.py` — REST API handler for `/api/resource/` CRUD

### The `frappe` Namespace
`frappe/__init__.py` is the god object — it exposes the entire framework API via thread-local state (`frappe.local`). Key globals:
- `frappe.db` — Database connection
- `frappe.session` — Current user session
- `frappe.conf` — Site configuration (from `site_config.json`)
- `frappe.cache` — Redis cache wrapper
- Common functions: `frappe.get_doc()`, `frappe.get_list()`, `frappe.call()`, `frappe.throw()`, `frappe.whitelist()`

### Database Layer
- `frappe/database/database.py` — Base database abstraction
- `frappe/database/mariadb/` — MariaDB backend
- `frappe/database/postgres/` — PostgreSQL backend
- ORM is document-based, not table-based. Use `frappe.get_doc()`, `frappe.get_list()`, `frappe.db.sql()`, or Query Builder (`frappe.qb`)

### Frontend (Desk UI)
- `frappe/public/js/frappe/` — Core desk JavaScript
- `frappe/public/js/frappe/form/` — Form views, controls, layout
- `frappe/public/js/frappe/list/` — List views
- `frappe/public/js/frappe/views/` — Reports, Kanban, Calendar, Dashboard
- `frappe/public/js/frappe/ui/` — Reusable UI components (dialogs, pages, widgets)
- Vue 3 components in `.vue` files, legacy code uses plain JS classes
- Build system: esbuild (`esbuild/` directory)

### Hooks System
`hooks.py` in each app declares integration points: scheduled jobs, doc events, overrides, website routes, permission queries, etc. The framework calls `frappe.get_hooks()` to discover and invoke them.

### Key Subsystems
- **Permissions**: `frappe/permissions.py` — RBAC with role, user, document-level, and sharing rules
- **Email**: `frappe/email/` — Send (queue-based) and receive (IMAP/POP3)
- **Background Jobs**: `frappe/utils/background_jobs.py` — RQ (Redis Queue) workers
- **Website**: `frappe/website/` — Public-facing pages with `frappe/website/router.py`
- **Printing/PDF**: `frappe/printing/` — Jinja-based print formats, PDF via Chromium or wkhtmltopdf
- **Workflow**: `frappe/workflow/` — State machine workflows on documents
- **Translations**: `frappe/translate.py` — i18n with `_()` function
