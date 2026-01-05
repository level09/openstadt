# OpenStadt

Open Source Civic Data Platform for German Cities.

A configurable, multi-city civic data platform built with Flask + Vue 3 + Leaflet.

## Features

### Current (MVP)
- **Multi-city architecture** - One codebase, unlimited cities via YAML config
- **Interactive map** - Leaflet with marker clustering
- **Multi-layer POI system** - Toggle layers: Kindergartens, Playgrounds, Schools, Recycling
- **District filtering** - Filter POIs by city district
- **Search** - Full-text search across all POIs
- **Geolocation** - "Near me" feature
- **OSM integration** - Sync data from OpenStreetMap Overpass API
- **Data import** - CSV and GeoJSON importers (CLI)
- **REST API** - Public endpoints for cities, layers, POIs, search

### Planned
- Admin dashboard for data management
- More filter options (radius, attributes)
- District boundary overlays
- Scheduled data sync

## Quick Start

```bash
# Setup
./setup.sh

# Or manually:
uv sync
cp .env-sample .env
uv run flask create-db
uv run flask install

# Load sample city
uv run flask load-city config/cities/mannheim.yaml

# Sync data from OpenStreetMap
uv run flask sync-osm mannheim playgrounds
uv run flask sync-osm mannheim kitas
uv run flask sync-osm mannheim schools
uv run flask sync-osm mannheim recycling

# Run
uv run flask run
```

Visit http://localhost:5000/mannheim

## CLI Commands

```bash
uv run flask create-db                    # Create database tables
uv run flask install                      # Create admin user
uv run flask load-city <yaml>             # Load city from YAML config
uv run flask list-cities                  # List all cities
uv run flask sync-osm <city> <layer>      # Sync from OpenStreetMap
uv run flask import-csv <city> <layer> <file>  # Import CSV data
```

## API Endpoints

```
GET /api/v1/cities                        # List all cities
GET /api/v1/cities/{slug}                 # Get city with layers
GET /api/v1/cities/{slug}/pois            # Get POIs (filterable)
GET /api/v1/cities/{slug}/search?q=...    # Search POIs
```

## Adding a City

1. Copy `config/cities/_template.yaml` to `config/cities/<your-city>.yaml`
2. Configure city center, bounds, and layers
3. Load: `uv run flask load-city config/cities/<your-city>.yaml`
4. Sync data from OSM or import from CSV/GeoJSON

## Tech Stack

- **Backend**: Flask, SQLAlchemy 2.x, Flask-Security-Too
- **Frontend**: Vue 3, Vuetify 3, Leaflet.js
- **Database**: SQLite (dev) / PostgreSQL + PostGIS (prod)
- **Package Manager**: uv

## Project Structure

```
openstadt/
├── openstadt/
│   ├── api/          # Models and API routes
│   ├── public/       # Public map views
│   ├── portal/       # Dashboard views (WIP)
│   ├── user/         # User models and auth
│   ├── static/       # CSS, JS, images
│   └── templates/    # Jinja2 templates
├── config/
│   └── cities/       # City YAML configs
├── instance/         # SQLite database (gitignored)
└── pyproject.toml
```

## Sample Data (Mannheim)

After syncing from OSM:
- Kindergartens: ~243
- Playgrounds: ~703
- Schools: ~183
- Recycling containers: ~510

## License

MIT
