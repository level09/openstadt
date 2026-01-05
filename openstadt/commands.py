"""Flask CLI commands for OpenStadt."""

import secrets
import string
from pathlib import Path

import click
from flask import current_app
from flask.cli import with_appcontext
from flask_security.utils import hash_password
from rich.console import Console

from openstadt.extensions import db

console = Console()


@click.command("create-db")
@with_appcontext
def create_db():
    """Create all database tables."""
    db.create_all()
    console.print("[green]Database tables created successfully.[/green]")


@click.command("install")
@with_appcontext
def install():
    """Initial setup: create database and admin user."""
    from openstadt.user.models import Role, User

    db.create_all()
    console.print("[green]Database tables created.[/green]")

    # Create admin role if not exists
    admin_role = db.session.scalars(
        db.select(Role).where(Role.name == "admin")
    ).first()
    if not admin_role:
        admin_role = Role(name="admin", description="Administrator")
        db.session.add(admin_role)
        console.print("[green]Admin role created.[/green]")

    # Check for existing admin
    admin = db.session.scalars(
        db.select(User).where(User.email == "admin@openstadt.de")
    ).first()
    if admin:
        console.print("[yellow]Admin user already exists.[/yellow]")
        return

    # Generate secure password
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    password = "".join(secrets.choice(alphabet) for _ in range(16))

    admin = User(
        email="admin@openstadt.de",
        name="Administrator",
        password=hash_password(password),
        active=True,
    )
    admin.roles.append(admin_role)
    db.session.add(admin)
    db.session.commit()

    console.print("\n[bold green]Admin user created:[/bold green]")
    console.print(f"  Email: [cyan]admin@openstadt.de[/cyan]")
    console.print(f"  Password: [cyan]{password}[/cyan]")
    console.print("\n[yellow]Please save this password - it won't be shown again.[/yellow]")


@click.command("create")
@click.option("-e", "--email", required=True, help="User email")
@click.option("-p", "--password", required=True, help="User password")
@click.option("-n", "--name", default=None, help="User name")
@with_appcontext
def create_user(email, password, name):
    """Create a new user."""
    from openstadt.user.models import User

    existing = db.session.scalars(db.select(User).where(User.email == email)).first()
    if existing:
        console.print(f"[red]User {email} already exists.[/red]")
        return

    user = User(
        email=email,
        name=name,
        password=hash_password(password),
        active=True,
    )
    db.session.add(user)
    db.session.commit()
    console.print(f"[green]User {email} created successfully.[/green]")


@click.command("add-role")
@click.option("-e", "--email", required=True, help="User email")
@click.option("-r", "--role", required=True, help="Role name")
@with_appcontext
def add_role(email, role):
    """Add a role to a user."""
    from openstadt.user.models import Role, User

    user = db.session.scalars(db.select(User).where(User.email == email)).first()
    if not user:
        console.print(f"[red]User {email} not found.[/red]")
        return

    role_obj = db.session.scalars(db.select(Role).where(Role.name == role)).first()
    if not role_obj:
        role_obj = Role(name=role)
        db.session.add(role_obj)

    if role_obj not in user.roles:
        user.roles.append(role_obj)
        db.session.commit()
        console.print(f"[green]Role '{role}' added to {email}.[/green]")
    else:
        console.print(f"[yellow]User {email} already has role '{role}'.[/yellow]")


