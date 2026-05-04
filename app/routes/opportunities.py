from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Opportunity

opportunities_bp = Blueprint("opportunities", __name__, url_prefix="/api/opportunities")

# Valid categories matching HTML <select> options
VALID_CATEGORIES = ["technology", "business", "design", "marketing", "data", "other"]


def check_ownership(opportunity, user):
    """Helper: verify opportunity belongs to current user, else return error tuple."""
    if opportunity.admin_id != user.id:
        return None, ("Not found", 404)
    return opportunity, None


@opportunities_bp.route("", methods=["GET"])
@login_required
def list_opportunities():
    """
    List all opportunities for logged-in admin.
    Returns empty [] if none exist.
    """
    try:
        opportunities = Opportunity.query.filter_by(admin_id=current_user.id).all()
        return jsonify(
            [
                {
                    "id": opp.id,
                    "admin_id": opp.admin_id,
                    "name": opp.name,
                    "category": opp.category,
                    "duration": opp.duration,
                    "start_date": opp.start_date,
                    "description": opp.description,
                    "skills": opp.skills,
                    "future_opportunities": opp.future_opportunities,
                    "max_applicants": opp.max_applicants,
                    "created_at": opp.created_at.isoformat()
                    if opp.created_at
                    else None,
                    "updated_at": opp.updated_at.isoformat()
                    if opp.updated_at
                    else None,
                }
                for opp in opportunities
            ]
        ), 200
    except Exception as e:
        current_app.logger.exception("Error listing opportunities")
        return jsonify({"error": "Internal server error"}), 500


