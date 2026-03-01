# Strategy Hub

Strategy Hub is a Django application for managing strategies, their hierarchy, and the controlling process around measures.

The current implementation focuses on:

- strategy master data
- hierarchical planning objects: `Handlungsfeld -> Ziel -> Massnahme`
- responsibilities for measures
- controlling periods and controlling records
- a dashboard with basic operational visibility

The UI is built with [iommi](https://github.com/iommirocks/iommi), so most list, detail, and CRUD screens are generated from Python configuration instead of hand-written templates.

## Tech Stack

- Python 3.12
- Django 5.2
- iommi 7
- SQLite by default for local development
- `uv` for dependency and environment management

## Project Structure

- `config/`: Django settings, URL routing, main menu
- `core/`: shared helpers, strategy context, management commands
- `strategies/`: strategies, hierarchy levels, measure types, responsibilities
- `controlling/`: controlling periods, records, services
- `people/`: person profiles linked to Django users
- `dashboard/`: landing page and summary views
- `fake_data/`: deterministic CSV-based demo dataset

## What Is Implemented

The application currently includes:

- strategy selection via an active strategy context
- list and detail views for strategies
- dedicated list pages for handlungsfelder, ziele, and massnahmen
- filtered creation flows for ziele and massnahmen
- CRUD flows for measure types and measure responsibilities
- controlling periods and controlling records
- deterministic demo-data import from CSV files

The application language and labels are currently German (`de-ch`), while the codebase and tooling are standard Django/Python.

## Local Setup

Install dependencies and create the local database:

```bash
uv sync
uv run python manage.py migrate
```

Create an admin user:

```bash
uv run python manage.py createsuperuser
```

Start the development server:

```bash
uv run python manage.py runserver
```

The app will then be available at `http://localhost:8000/`.

## Demo Data

The repository includes a deterministic demo dataset under [fake_data/](/home/lcalm/Work/Dev/strategyhub/fake_data).

Load or reload the dataset:

```bash
uv run python manage.py load_fake_data --replace
```

Bootstrap a local instance with migrations plus demo data:

```bash
uv run python manage.py create_demo_data --migrate
```

The demo import creates:

- Django users from `fake_data/users.csv`
- person profiles
- strategies
- hierarchy levels
- measure responsibilities
- controlling periods
- controlling records
- controlling record responsibilities

`load_fake_data --replace` deletes previously imported domain data before recreating it from the CSV files.

## Authentication

- Login uses Django's built-in authentication.
- Demo users are loaded from `fake_data/users.csv`.
- Login currently uses `username`, not email.

## Development Notes

The default local database is SQLite and lives in `db.sqlite3`. Static files are served from `static/`, uploaded media from `media/`.

Useful checks:

```bash
uv run python manage.py check
uv run pytest
```

Linting:

```bash
uv run ruff check .
```

## Heroku Deployment

The repository now includes a basic Heroku deployment setup:

- [Procfile](/home/lcalm/Work/Dev/strategyhub/Procfile)
- [uv.lock](/home/lcalm/Work/Dev/strategyhub/uv.lock)
- [runtime.txt](/home/lcalm/Work/Dev/strategyhub/runtime.txt)
- environment-based production settings in [config/settings.py](/home/lcalm/Work/Dev/strategyhub/config/settings.py)

Required config vars:

- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY=<strong-random-secret>`
- `DJANGO_ALLOWED_HOSTS=<your-app>.herokuapp.com`
- `DATABASE_URL=<Heroku Postgres URL>`

Optional config vars:

- `DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-app>.herokuapp.com`
- `DJANGO_SECURE_SSL_REDIRECT=true`

Typical first deployment flow:

```bash
heroku create
heroku addons:create heroku-postgresql:essential-0
heroku config:set DJANGO_DEBUG=false
heroku config:set DJANGO_SECRET_KEY=<strong-random-secret>
heroku config:set DJANGO_ALLOWED_HOSTS=<your-app>.herokuapp.com
heroku config:set DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-app>.herokuapp.com
git push heroku main
```

The `release` process in [Procfile](/home/lcalm/Work/Dev/strategyhub/Procfile) runs `python manage.py migrate` automatically on deploy.

Current limitation:

- uploaded media is still stored on the local filesystem. That is not durable on Heroku. For real user uploads, move media storage to S3-compatible object storage before relying on it.

## Key Files

- [pyproject.toml](/home/lcalm/Work/Dev/strategyhub/pyproject.toml): project metadata and tool configuration
- [config/settings.py](/home/lcalm/Work/Dev/strategyhub/config/settings.py): Django settings
- [project-description-md](/home/lcalm/Work/Dev/strategyhub/project-description-md): business context
- [technical-design.md](/home/lcalm/Work/Dev/strategyhub/technical-design.md): technical design notes

## Current Status

This repository is an actively evolving application rather than a polished product package. The README documents the current developer workflow and implemented feature set, not a finished release scope.
