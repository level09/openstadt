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