@click.command("load-city")
@click.argument("config_file", type=click.Path(exists=True))
@with_appcontext
def load_city(config_file):
    """Load a city from a YAML config file."""
    import yaml

    from openstadt.api.models import City, Layer

    with open(config_file) as f:
        config = yaml.safe_load(f)

    city_data = config.get("city", {})
    slug = city_data.get("slug")

    if not slug:
        console.print("[red]Config must include city.slug[/red]")
        return

    # Create or update city
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        city = City(slug=slug)

    city.name = city_data.get("name", slug.title())
    city.state = city_data.get("state")
    center = city_data.get("center", [49.4875, 8.4660])
    city.center_lat = center[0]
    city.center_lng = center[1]
    city.default_zoom = city_data.get("zoom", 12)
    city.bounds = city_data.get("bounds")

    # Theme
    theme = config.get("theme", {})
    city.primary_color = theme.get("primary_color", "#0066CC")
    city.logo_url = theme.get("logo")

    city.config = config

    db.session.add(city)
    db.session.flush()  # Get city.id

    # Create layers
    for layer_data in config.get("layers", []):
        layer_slug = layer_data.get("slug")
        if not layer_slug:
            continue

        layer = db.session.scalars(
            db.select(Layer).where(Layer.city_id == city.id, Layer.slug == layer_slug)
        ).first()
        if not layer:
            layer = Layer(city_id=city.id, slug=layer_slug)

        layer.name = layer_data.get("name", layer_slug.title())
        layer.name_de = layer_data.get("name_de")
        layer.icon = layer_data.get("icon", "map-marker")
        layer.color = layer_data.get("color", "#3388ff")
        layer.visible_by_default = layer_data.get("visible", True)

        source = layer_data.get("source", {})
        layer.source_type = source.get("type")
        layer.source_url = source.get("url")
        layer.source_config = source.get("mapping") or source.get("query")

        layer.schema = layer_data.get("attributes")

        db.session.add(layer)

    db.session.commit()
    console.print(f"[green]City '{city.name}' loaded with {len(config.get('layers', []))} layers.[/green]")


@click.command("list-cities")
@with_appcontext
def list_cities():
    """List all cities."""
    from openstadt.api.models import City

    cities = db.session.scalars(db.select(City).order_by(City.name)).all()
    if not cities:
        console.print("[yellow]No cities found.[/yellow]")
        return

    for city in cities:
        poi_count = len(city.pois)
        layer_count = len(city.layers)
        console.print(
            f"[cyan]{city.slug}[/cyan] - {city.name} ({layer_count} layers, {poi_count} POIs)"
        )


