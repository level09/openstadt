# OpenStadt

**Open-source infrastructure equity platform for German cities — map, analyze, and compare public facilities across neighborhoods**

## What is OpenStadt?

OpenStadt helps cities answer a simple but important question: **"Are public facilities distributed fairly across all neighborhoods?"**

Every city has public infrastructure - playgrounds, schools, kindergartens, recycling containers, and more. But this infrastructure isn't always distributed evenly. Some neighborhoods might have 20 playgrounds while others have none. OpenStadt makes these inequalities visible so city planners, journalists, and citizens can identify underserved areas and advocate for better resource allocation.

### The Problem

- Cities don't always know where their infrastructure gaps are
- Data is scattered across different departments and formats
- There's no easy way to compare neighborhoods
- Citizens can't see if their area is underserved

### The Solution

OpenStadt pulls real data from OpenStreetMap, assigns each facility to its neighborhood, and calculates an **Equity Score** for every district. Districts scoring below 50% are flagged as "underserved" - they have less than half the city average of public facilities.

## Features

### Interactive Map (`/city-name`)
- View all public facilities on a map with colored markers by category
- Filter by facility type (playgrounds, schools, etc.)
- Filter by neighborhood/district
- Search for specific places
- Click any marker to see details (address, district, accessibility info)
- City switcher to navigate between cities
- "Near me" geolocation
- Share POI links for specific locations

### Analytics Dashboard (`/city-name/analytics`)
- **Summary cards**: Total facilities, districts, city average, underserved count
- **District comparison table**: Every neighborhood ranked by equity score
- **Layer comparison**: Statistics per facility type (min, max, average, spread)
- **Coverage analysis**: Which areas have gaps in specific infrastructure types
- **Sorting**: View by equity score (worst first) or by total count

### Data Management
- Sync data directly from OpenStreetMap
- Import from CSV or GeoJSON
- Multi-city support from a single codebase
- Configurable layers per city via YAML

## How Equity Score Works

```
Equity Score = (District's Facilities / City Average) × 100

Example:
- City has 1000 facilities across 50 districts
- City average = 20 facilities per district
- District A has 10 facilities → Equity Score = 50% (underserved)
- District B has 30 facilities → Equity Score = 150% (well-served)
```

Districts below 50% are highlighted in red as "severely underserved."

## Quick Start

```bash
# Setup
./setup.sh

# Or manually:
uv sync
cp .env-sample .env
uv run flask create-db
uv run flask install

# Load a city
uv run flask load-city config/cities/mannheim.yaml

# Sync district boundaries from OpenStreetMap
uv run flask sync-districts mannheim

# Sync facilities from OpenStreetMap
uv run flask sync-osm mannheim playgrounds
uv run flask sync-osm mannheim kitas
uv run flask sync-osm mannheim schools
uv run flask sync-osm mannheim recycling

# Run the app
uv run flask run
```

Visit:
- Map: http://localhost:5000/mannheim
- Analytics: http://localhost:5000/mannheim/analytics

## CLI Commands

```bash
uv run flask create-db                         # Create database tables
uv run flask install                           # Create admin user
uv run flask load-city <yaml>                  # Load city from YAML config
uv run flask list-cities                       # List all cities
uv run flask sync-districts <city>             # Sync district boundaries from OSM
uv run flask sync-osm <city> <layer>           # Sync facilities from OSM
uv run flask sync-all                          # Load all city configs and sync all OSM data
uv run flask sync-all -c <city>                # Sync all layers for a specific city
uv run flask import-csv <city> <layer> <file>  # Import CSV data
```

## API Endpoints

```
GET /api/v1/cities                             # List all cities
GET /api/v1/cities/{slug}                      # Get city with layers
GET /api/v1/cities/{slug}/pois                 # Get POIs (filterable)
GET /api/v1/cities/{slug}/search?q=...         # Search POIs

# Analytics endpoints
GET /api/v1/cities/{slug}/analytics/districts  # District statistics with equity scores
GET /api/v1/cities/{slug}/analytics/comparison # Layer-by-layer comparison
GET /api/v1/cities/{slug}/analytics/coverage   # Coverage analysis per layer
```

## Adding a City

1. Copy `config/cities/_template.yaml` to `config/cities/<your-city>.yaml`
2. Configure city center, bounds, and layers
3. Load: `uv run flask load-city config/cities/<your-city>.yaml`
4. Sync districts: `uv run flask sync-districts <your-city>`
5. Sync data from OSM or import from CSV/GeoJSON

## Tech Stack

- **Backend**: Flask, SQLAlchemy 2.x, Flask-Security-Too
- **Frontend**: Vue 3, Vuetify 3, Leaflet.js
- **Database**: SQLite (dev) / PostgreSQL + PostGIS (prod)
- **Package Manager**: uv
- **Data Source**: OpenStreetMap via Overpass API

## Project Structure

```
openstadt/
├── openstadt/
│   ├── api/          # Models, API routes, analytics
│   ├── public/       # Public map and analytics views
│   ├── portal/       # Admin dashboard (WIP)
│   ├── user/         # User models and auth
│   ├── static/       # CSS, JS, images
│   └── templates/    # Jinja2 + Vue templates
├── config/
│   └── cities/       # City YAML configs
├── instance/         # SQLite database (gitignored)
└── pyproject.toml
```

## Included Cities

Pre-configured city configs are available in `config/cities/`:

| City | Config File |
|------|-------------|
| Berlin | `berlin.yaml` |
| Darmstadt | `darmstadt.yaml` |
| Frankfurt am Main | `frankfurt.yaml` |
| Hamburg | `hamburg.yaml` |
| Köln | `koeln.yaml` |
| Mannheim | `mannheim.yaml` |
| München | `muenchen.yaml` |

Load all cities at once:
```bash
uv run flask sync-all
```

## Sample Data (Mannheim)

After syncing from OSM:
- **55 districts** with boundaries
- **1,639 facilities** total:
  - 703 Spielplätze (playgrounds)
  - 510 Wertstoffcontainer (recycling)
  - 243 Kindergärten
  - 183 Schulen (schools)
- **20 underserved districts** (equity score < 50%)

## Use Cases

- **City planners**: Identify where to build new facilities
- **Journalists**: Data-driven stories about urban inequality
- **Citizens**: Check if your neighborhood is underserved
- **Researchers**: Analyze infrastructure distribution patterns
- **NGOs**: Advocate for equitable resource allocation

## License

MIT
