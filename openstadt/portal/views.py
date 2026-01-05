"""Portal views - admin dashboard for city data management."""

from flask import Blueprint, render_template
from flask_security import auth_required

from openstadt.api.models import City, Layer, POI
from openstadt.extensions import db

portal = Blueprint("portal", __name__, url_prefix="/dashboard")


@portal.before_request
@auth_required("session")
def before_request():
    """Protect all portal routes."""
    pass


@portal.route("/")
def index():
    """Dashboard home - overview of all cities."""
    cities = db.session.scalars(db.select(City).order_by(City.name)).all()
    total_pois = db.session.scalar(db.select(db.func.count(POI.id)))
    total_layers = db.session.scalar(db.select(db.func.count(Layer.id)))

    return render_template(
        "portal/index.html",
        cities=cities,
        total_pois=total_pois,
        total_layers=total_layers,
    )


@portal.route("/cities")
def cities():
    """City management."""
    cities = db.session.scalars(db.select(City).order_by(City.name)).all()
    return render_template("portal/cities.html", cities=cities)


@portal.route("/cities/<slug>")
def city_detail(slug):
    """City detail - layers and stats."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return render_template("errors/404.html"), 404

    return render_template("portal/city.html", city=city)


@portal.route("/cities/<slug>/layers/<layer_slug>")
def layer_detail(slug, layer_slug):
    """Layer detail - POI list and import."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return render_template("errors/404.html"), 404

    layer = db.session.scalars(
        db.select(Layer).where(Layer.city_id == city.id, Layer.slug == layer_slug)
    ).first()
    if not layer:
        return render_template("errors/404.html"), 404

    return render_template("portal/layer.html", city=city, layer=layer)


@portal.route("/import")
def import_page():
    """Data import interface."""
    cities = db.session.scalars(db.select(City).order_by(City.name)).all()
    return render_template("portal/import.html", cities=cities)
