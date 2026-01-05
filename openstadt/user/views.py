"""User management views (admin only)."""

from flask import Blueprint, jsonify, render_template, request
from flask_security import auth_required, roles_required

from openstadt.extensions import db
from openstadt.user.models import Activity, Role, User

bp_user = Blueprint("user", __name__, url_prefix="/admin")


@bp_user.before_request
@auth_required("session")
@roles_required("admin")
def before_request():
    """Protect all admin routes."""
    pass


# ============================================================
# User Management
# ============================================================


@bp_user.route("/users")
def users():
    """User management page."""
    roles = db.session.scalars(db.select(Role)).all()
    return render_template("admin/users.html", roles=roles)


@bp_user.route("/api/users", methods=["GET"])
def api_users():
    """List users."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)

    query = db.select(User).order_by(User.created_at.desc())
    pagination = db.paginate(query, page=page, per_page=per_page)

    return jsonify(
        {
            "items": [u.to_dict() for u in pagination.items],
            "total": pagination.total,
            "perPage": per_page,
        }
    )


@bp_user.route("/api/user/", methods=["POST"])
def api_user_create():
    """Create user."""
    from flask_security.utils import hash_password

    data = request.json
    user = User(
        email=data["email"],
        name=data.get("name"),
        password=hash_password(data["password"]),
        active=data.get("active", True),
    )
    if "roles" in data:
        role_ids = [r.get("id") for r in data["roles"]]
        user.roles = (
            db.session.scalars(db.select(Role).where(Role.id.in_(role_ids))).all()
            if role_ids
            else []
        )

    user.save()
    Activity.register(request.user_id if hasattr(request, "user_id") else 0, "User Create", user.to_dict())
    db.session.commit()

    return jsonify(user.to_dict())


@bp_user.route("/api/user/<int:user_id>", methods=["POST"])
def api_user_update(user_id):
    """Update user."""
    user = db.get_or_404(User, user_id)
    old_data = user.to_dict()
    user.from_dict(request.json)
    user.save()
    Activity.register(request.user_id if hasattr(request, "user_id") else 0, "User Update", {"old": old_data, "new": user.to_dict()})
    db.session.commit()

    return jsonify(user.to_dict())


@bp_user.route("/api/user/<int:user_id>", methods=["DELETE"])
def api_user_delete(user_id):
    """Delete user."""
    user = db.get_or_404(User, user_id)
    user_data = user.to_dict()
    user.delete()
    Activity.register(request.user_id if hasattr(request, "user_id") else 0, "User Delete", user_data)
    db.session.commit()

    return jsonify({"success": True})


# ============================================================
# Role Management
# ============================================================


@bp_user.route("/roles")
def roles():
    """Role management page."""
    return render_template("admin/roles.html")


@bp_user.route("/api/roles", methods=["GET"])
def api_roles():
    """List roles."""
    roles = db.session.scalars(db.select(Role)).all()
    return jsonify({"items": [r.to_dict() for r in roles]})


@bp_user.route("/api/role/", methods=["POST"])
def api_role_create():
    """Create role."""
    data = request.json
    role = Role(name=data["name"], description=data.get("description"))
    role.save()
    return jsonify(role.to_dict())


@bp_user.route("/api/role/<int:role_id>", methods=["POST"])
def api_role_update(role_id):
    """Update role."""
    role = db.get_or_404(Role, role_id)
    role.from_dict(request.json)
    role.save()
    return jsonify(role.to_dict())


@bp_user.route("/api/role/<int:role_id>", methods=["DELETE"])
def api_role_delete(role_id):
    """Delete role."""
    role = db.get_or_404(Role, role_id)
    role.delete()
    return jsonify({"success": True})


# ============================================================
# Activity Log
# ============================================================


@bp_user.route("/activities")
def activities():
    """Activity log page."""
    return render_template("admin/activities.html")


@bp_user.route("/api/activities", methods=["GET"])
def api_activities():
    """List activities."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)

    query = db.select(Activity).order_by(Activity.created_at.desc())
    pagination = db.paginate(query, page=page, per_page=per_page)

    return jsonify(
        {
            "items": [
                {
                    "id": a.id,
                    "userId": a.user_id,
                    "action": a.action,
                    "data": a.data,
                    "createdAt": a.created_at.isoformat(),
                }
                for a in pagination.items
            ],
            "total": pagination.total,
            "perPage": per_page,
        }
    )