@click.command("import-csv")
@click.argument("city_slug")
@click.argument("layer_slug")
@click.argument("csv_file", type=click.Path(exists=True))
@click.option("--name-col", default="name", help="Column for POI name")
@click.option("--lat-col", default="lat", help="Column for latitude")
@click.option("--lng-col", default="lng", help="Column for longitude")
@click.option("--address-col", default="address", help="Column for address")
@click.option("--district-col", default="district", help="Column for district")
@with_appcontext
def import_csv(city_slug, layer_slug, csv_file, name_col, lat_col, lng_col, address_col, district_col):
    """Import POIs from a CSV file."""
    import csv

    from openstadt.api.models import City, Layer, POI

    city = db.session.scalars(db.select(City).where(City.slug == city_slug)).first()
    if not city:
        console.print(f"[red]City '{city_slug}' not found.[/red]")
        return

    layer = db.session.scalars(
        db.select(Layer).where(Layer.city_id == city.id, Layer.slug == layer_slug)
    ).first()
    if not layer:
        console.print(f"[red]Layer '{layer_slug}' not found in {city.name}.[/red]")
        return

    with open(csv_file, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                lat = float(row.get(lat_col, 0))
                lng = float(row.get(lng_col, 0))
            except (ValueError, TypeError):
                continue

            if not lat or not lng:
                continue

            name = row.get(name_col, "Unknown")

            # Store extra columns as attributes
            skip_cols = {name_col, lat_col, lng_col, address_col, district_col}
            attributes = {k: v for k, v in row.items() if k not in skip_cols and v}

            poi = POI(
                city_id=city.id,
                layer_id=layer.id,
                name=name,
                lat=lat,
                lng=lng,
                address=row.get(address_col),
                district=row.get(district_col),
                attributes=attributes if attributes else None,
            )
            db.session.add(poi)
            count += 1

        db.session.commit()
        console.print(f"[green]Imported {count} POIs to {layer.name}.[/green]")


@click.command("sync-osm")
@click.argument("city_slug")
@click.argument("layer_slug")
@with_appcontext
def sync_osm(city_slug, layer_slug):
    """Sync POIs from OpenStreetMap Overpass API."""
    import httpx

    from openstadt.api.models import City, Layer, POI

    city = db.session.scalars(db.select(City).where(City.slug == city_slug)).first()
    if not city:
        console.print(f"[red]City '{city_slug}' not found.[/red]")
        return

    layer = db.session.scalars(
        db.select(Layer).where(Layer.city_id == city.id, Layer.slug == layer_slug)
    ).first()
    if not layer:
        console.print(f"[red]Layer '{layer_slug}' not found in {city.name}.[/red]")
        return

    if layer.source_type != "osm":
        console.print(f"[red]Layer '{layer_slug}' is not an OSM layer.[/red]")
        return

    osm_query = layer.source_config
    if not osm_query:
        console.print(f"[red]No OSM query configured for layer.[/red]")
        return

    # Build Overpass query
    bounds = city.bounds or [
        [city.center_lat - 0.1, city.center_lng - 0.1],
        [city.center_lat + 0.1, city.center_lng + 0.1],
    ]
    bbox = f"{bounds[0][0]},{bounds[0][1]},{bounds[1][0]},{bounds[1][1]}"

    query = f"""
    [out:json][timeout:60];
    (
      node[{osm_query}]({bbox});
      way[{osm_query}]({bbox});
    );
    out center;
    """

    console.print(f"[yellow]Fetching from Overpass API...[/yellow]")

    # Try multiple Overpass API endpoints
    endpoints = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
    ]
    response = None
    for endpoint in endpoints:
        try:
            console.print(f"[yellow]Trying {endpoint}...[/yellow]")
            response = httpx.post(
                endpoint,
                data={"data": query},
                timeout=90,
            )
            response.raise_for_status()
            break
        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
            continue

    if not response:
        console.print("[red]All Overpass endpoints failed.[/red]")
        return

    try:
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        console.print(f"[red]Error fetching OSM data: {e}[/red]")
        return

    # Clear existing POIs for this layer (full sync)
    db.session.execute(db.delete(POI).where(POI.layer_id == layer.id))

    count = 0
    for element in data.get("elements", []):
        if element["type"] == "node":
            lat, lng = element["lat"], element["lon"]
        elif "center" in element:
            lat, lng = element["center"]["lat"], element["center"]["lon"]
        else:
            continue

        tags = element.get("tags", {})

        # Generate meaningful name from OSM tags
        name = tags.get("name")
        if not name:
            name = tags.get("operator")
        if not name:
            # Try to build name from type tags
            if tags.get("amenity") == "recycling":
                recycling_types = [k.split(":")[1] for k in tags.keys() if k.startswith("recycling:") and tags[k] == "yes"]
                if recycling_types:
                    name = f"Recycling: {', '.join(recycling_types[:3])}"
                else:
                    name = "Recyclingcontainer"
            elif tags.get("leisure") == "playground":
                name = tags.get("description", "Spielplatz")
            elif tags.get("amenity") == "kindergarten":
                name = "Kindergarten"
            elif tags.get("amenity") == "school":
                name = tags.get("school:type", "Schule")
            elif tags.get("natural") == "tree":
                species = tags.get("species:de") or tags.get("species") or tags.get("genus:de") or tags.get("genus")
                name = species if species else "Baum"
            else:
                # Fallback: use layer name + address or ID
                addr = tags.get("addr:street", "")
                if addr:
                    name = f"{layer.name} - {addr}"
                else:
                    name = f"{layer.name} #{count + 1}"

        # Build address only if we have street info
        street = tags.get("addr:street", "")
        housenumber = tags.get("addr:housenumber", "")
        address = f"{street} {housenumber}".strip() if street else None

        poi = POI(
            city_id=city.id,
            layer_id=layer.id,
            name=name,
            lat=lat,
            lng=lng,
            address=address,
            source_id=str(element["id"]),
            attributes={k: v for k, v in tags.items() if k not in ("name", "addr:street", "addr:housenumber")},
        )
        db.session.add(poi)
        count += 1

    from datetime import datetime
    layer.last_sync = datetime.now()
    db.session.commit()

    console.print(f"[green]Synced {count} POIs from OpenStreetMap.[/green]")


