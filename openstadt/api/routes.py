"""Public API endpoints for OpenStadt."""

from flask import Blueprint, jsonify, request

from openstadt.api.models import City, District, Layer, POI
from openstadt.extensions import db

api = Blueprint("api", __name__, url_prefix="/api/v1")


# ============================================================
# Cities
# ============================================================


@api.route("/cities", methods=["GET"])
def list_cities():
    """List all cities."""
    query = db.select(City).order_by(City.name)
    cities = db.session.scalars(query).all()
    return jsonify({"items": [c.to_dict() for c in cities]})


@api.route("/cities/<slug>", methods=["GET"])
def get_city(slug):
    """Get a single city by slug."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return jsonify({"error": "City not found"}), 404
    return jsonify(city.to_dict(include_layers=True))


# ============================================================
# Layers
# ============================================================


@api.route("/cities/<slug>/layers", methods=["GET"])
def list_layers(slug):
    """List all layers for a city."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return jsonify({"error": "City not found"}), 404

    return jsonify({"items": [layer.to_dict(include_stats=True) for layer in city.layers]})


@api.route("/cities/<slug>/layers/<layer_slug>", methods=["GET"])
def get_layer(slug, layer_slug):
    """Get a single layer."""
    query = (
        db.select(Layer)
        .join(City)
        .where(City.slug == slug, Layer.slug == layer_slug)
    )
    layer = db.session.scalars(query).first()
    if not layer:
        return jsonify({"error": "Layer not found"}), 404
    return jsonify(layer.to_dict(include_stats=True))


# ============================================================
# POIs
# ============================================================


@api.route("/cities/<slug>/pois", methods=["GET"])
def list_pois(slug):
    """List POIs for a city with filtering."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return jsonify({"error": "City not found"}), 404

    query = db.select(POI).where(POI.city_id == city.id)

    # Filter by layer
    layer_slug = request.args.get("layer")
    if layer_slug:
        layer = db.session.scalars(
            db.select(Layer).where(Layer.city_id == city.id, Layer.slug == layer_slug)
        ).first()
        if layer:
            query = query.where(POI.layer_id == layer.id)

    # Filter by district
    district = request.args.get("district")
    if district:
        query = query.where(POI.district == district)

    # Bounding box filter
    bbox = request.args.get("bbox")
    if bbox:
        try:
            sw_lat, sw_lng, ne_lat, ne_lng = map(float, bbox.split(","))
            query = query.where(
                POI.lat >= sw_lat,
                POI.lat <= ne_lat,
                POI.lng >= sw_lng,
                POI.lng <= ne_lng,
            )
        except ValueError:
            pass  # ignore invalid bbox

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    per_page = min(per_page, 500)  # cap at 500

    pagination = db.paginate(query, page=page, per_page=per_page)

    return jsonify(
        {
            "items": [poi.to_dict() for poi in pagination.items],
            "total": pagination.total,
            "page": page,
            "perPage": per_page,
        }
    )


@api.route("/cities/<slug>/pois/geojson", methods=["GET"])
def pois_geojson(slug):
    """Get all POIs as GeoJSON FeatureCollection."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return jsonify({"error": "City not found"}), 404

    query = db.select(POI).where(POI.city_id == city.id)

    # Filter by layer(s)
    layers = request.args.get("layers")
    if layers:
        layer_slugs = layers.split(",")
        layer_ids = db.session.scalars(
            db.select(Layer.id).where(
                Layer.city_id == city.id, Layer.slug.in_(layer_slugs)
            )
        ).all()
        query = query.where(POI.layer_id.in_(layer_ids))

    pois = db.session.scalars(query).all()

    return jsonify(
        {
            "type": "FeatureCollection",
            "features": [poi.to_geojson() for poi in pois],
        }
    )


@api.route("/cities/<slug>/pois/<int:poi_id>", methods=["GET"])
def get_poi(slug, poi_id):
    """Get a single POI."""
    query = db.select(POI).join(City).where(City.slug == slug, POI.id == poi_id)
    poi = db.session.scalars(query).first()
    if not poi:
        return jsonify({"error": "POI not found"}), 404
    return jsonify(poi.to_dict(include_layer=True))


# ============================================================
# Search
# ============================================================


@api.route("/cities/<slug>/search", methods=["GET"])
def search_pois(slug):
    """Search POIs by name."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return jsonify({"error": "City not found"}), 404

    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify({"items": []})

    query = (
        db.select(POI)
        .where(POI.city_id == city.id, POI.name.ilike(f"%{q}%"))
        .limit(20)
    )
    pois = db.session.scalars(query).all()

    return jsonify({"items": [poi.to_dict(include_layer=True) for poi in pois]})


# ============================================================
# Districts
# ============================================================


@api.route("/cities/<slug>/districts", methods=["GET"])
def list_districts(slug):
    """List all districts for a city."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return jsonify({"error": "City not found"}), 404

    include_geometry = request.args.get("geometry", "false").lower() == "true"
    return jsonify(
        {
            "items": [
                d.to_dict(include_geometry=include_geometry) for d in city.districts
            ]
        }
    )


