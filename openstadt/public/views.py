"""Public views - the main map interface."""

from flask import Blueprint, current_app, redirect, render_template, url_for

from openstadt.api.models import City
from openstadt.extensions import db

public = Blueprint("public", __name__)


@public.route("/")
def index():
    """Landing page - redirect to default city or show city selection."""
    default_city = current_app.config.get("DEFAULT_CITY")
    if default_city:
        return redirect(url_for("public.city_map", slug=default_city))

    # Show all cities
    cities = db.session.scalars(db.select(City).order_by(City.name)).all()
    return render_template("public/index.html", cities=cities)


@public.route("/<slug>")
def city_map(slug):
    """Main map view for a city."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return render_template("errors/404.html"), 404

    # Pass all cities for the city switcher (simplified list)
    all_cities = db.session.scalars(db.select(City).order_by(City.name)).all()
    cities_list = [{"slug": c.slug, "name": c.name} for c in all_cities]
    return render_template("public/map.html", city=city, all_cities=cities_list)


@public.route("/<slug>/poi/<int:poi_id>")
def poi_detail(slug, poi_id):
    """POI detail page (for sharing/SEO)."""
    from openstadt.api.models import POI

    query = db.select(POI).join(City).where(City.slug == slug, POI.id == poi_id)
    poi = db.session.scalars(query).first()
    if not poi:
        return render_template("errors/404.html"), 404

    return render_template("public/poi.html", city=poi.city, poi=poi)


@public.route("/<slug>/analytics")
def city_analytics(slug):
    """Equity analysis dashboard for a city."""
    city = db.session.scalars(db.select(City).where(City.slug == slug)).first()
    if not city:
        return render_template("errors/404.html"), 404

    return render_template("public/analytics.html", city=city)
