import pytest
from app.extensions import db
from app.models import Opportunity


class TestOpportunityCRUD:
    """US-2.1–2.6: Opportunity CRUD tests."""

    def test_list_empty(self, login_admin_a):
        """New admin sees empty opportunities list."""
        res = login_admin_a.get("/api/opportunities")

        assert res.status_code == 200
        data = res.get_json()
        assert data == []

    def test_create_success(self, login_admin_a):
        """Create opportunity returns 201."""
        res = login_admin_a.post(
            "/api/opportunities",
            json={
                "name": "Full Stack Dev",
                "category": "technology",
                "duration": "3 months",
                "start_date": "2024-06-01",
                "description": "Build web apps",
                "skills": "Python, JavaScript, React",
                "future_opportunities": "Full-time offer",
                "max_applicants": 10,
            },
        )

        assert res.status_code == 201
        data = res.get_json()
        assert data["name"] == "Full Stack Dev"
        assert data["id"] is not None

    def test_create_missing_field(self, login_admin_a):
        """Missing required field returns 422."""
        res = login_admin_a.post(
            "/api/opportunities",
            json={
                "name": "Full Stack Dev",
                # Missing category, duration, etc.
            },
        )

        assert res.status_code == 422
        assert "Validation failed" in res.get_json()["error"]

    def test_create_invalid_category(self, login_admin_a):
        """Invalid category returns 422."""
        res = login_admin_a.post(
            "/api/opportunities",
            json={
                "name": "Some Role",
                "category": "invalid_category",
                "duration": "3 months",
                "start_date": "2024-06-01",
                "description": "Desc",
                "skills": "Skills",
                "future_opportunities": "Future",
            },
        )

        assert res.status_code == 422

    def test_list_after_create(self, login_admin_a):
        """List returns created opportunity."""
        # Create
        create_res = login_admin_a.post(
            "/api/opportunities",
            json={
                "name": "Data Science",
                "category": "data",
                "duration": "6 months",
                "start_date": "2024-07-01",
                "description": "Analyze data",
                "skills": "Python, SQL, ML",
                "future_opportunities": "Possible hire",
                "max_applicants": 5,
            },
        )
        opp_id = create_res.get_json()["id"]

        # List
        list_res = login_admin_a.get("/api/opportunities")

        assert list_res.status_code == 200
        opportunities = list_res.get_json()
        assert len(opportunities) == 1
        assert opportunities[0]["id"] == opp_id
        assert opportunities[0]["name"] == "Data Science"

    def test_get_opportunity(self, login_admin_a):
        """Get single opportunity returns full object."""
        # Create
        create_res = login_admin_a.post(
            "/api/opportunities",
            json={
                "name": "Design Role",
                "category": "design",
                "duration": "3 months",
                "start_date": "2024-06-01",
                "description": "Design UIs",
                "skills": "Figma, CSS",
                "future_opportunities": "Internship to FTE",
            },
        )
        opp_id = create_res.get_json()["id"]

        # Get
        res = login_admin_a.get(f"/api/opportunities/{opp_id}")

        assert res.status_code == 200
        data = res.get_json()
        assert data["id"] == opp_id
        assert data["name"] == "Design Role"

    def test_get_nonexistent(self, login_admin_a):
        """Get nonexistent opportunity returns 404."""
        res = login_admin_a.get("/api/opportunities/99999")

        assert res.status_code == 404

    def test_update_opportunity(self, login_admin_a):
        """Update opportunity returns updated object."""
        # Create
        create_res = login_admin_a.post(
            "/api/opportunities",
            json={
                "name": "Marketing Role",
                "category": "marketing",
                "duration": "2 months",
                "start_date": "2024-05-01",
                "description": "Original description",
                "skills": "Social Media",
                "future_opportunities": "Original future",
            },
        )
        opp_id = create_res.get_json()["id"]

        # Update
        update_res = login_admin_a.put(
            f"/api/opportunities/{opp_id}",
            json={
                "description": "Updated description",
                "name": "Updated Marketing Role",
            },
        )

        assert update_res.status_code == 200
        data = update_res.get_json()
        assert data["description"] == "Updated description"
        assert data["name"] == "Updated Marketing Role"
        # Other fields unchanged
        assert data["category"] == "marketing"

    def test_delete_opportunity(self, login_admin_a):
        """Delete opportunity returns 204."""
        # Create
        create_res = login_admin_a.post(
            "/api/opportunities",
            json={
                "name": "Role to Delete",
                "category": "business",
                "duration": "1 month",
                "start_date": "2024-04-01",
                "description": "This will be deleted",
                "skills": "None",
                "future_opportunities": "None",
            },
        )
        opp_id = create_res.get_json()["id"]

        # Delete
        del_res = login_admin_a.delete(f"/api/opportunities/{opp_id}")

        assert del_res.status_code == 204

        # Verify deleted
        get_res = login_admin_a.get(f"/api/opportunities/{opp_id}")
        assert get_res.status_code == 404


class TestOwnershipIsolation:
    """US-2.3: Ensure admins only see their own opportunities."""

    def test_admin_a_cannot_see_admin_b_opportunities(self, app, admin_a, admin_b):
        """Admin A cannot access Admin B's opportunity."""
        with app.app_context():
            # Admin B creates an opportunity
            opp = Opportunity(
                admin_id=admin_b["id"],
                name="Admin B Role",
                category="technology",
                duration="3 months",
                start_date="2024-06-01",
                description="Only B sees this",
                skills="Private",
                future_opportunities="Private",
            )
            db.session.add(opp)
            db.session.commit()
            opp_id = opp.id

        # Login as Admin A
        client = app.test_client()
        client.post(
            "/api/auth/login",
            json={"email": admin_a["email"], "password": admin_a["password"]},
        )

        # Try to access Admin B's opportunity
        res = client.get(f"/api/opportunities/{opp_id}")

        # Should return 404 (not 403, to avoid leaking existence)
        assert res.status_code == 404

    def test_admin_list_only_own(self, app, admin_a, admin_b):
        """Admin A list only shows Admin A's opportunities."""
        with app.app_context():
            # Admin A creates 2 opportunities
            opp_a1 = Opportunity(
                admin_id=admin_a["id"],
                name="A Role 1",
                category="technology",
                duration="3 months",
                start_date="2024-06-01",
                description="A desc",
                skills="A skills",
                future_opportunities="A future",
            )
            opp_a2 = Opportunity(
                admin_id=admin_a["id"],
                name="A Role 2",
                category="business",
                duration="2 months",
                start_date="2024-07-01",
                description="A desc 2",
                skills="A skills 2",
                future_opportunities="A future 2",
            )

            # Admin B creates 1 opportunity
            opp_b1 = Opportunity(
                admin_id=admin_b["id"],
                name="B Role 1",
                category="design",
                duration="1 month",
                start_date="2024-05-01",
                description="B desc",
                skills="B skills",
                future_opportunities="B future",
            )

            db.session.add_all([opp_a1, opp_a2, opp_b1])
            db.session.commit()

        # Login as Admin A
        client = app.test_client()
        client.post(
            "/api/auth/login",
            json={"email": admin_a["email"], "password": admin_a["password"]},
        )

        # List should only show A's opportunities
        res = client.get("/api/opportunities")

        assert res.status_code == 200
        opportunities = res.get_json()
        assert len(opportunities) == 2
        assert all(opp["admin_id"] == admin_a["id"] for opp in opportunities)

        # Verify B's opportunity not in list
        names = [opp["name"] for opp in opportunities]
        assert "B Role 1" not in names
