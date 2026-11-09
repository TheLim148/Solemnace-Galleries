# Solemnace Galleries

Solemnace Galleries is a Django web application for cataloguing and managing digital galleries, locations and exhibits.

The project is inspired by the concept of Solemnace and Trazyn the Infinite's collection from Warhammer 40,000, but the application architecture itself is generic: it can be used to organise exhibits into hierarchical locations and thematic galleries, attach media and sources, and publish content after moderation.

## Current status

The project is under active development as a college coursework project.

The current MVP already supports the main cataloguing workflow: authentication, content ownership, exhibit moderation, gallery and location management, media uploads, favorites, search and filtering.

The next development stage is interface styling and final project polishing.

## Features

- User registration, login and logout.
- User and administrator roles.
- Hierarchical locations with a protected system root.
- User-created galleries assigned to locations.
- Exhibits with categories, tags, sources and media.
- Many-to-many relation between galleries and exhibits.
- Related exhibits.
- Exhibit lifecycle: draft, pending review, published and rejected.
- Owner and administrator access control.
- Favorites for authenticated users.
- Public exhibit search by text, category and tag.
- Django Admin for technical administration and moderation.

## Technology stack

- Python 3.12
- Django 6.1
- PostgreSQL
- psycopg 3
- python-dotenv
- uv
- Django Templates / HTML

CSS and small client-side JavaScript are planned for the interface layer.

## Project structure

```text
.
├── accounts/                 # Authentication and custom User model
├── archive/                  # Main catalog domain
│   ├── migrations/
│   ├── templates/archive/
│   ├── views/
│   │   ├── exhibits.py       # Exhibit CRUD, moderation and media
│   │   ├── favorites.py      # Favorites
│   │   ├── galleries.py      # Gallery pages and CRUD
│   │   ├── locations.py      # Location pages and CRUD
│   │   └── pages.py          # General pages
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── permissions.py        # Shared access-control rules
│   ├── services.py           # Reusable domain operations
│   └── urls.py
├── config/                   # Django project configuration
├── docs/                     # Project notes and documentation
├── src/solemnace_galleries/  # Python package used by the uv build backend
├── manage.py
├── pyproject.toml
└── uv.lock
```

The `src/solemnace_galleries` package should not be removed: the project uses the `uv_build` build backend and keeps the package as part of the uv project layout.

## Data model overview

The central entities are:

```text
Location 1 ─── N Gallery
Gallery  M ─── N Exhibit
User     1 ─── N Exhibit
User     1 ─── N Gallery
User     1 ─── N Location
Category 1 ─── N Exhibit
Exhibit  M ─── N Tag
Exhibit  M ─── N Source
User     M ─── N Exhibit   (Favorite)
Exhibit  M ─── N Exhibit   (related exhibits)
```

Locations form a hierarchy through a self-reference. The root `Solemnace` location is a system location and is protected from ordinary user-interface editing and deletion.

## Local setup

### 1. Requirements

Install:

- Python 3.12
- PostgreSQL
- uv

### 2. Install Python dependencies

From the project root:

```bash
uv sync
```

### 3. Configure PostgreSQL

Create a PostgreSQL database and a user for the application. The default development names used by the project are:

```text
Database: solemnace
User: solemnace_app
```

Copy the environment template:

```bash
cp .env.example .env
```

Then fill in the real database password in `.env`:

```dotenv
DB_NAME=solemnace
DB_USER=solemnace_app
DB_PASSWORD=your-password
DB_HOST=127.0.0.1
DB_PORT=5432
```

`.env` is ignored by Git and must not be committed.

### 4. Apply migrations

```bash
uv run python manage.py migrate
```

### 5. Create an administrator

```bash
uv run python manage.py createsuperuser
```

### 6. Create the root location

Until the root location is created automatically by a data migration, create it once through Django Admin:

```text
Name: Solemnace
System location: yes
Owner: empty
Parent: empty
```

### 7. Run the development server

```bash
uv run python manage.py runserver
```

Open the local Django address printed in the terminal. Django Admin is available at `/admin/`.

## Useful development commands

Check Django configuration:

```bash
uv run python manage.py check
```

Create migrations after model changes:

```bash
uv run python manage.py makemigrations
```

Apply migrations:

```bash
uv run python manage.py migrate
```

Run tests:

```bash
uv run python manage.py test
```

## Content and access rules

An ordinary user can create and manage their own exhibits, galleries and locations. Administrators can manage user content as well.

An exhibit can belong to multiple galleries. Deleting a gallery removes its membership links but does not delete the exhibits themselves.

A normal location must have a parent. A location cannot be moved inside itself or one of its descendants. A location containing child locations or galleries cannot be deleted through the application.

Unpublished exhibits are visible only to their owner and administrators. Public catalog pages contain only published exhibits.

When creating or editing an exhibit, an ordinary user can attach it only to galleries they own. Administrators can select any gallery.

## Moderation workflow

```text
Draft
  ↓
Pending review
  ↓
Published
```

A rejected exhibit can be edited and submitted for review again.

At the current MVP stage, the final moderation decision is performed through Django Admin.

## Disclaimer

Solemnace Galleries is a non-commercial fan-inspired educational project and is not affiliated with Games Workshop.

Warhammer 40,000 and related names, characters and materials belong to their respective rights holders.