@click.command("sync-districts")
@click.argument("city_slug")
@with_appcontext
def sync_districts(city_slug):
    """Sync district boundaries from OpenStreetMap."""
    import httpx

    from openstadt.api.models import City, District

    city = db.session.scalars(db.select(City).where(City.slug == city_slug)).first()
    if not city:
        console.print(f"[red]City '{city_slug}' not found.[/red]")
        return

    # OSM relation IDs for German cities (admin_level=4 for city-states, 6 for others)
    # This ensures we only get districts WITHIN the city, not surrounding areas
    city_osm_relations = {
        "berlin": 62422,      # Berlin (city-state)
        "hamburg": 62782,     # Hamburg (city-state)
        "muenchen": 62428,    # München
        "koeln": 62578,       # Köln
        "frankfurt": 62400,   # Frankfurt am Main
        "mannheim": 62691,    # Mannheim
        "darmstadt": 62581,   # Darmstadt
    }

    osm_relation_id = city_osm_relations.get(city_slug)

    if osm_relation_id:
        # Use area-based query to get only districts within the city
        query = f"""
        [out:json][timeout:90];
        area({3600000000 + osm_relation_id})->.city;
        relation["boundary"="administrative"]["admin_level"~"9|10"](area.city);
        out body;
        >;
        out skel qt;
        """
        console.print(f"[yellow]Using OSM relation {osm_relation_id} for precise boundary[/yellow]")
    else:
        # Fallback to bounding box (less accurate)
        bounds = city.bounds or [
            [city.center_lat - 0.15, city.center_lng - 0.15],
            [city.center_lat + 0.15, city.center_lng + 0.15],
        ]
        bbox = f"{bounds[0][0]},{bounds[0][1]},{bounds[1][0]},{bounds[1][1]}"
        query = f"""
        [out:json][timeout:90];
        (
          relation["boundary"="administrative"]["admin_level"~"9|10"]({bbox});
        );
        out body;
        >;
        out skel qt;
        """
        console.print(f"[yellow]Warning: No OSM relation ID for {city_slug}, using bbox (may include surrounding areas)[/yellow]")

    console.print(f"[yellow]Fetching district boundaries from Overpass API...[/yellow]")

    endpoints = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
    ]
    response = None
    for endpoint in endpoints:
        try:
            console.print(f"[yellow]Trying {endpoint}...[/yellow]")
            response = httpx.post(
                endpoint,
                data={"data": query},
                timeout=120,
            )
            response.raise_for_status()
            break
        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
            continue

    if not response:
        console.print("[red]All Overpass endpoints failed.[/red]")
        return

    try:
        data = response.json()
    except Exception as e:
        console.print(f"[red]Error parsing response: {e}[/red]")
        return

    # Parse OSM data into districts
    elements = data.get("elements", [])
    nodes = {e["id"]: e for e in elements if e["type"] == "node"}
    ways = {e["id"]: e for e in elements if e["type"] == "way"}
    relations = [e for e in elements if e["type"] == "relation"]

    # Clear existing districts for this city (full sync)
    console.print(f"[yellow]Clearing existing districts...[/yellow]")
    db.session.execute(db.delete(District).where(District.city_id == city.id))

    # Also clear district assignments on POIs
    from openstadt.api.models import POI
    db.session.execute(
        db.update(POI).where(POI.city_id == city.id).values(district=None)
    )

    count = 0
    for rel in relations:
        tags = rel.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        # Build polygon from relation members
        outer_coords = []
        for member in rel.get("members", []):
            if member.get("role") == "outer" and member.get("type") == "way":
                way = ways.get(member["ref"])
                if way:
                    for node_id in way.get("nodes", []):
                        node = nodes.get(node_id)
                        if node:
                            outer_coords.append([node["lon"], node["lat"]])

        if len(outer_coords) < 3:
            continue

        # Create GeoJSON polygon
        geometry = {
            "type": "Polygon",
            "coordinates": [outer_coords]
        }

        # Calculate approximate area (rough estimate)
        area_km2 = _calculate_polygon_area(outer_coords)

        # Create slug from name
        slug = name.lower().replace(" ", "-").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")

        # Create or update district
        district = db.session.scalars(
            db.select(District).where(District.city_id == city.id, District.slug == slug)
        ).first()
        if not district:
            district = District(city_id=city.id, slug=slug)

        district.name = name
        district.geometry = geometry
        district.area_km2 = round(area_km2, 2) if area_km2 else None

        db.session.add(district)
        count += 1

    db.session.commit()
    console.print(f"[green]Synced {count} districts from OpenStreetMap.[/green]")


def _calculate_polygon_area(coords):
    """Calculate approximate area of polygon in km² using Shoelace formula."""
    import math

    if len(coords) < 3:
        return 0

    # Convert to radians and calculate using spherical approximation
    n = len(coords)
    area = 0
    for i in range(n):
        j = (i + 1) % n
        lng1, lat1 = math.radians(coords[i][0]), math.radians(coords[i][1])
        lng2, lat2 = math.radians(coords[j][0]), math.radians(coords[j][1])
        area += lng1 * lat2
        area -= lng2 * lat1

    area = abs(area) / 2
    # Convert from steradians to km² (Earth radius ≈ 6371 km)
    area_km2 = area * (6371 ** 2)
    return area_km2


