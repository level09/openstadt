"""Core civic data models for OpenStadt."""

from datetime import datetime

from openstadt.extensions import db
from openstadt.utils.base import BaseMixin


class City(db.Model, BaseMixin):
    """A city/municipality that has its own civic data."""

    __tablename__ = "city"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=True)  # Bundesland

    # Map configuration
    center_lat = db.Column(db.Float, nullable=False, default=49.4875)
    center_lng = db.Column(db.Float, nullable=False, default=8.4660)
    default_zoom = db.Column(db.Integer, default=12)
    bounds = db.Column(db.JSON, nullable=True)  # [[lat,lng], [lat,lng]]

    # Theme
    primary_color = db.Column(db.String(7), default="#0066CC")
    logo_url = db.Column(db.String(500), nullable=True)

    # Config from YAML
    config = db.Column(db.JSON, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # Relationships
    layers = db.relationship("Layer", back_populates="city", cascade="all, delete")
    pois = db.relationship("POI", back_populates="city", cascade="all, delete")
    districts = db.relationship(
        "District", back_populates="city", cascade="all, delete"
    )

    def to_dict(self, include_layers=False):
        result = {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "state": self.state,
            "center": [self.center_lat, self.center_lng],
            "defaultZoom": self.default_zoom,
            "bounds": self.bounds,
            "primaryColor": self.primary_color,
            "logoUrl": self.logo_url,
        }
        if include_layers:
            result["layers"] = [layer.to_dict(include_stats=True) for layer in self.layers]
        return result


class Layer(db.Model, BaseMixin):
    """A layer of POIs (e.g., kitas, playgrounds, trees)."""

    __tablename__ = "layer"

    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("city.id"), nullable=False)
    slug = db.Column(db.String(50), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # Display name
    name_de = db.Column(db.String(100), nullable=True)  # German name

    # Display
    icon = db.Column(db.String(50), default="map-marker")  # FontAwesome/Mdi icon
    color = db.Column(db.String(7), default="#3388ff")
    visible_by_default = db.Column(db.Boolean, default=True)

    # Data source configuration
    source_type = db.Column(db.String(20), nullable=True)  # csv, geojson, osm
    source_url = db.Column(db.String(500), nullable=True)
    source_config = db.Column(db.JSON, nullable=True)  # column mapping, OSM query, etc.

    # Schema for POI attributes
    schema = db.Column(db.JSON, nullable=True)  # field definitions

    # Timestamps
    last_sync = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # Relationships
    city = db.relationship("City", back_populates="layers")
    pois = db.relationship("POI", back_populates="layer", cascade="all, delete")

    # Unique constraint: slug per city
    __table_args__ = (
        db.UniqueConstraint("city_id", "slug", name="uq_layer_city_slug"),
    )

    def to_dict(self, include_stats=False):
        result = {
            "id": self.id,
            "cityId": self.city_id,
            "slug": self.slug,
            "name": self.name,
            "nameDe": self.name_de,
            "icon": self.icon,
            "color": self.color,
            "visibleByDefault": self.visible_by_default,
            "sourceType": self.source_type,
            "schema": self.schema,
            "lastSync": self.last_sync.isoformat() if self.last_sync else None,
        }
        if include_stats:
            result["poiCount"] = len(self.pois)
        return result


class POI(db.Model, BaseMixin):
    """A Point of Interest (civic facility, tree, etc.)."""

    __tablename__ = "poi"

    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("city.id"), nullable=False)
    layer_id = db.Column(db.Integer, db.ForeignKey("layer.id"), nullable=False)

    # Core data
    name = db.Column(db.String(200), nullable=False)
    lat = db.Column(db.Float, nullable=False, index=True)
    lng = db.Column(db.Float, nullable=False, index=True)
    address = db.Column(db.String(300), nullable=True)
    district = db.Column(db.String(100), nullable=True, index=True)

    # Flexible attributes (layer-specific data)
    attributes = db.Column(db.JSON, nullable=True)

    # External reference
    source_id = db.Column(db.String(100), nullable=True, index=True)
    source_url = db.Column(db.String(500), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # Relationships
    city = db.relationship("City", back_populates="pois")
    layer = db.relationship("Layer", back_populates="pois")

    # Indexes for common queries
    __table_args__ = (
        db.Index("idx_poi_location", "lat", "lng"),
        db.Index("ix_poi_city_id", "city_id"),
        db.Index("ix_poi_city_district_layer", "city_id", "district", "layer_id"),
    )

    def to_dict(self, include_layer=False):
        result = {
            "id": self.id,
            "cityId": self.city_id,
            "layerId": self.layer_id,
            "name": self.name,
            "lat": self.lat,
            "lng": self.lng,
            "address": self.address,
            "district": self.district,
            "attributes": self.attributes or {},
            "sourceId": self.source_id,
            "sourceUrl": self.source_url,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_layer and self.layer:
            result["layer"] = {
                "slug": self.layer.slug,
                "name": self.layer.name,
                "icon": self.layer.icon,
                "color": self.layer.color,
            }
        return result

    def to_geojson(self):
        """Return POI as GeoJSON Feature."""
        return {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [self.lng, self.lat]},
            "properties": {
                "id": self.id,
                "name": self.name,
                "layerId": self.layer_id,
                "address": self.address,
                "district": self.district,
                **(self.attributes or {}),
            },
        }


class District(db.Model, BaseMixin):
    """Administrative district/neighborhood within a city."""

    __tablename__ = "district"

    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("city.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), nullable=False, index=True)

    # GeoJSON polygon
    geometry = db.Column(db.JSON, nullable=True)

    # Demographics (for equity calculations)
    population = db.Column(db.Integer, nullable=True)
    area_km2 = db.Column(db.Float, nullable=True)  # Area in square kilometers

    # Relationships
    city = db.relationship("City", back_populates="districts")

    __table_args__ = (
        db.UniqueConstraint("city_id", "slug", name="uq_district_city_slug"),
    )

    def to_dict(self, include_geometry=False):
        result = {
            "id": self.id,
            "cityId": self.city_id,
            "name": self.name,
            "slug": self.slug,
            "population": self.population,
            "areaKm2": self.area_km2,
        }
        if include_geometry and self.geometry:
            result["geometry"] = self.geometry
        return result

    def to_geojson(self):
        """Return district as GeoJSON Feature."""
        return {
            "type": "Feature",
            "geometry": self.geometry,
            "properties": {
                "id": self.id,
                "name": self.name,
                "slug": self.slug,
            },
        }