@opportunities_bp.route("", methods=["POST"])
@login_required
def create_opportunity():
    """
    US-2.2: Create new opportunity.
    Expected JSON: {
        "name": "Full Stack Developer",
        "category": "technology",
        "duration": "3 months",
        "start_date": "2024-06-01",
        "description": "Build web apps...",
        "skills": "Python, JavaScript, React",
        "future_opportunities": "Potential full-time offer",
        "max_applicants": 10
    }
    """
    try:
        data = request.get_json() or {}

        # Helper to safely strip string values
        def safe_strip(value):
            if value is None:
                return ""
            if isinstance(value, str):
                return value.strip()
            return str(value).strip()

        # Validate required fields
        errors = {}
        name = safe_strip(data.get("name"))
        category = safe_strip(data.get("category"))
        duration = safe_strip(data.get("duration"))
        start_date = safe_strip(data.get("start_date"))
        description = safe_strip(data.get("description"))
        skills = safe_strip(data.get("skills"))
        future_opportunities = safe_strip(data.get("future_opportunities"))
        max_applicants = data.get("max_applicants")

        if not name:
            errors["name"] = "Name is required"
        if not category:
            errors["category"] = "Category is required"
        elif category not in VALID_CATEGORIES:
            errors["category"] = (
                f"Category must be one of: {', '.join(VALID_CATEGORIES)}"
            )
        if not duration:
            errors["duration"] = "Duration is required"
        if not start_date:
            errors["start_date"] = "Start date is required"
        if not description:
            errors["description"] = "Description is required"
        if not skills:
            errors["skills"] = "Skills are required"
        if not future_opportunities:
            errors["future_opportunities"] = "Future opportunities field is required"

        if max_applicants is not None:
            try:
                max_applicants = int(max_applicants)
            except (ValueError, TypeError):
                errors["max_applicants"] = "Max applicants must be an integer"

        if errors:
            return jsonify({"error": "Validation failed", "fields": errors}), 422

        # Create opportunity
        opp = Opportunity(
            admin_id=current_user.id,
            name=name,
            category=category,
            duration=duration,
            start_date=start_date,
            description=description,
            skills=skills,
            future_opportunities=future_opportunities,
            max_applicants=max_applicants,
        )
        db.session.add(opp)
        db.session.commit()

        return jsonify(
            {
                "id": opp.id,
                "name": opp.name,
                "category": opp.category,
                "duration": opp.duration,
                "start_date": opp.start_date,
                "description": opp.description,
                "skills": opp.skills,
                "future_opportunities": opp.future_opportunities,
                "max_applicants": opp.max_applicants,
                "created_at": opp.created_at.isoformat(),
                "updated_at": opp.updated_at.isoformat(),
                "message": "Opportunity created successfully",
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error creating opportunity")
        return jsonify({"error": "Internal server error"}), 500


@opportunities_bp.route("/<int:opp_id>", methods=["GET"])
@login_required
def get_opportunity(opp_id):
    """US-2.4: Get one opportunity by ID (check ownership)."""
    try:
        opp = Opportunity.query.get(opp_id)

        if not opp:
            return jsonify({"error": "Not found"}), 404

        # Check ownership
        if opp.admin_id != current_user.id:
            return jsonify({"error": "Not found"}), 404

        return jsonify(
            {
                "id": opp.id,
                "name": opp.name,
                "category": opp.category,
                "duration": opp.duration,
                "start_date": opp.start_date,
                "description": opp.description,
                "skills": opp.skills,
                "future_opportunities": opp.future_opportunities,
                "max_applicants": opp.max_applicants,
                "created_at": opp.created_at.isoformat() if opp.created_at else None,
                "updated_at": opp.updated_at.isoformat() if opp.updated_at else None,
            }
        ), 200

    except Exception as e:
        current_app.logger.exception("Error getting opportunity")
        return jsonify({"error": "Internal server error"}), 500


@opportunities_bp.route("/<int:opp_id>", methods=["PUT"])
@login_required
def update_opportunity(opp_id):
    """
    US-2.5: Update opportunity (check ownership).
    All fields optional (partial update).
    """
    try:
        opp = Opportunity.query.get(opp_id)

        if not opp:
            return jsonify({"error": "Not found"}), 404

        if opp.admin_id != current_user.id:
            return jsonify({"error": "Not found"}), 404

        data = request.get_json() or {}

        # Validate fields if provided
        errors = {}

        if "category" in data and data["category"] not in VALID_CATEGORIES:
            errors["category"] = (
                f"Category must be one of: {', '.join(VALID_CATEGORIES)}"
            )

        if "max_applicants" in data and data["max_applicants"] is not None:
            try:
                data["max_applicants"] = int(data["max_applicants"])
            except (ValueError, TypeError):
                errors["max_applicants"] = "Max applicants must be an integer"

        if errors:
            return jsonify({"error": "Validation failed", "fields": errors}), 422

        # Update only provided fields
        for field in [
            "name",
            "category",
            "duration",
            "start_date",
            "description",
            "skills",
            "future_opportunities",
            "max_applicants",
        ]:
            if field in data:
                setattr(opp, field, data[field])

        db.session.commit()

        return jsonify(
            {
                "id": opp.id,
                "name": opp.name,
                "category": opp.category,
                "duration": opp.duration,
                "start_date": opp.start_date,
                "description": opp.description,
                "skills": opp.skills,
                "future_opportunities": opp.future_opportunities,
                "max_applicants": opp.max_applicants,
                "created_at": opp.created_at.isoformat() if opp.created_at else None,
                "updated_at": opp.updated_at.isoformat() if opp.updated_at else None,
                "message": "Opportunity updated successfully",
            }
        ), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error updating opportunity")
        return jsonify({"error": "Internal server error"}), 500


@opportunities_bp.route("/<int:opp_id>", methods=["DELETE"])
@login_required
def delete_opportunity(opp_id):
    """US-2.6: Delete opportunity (check ownership)."""
    try:
        opp = Opportunity.query.get(opp_id)

        if not opp:
            return jsonify({"error": "Not found"}), 404

        if opp.admin_id != current_user.id:
            return jsonify({"error": "Not found"}), 404

        db.session.delete(opp)
        db.session.commit()

        return "", 204

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error deleting opportunity")
        return jsonify({"error": "Internal server error"}), 500