@click.command("assign-districts")
@click.argument("city_slug")
@with_appcontext
def assign_districts(city_slug):
    """Assign POIs to districts based on their location (point-in-polygon)."""
    from openstadt.api.models import City, District, POI

    city = db.session.scalars(db.select(City).where(City.slug == city_slug)).first()
    if not city:
        console.print(f"[red]City '{city_slug}' not found.[/red]")
        return

    districts = db.session.scalars(
        db.select(District).where(District.city_id == city.id, District.geometry.isnot(None))
    ).all()

    if not districts:
        console.print(f"[red]No districts with geometry found. Run sync-districts first.[/red]")
        return

    console.print(f"[yellow]Assigning {len(city.pois)} POIs to {len(districts)} districts...[/yellow]")

    assigned = 0
    for poi in city.pois:
        for district in districts:
            if _point_in_polygon(poi.lng, poi.lat, district.geometry):
                poi.district = district.name
                assigned += 1
                break

    db.session.commit()
    console.print(f"[green]Assigned {assigned} POIs to districts.[/green]")


def _point_in_polygon(x, y, geometry):
    """Check if point (x=lng, y=lat) is inside a GeoJSON polygon using ray casting."""
    if not geometry or geometry.get("type") != "Polygon":
        return False

    coords = geometry.get("coordinates", [[]])[0]
    if len(coords) < 3:
        return False

    n = len(coords)
    inside = False

    j = n - 1
    for i in range(n):
        xi, yi = coords[i]
        xj, yj = coords[j]

        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i

    return inside


@click.command("sync-all")
@click.option("--city", "-c", default=None, help="Sync only this city (slug)")
@click.option("--skip-load", is_flag=True, help="Skip loading city configs")
@with_appcontext
def sync_all(city, skip_load):
    """
    Load all city configs and sync all OSM data.

    Examples:
        flask sync-all                  # Load & sync all cities
        flask sync-all -c berlin        # Only sync Berlin
        flask sync-all --skip-load      # Skip config loading, just sync OSM
    """
    import yaml
    from openstadt.api.models import City, Layer, POI
    import httpx

    config_dir = Path("config/cities")
    if not config_dir.exists():
        console.print(f"[red]Config directory not found: {config_dir}[/red]")
        return

    # Find all city configs (exclude template)
    config_files = [f for f in config_dir.glob("*.yaml") if not f.name.startswith("_")]

    if not config_files:
        console.print("[yellow]No city configs found.[/yellow]")
        return

    console.print(f"[bold]Found {len(config_files)} city configs[/bold]\n")

    for config_file in sorted(config_files):
        with open(config_file) as f:
            config = yaml.safe_load(f)

        city_data = config.get("city", {})
        slug = city_data.get("slug")

        if not slug:
            continue

        # Filter by city if specified
        if city and slug != city:
            continue

        console.print(f"[bold cyan]{'='*50}[/bold cyan]")
        console.print(f"[bold cyan]{city_data.get('name', slug)}[/bold cyan]")
        console.print(f"[bold cyan]{'='*50}[/bold cyan]")

        # Step 1: Load city config
        if not skip_load:
            console.print(f"\n[yellow]Loading config...[/yellow]")
            _load_city_config(config)
            console.print(f"[green]✓ City config loaded[/green]")

        # Step 2: Sync OSM layers
        city_obj = db.session.scalars(db.select(City).where(City.slug == slug)).first()
        if not city_obj:
            console.print(f"[red]City not found in database[/red]")
            continue

        layers = db.session.scalars(
            db.select(Layer).where(Layer.city_id == city_obj.id, Layer.source_type == "osm")
        ).all()

        for layer in layers:
            console.print(f"\n[yellow]Syncing {layer.name}...[/yellow]")
            count = _sync_osm_layer(city_obj, layer)
            if count >= 0:
                console.print(f"[green]✓ {layer.name}: {count} POIs[/green]")
            else:
                console.print(f"[red]✗ {layer.name}: sync failed[/red]")

        console.print()

    console.print("[bold green]Done![/bold green]")