@api.route("/cities/<slug>/districts/geojson", methods=["GET"])
def districts_geojson(slug):
    """Get districts as GeoJSON FeatureCollection."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return jsonify({"error": "City not found"}), 404

    return jsonify(
        {
            "type": "FeatureCollection",
            "features": [d.to_geojson() for d in city.districts if d.geometry],
        }
    )


# ============================================================
# Analytics - Equity Analysis
# ============================================================


@api.route("/cities/<slug>/analytics/districts", methods=["GET"])
def district_analytics(slug):
    """Get POI statistics per district for equity analysis."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return jsonify({"error": "City not found"}), 404

    # Get all layers for this city
    layers = {layer.id: layer for layer in city.layers}

    # Get POI counts per district per layer
    district_stats = {}

    # Initialize with districts from database
    for district in city.districts:
        district_stats[district.name] = {
            "name": district.name,
            "slug": district.slug,
            "population": district.population,
            "areaKm2": district.area_km2,
            "layers": {layer.slug: 0 for layer in city.layers},
            "total": 0,
        }

    # Also track districts from POI data (may not have geometry yet)
    for poi in city.pois:
        district_name = poi.district or "Unbekannt"
        if district_name not in district_stats:
            district_stats[district_name] = {
                "name": district_name,
                "slug": district_name.lower().replace(" ", "-"),
                "population": None,
                "areaKm2": None,
                "layers": {layer.slug: 0 for layer in city.layers},
                "total": 0,
            }

        layer = layers.get(poi.layer_id)
        if layer:
            district_stats[district_name]["layers"][layer.slug] += 1
            district_stats[district_name]["total"] += 1

    # Calculate density and equity scores
    results = []
    city_total = sum(d["total"] for d in district_stats.values())
    city_avg = city_total / len(district_stats) if district_stats else 0

    for name, stats in district_stats.items():
        # Calculate equity score (100 = average, >100 = above average)
        if city_avg > 0:
            equity_score = round((stats["total"] / city_avg) * 100)
        else:
            equity_score = 0

        # Calculate density if area is available
        density = None
        if stats["areaKm2"] and stats["areaKm2"] > 0:
            density = round(stats["total"] / stats["areaKm2"], 1)

        results.append({
            **stats,
            "equityScore": equity_score,
            "density": density,
        })

    # Sort by equity score (lowest first to highlight underserved)
    results.sort(key=lambda x: x["equityScore"])

    return jsonify({
        "items": results,
        "summary": {
            "totalPois": city_total,
            "totalDistricts": len(results),
            "cityAverage": round(city_avg, 1),
        }
    })


@api.route("/cities/<slug>/analytics/coverage", methods=["GET"])
def coverage_analysis(slug):
    """Analyze coverage gaps - areas far from facilities."""
    import math

    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return jsonify({"error": "City not found"}), 404

    # Get layer to analyze (default: playgrounds)
    layer_slug = request.args.get("layer", "playgrounds")
    radius_m = request.args.get("radius", 500, type=int)  # meters

    layer = db.session.scalars(
        db.select(Layer).where(Layer.city_id == city.id, Layer.slug == layer_slug)
    ).first()

    if not layer:
        return jsonify({"error": f"Layer '{layer_slug}' not found"}), 404

    # Get all POIs for this layer
    pois = db.session.scalars(
        db.select(POI).where(POI.layer_id == layer.id)
    ).all()

    # Create coverage circles (simplified for API response)
    coverage_points = []
    for poi in pois:
        coverage_points.append({
            "lat": poi.lat,
            "lng": poi.lng,
            "name": poi.name,
            "district": poi.district,
        })

    # Calculate coverage statistics per district
    district_coverage = {}
    for poi in city.pois:
        district = poi.district or "Unbekannt"
        if district not in district_coverage:
            district_coverage[district] = {
                "total": 0,
                "covered": 0,  # POIs within radius of target layer
            }
        district_coverage[district]["total"] += 1

        # Check if this POI is within radius of any target POI
        for target in pois:
            dist = _haversine_distance(poi.lat, poi.lng, target.lat, target.lng)
            if dist <= radius_m:
                district_coverage[district]["covered"] += 1
                break

    # Calculate coverage percentage per district
    coverage_stats = []
    for district, stats in district_coverage.items():
        coverage_pct = round((stats["covered"] / stats["total"]) * 100) if stats["total"] > 0 else 0
        coverage_stats.append({
            "district": district,
            "totalPois": stats["total"],
            "coveredPois": stats["covered"],
            "coveragePct": coverage_pct,
        })

    coverage_stats.sort(key=lambda x: x["coveragePct"])

    return jsonify({
        "layer": layer.slug,
        "layerName": layer.name,
        "radiusMeters": radius_m,
        "totalFacilities": len(pois),
        "coveragePoints": coverage_points,
        "districtCoverage": coverage_stats,
    })


@api.route("/cities/<slug>/analytics/comparison", methods=["GET"])
def layer_comparison(slug):
    """Compare infrastructure across all layers."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return jsonify({"error": "City not found"}), 404

    comparison = []
    for layer in city.layers:
        poi_count = len(layer.pois)

        # Get district distribution
        district_counts = {}
        for poi in layer.pois:
            d = poi.district or "Unbekannt"
            district_counts[d] = district_counts.get(d, 0) + 1

        # Calculate distribution stats
        if district_counts:
            counts = list(district_counts.values())
            avg = sum(counts) / len(counts)
            max_count = max(counts)
            min_count = min(counts)
            spread = max_count - min_count if counts else 0
        else:
            avg = max_count = min_count = spread = 0

        comparison.append({
            "slug": layer.slug,
            "name": layer.name,
            "color": layer.color,
            "totalPois": poi_count,
            "districtsServed": len(district_counts),
            "avgPerDistrict": round(avg, 1),
            "maxInDistrict": max_count,
            "minInDistrict": min_count,
            "distributionSpread": spread,
        })

    return jsonify({"items": comparison})


def _haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points in meters."""
    import math

    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