def _load_city_config(config):
    """Internal: Load city from config dict."""
    from openstadt.api.models import City, Layer

    city_data = config.get("city", {})
    slug = city_data.get("slug")

    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        city = City(slug=slug)

    city.name = city_data.get("name", slug.title())
    city.state = city_data.get("state")
    center = city_data.get("center", [49.4875, 8.4660])
    city.center_lat = center[0]
    city.center_lng = center[1]
    city.default_zoom = city_data.get("zoom", 12)
    city.bounds = city_data.get("bounds")

    theme = config.get("theme", {})
    city.primary_color = theme.get("primary_color", "#0066CC")
    city.logo_url = theme.get("logo")
    city.config = config

    db.session.add(city)
    db.session.flush()

    for layer_data in config.get("layers", []):
        layer_slug = layer_data.get("slug")
        if not layer_slug:
            continue

        layer = db.session.scalars(
            db.select(Layer).where(Layer.city_id == city.id, Layer.slug == layer_slug)
        ).first()
        if not layer:
            layer = Layer(city_id=city.id, slug=layer_slug)

        layer.name = layer_data.get("name", layer_slug.title())
        layer.name_de = layer_data.get("name_de")
        layer.icon = layer_data.get("icon", "map-marker")
        layer.color = layer_data.get("color", "#3388ff")
        layer.visible_by_default = layer_data.get("visible", True)

        source = layer_data.get("source", {})
        layer.source_type = source.get("type")
        layer.source_url = source.get("url")
        layer.source_config = source.get("mapping") or source.get("query")
        layer.schema = layer_data.get("attributes")

        db.session.add(layer)

    db.session.commit()


def _sync_osm_layer(city, layer):
    """Internal: Sync a single OSM layer. Returns POI count or -1 on error."""
    import httpx
    from openstadt.api.models import POI

    osm_query = layer.source_config
    if not osm_query:
        return -1

    bounds = city.bounds or [
        [city.center_lat - 0.1, city.center_lng - 0.1],
        [city.center_lat + 0.1, city.center_lng + 0.1],
    ]
    bbox = f"{bounds[0][0]},{bounds[0][1]},{bounds[1][0]},{bounds[1][1]}"

    query = f"""
    [out:json][timeout:60];
    (
      node[{osm_query}]({bbox});
      way[{osm_query}]({bbox});
    );
    out center;
    """

    endpoints = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
    ]

    response = None
    for endpoint in endpoints:
        try:
            response = httpx.post(endpoint, data={"data": query}, timeout=90)
            response.raise_for_status()
            break
        except Exception:
            continue

    if not response:
        return -1

    try:
        data = response.json()
    except Exception:
        return -1

    # Clear existing POIs
    db.session.execute(db.delete(POI).where(POI.layer_id == layer.id))

    count = 0
    for element in data.get("elements", []):
        if element["type"] == "node":
            lat, lng = element["lat"], element["lon"]
        elif "center" in element:
            lat, lng = element["center"]["lat"], element["center"]["lon"]
        else:
            continue

        tags = element.get("tags", {})
        name = tags.get("name") or tags.get("operator")

        if not name:
            if tags.get("amenity") == "recycling":
                recycling_types = [k.split(":")[1] for k in tags.keys() if k.startswith("recycling:") and tags[k] == "yes"]
                name = f"Recycling: {', '.join(recycling_types[:3])}" if recycling_types else "Recyclingcontainer"
            elif tags.get("leisure") == "playground":
                name = tags.get("description", "Spielplatz")
            elif tags.get("amenity") == "kindergarten":
                name = "Kindergarten"
            elif tags.get("amenity") == "school":
                name = tags.get("school:type", "Schule")
            else:
                name = f"{layer.name} #{count + 1}"

        street = tags.get("addr:street", "")
        housenumber = tags.get("addr:housenumber", "")
        address = f"{street} {housenumber}".strip() if street else None

        poi = POI(
            city_id=city.id,
            layer_id=layer.id,
            name=name,
            lat=lat,
            lng=lng,
            address=address,
            source_id=str(element["id"]),
            attributes={k: v for k, v in tags.items() if k not in ("name", "addr:street", "addr:housenumber")},
        )
        db.session.add(poi)
        count += 1

    from datetime import datetime
    layer.last_sync = datetime.now()
    db.session.commit()

    return count
