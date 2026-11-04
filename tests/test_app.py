import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import check_password_hash

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

import app2 as app_module  # noqa: E402


class EmployeeManagementTests(unittest.TestCase):
    def setUp(self):
        app_module.app2.config.update(TESTING=True, CSRF_ENABLED=False, SECRET_KEY="test-secret")
        self.client = app_module.app2.test_client()

    def login_session(self, role="employee", user_id=101):
        with self.client.session_transaction() as session:
            session.update(user_id=user_id, username="test-user", role=role)

    def test_protected_dashboard_requires_login(self):
        response = self.client.get("/sepm")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_employee_cannot_access_administration(self):
        self.login_session(role="employee")
        response = self.client.get("/official")
        self.assertEqual(response.status_code, 403)

    @patch.object(app_module, "execute_db")
    def test_legacy_password_is_upgraded_after_login(self, execute_db):
        execute_db.side_effect = [
            [{"user_id": 101, "username": "ASD", "password_hash": "ds_password"}],
            1,
        ]
        response = self.client.post(
            "/login",
            data={"e_id": "101", "username": "ASD", "password": "ds_password", "role": "employee"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/sepm", response.headers["Location"])
        update_args = execute_db.call_args_list[1].args[1]
        self.assertNotEqual(update_args[0], "ds_password")
        self.assertTrue(check_password_hash(update_args[0], "ds_password"))
        with self.client.session_transaction() as session:
            self.assertEqual(session["user_id"], 101)
            self.assertEqual(session["role"], "employee")

    @patch.object(app_module, "execute_db", return_value=[])
    def test_login_does_not_create_shared_global_identity(self, execute_db):
        self.login_session(role="employee", user_id=101)
        with self.client.session_transaction() as session:
            self.assertEqual(session["user_id"], 101)
        self.assertFalse(hasattr(app_module, "e_id"))

    @patch.object(app_module, "execute_db", return_value=[])
    def test_credentials_page_does_not_read_password(self, execute_db):
        self.login_session(role="employee")
        response = self.client.get("/login_cred")
        self.assertEqual(response.status_code, 200)
        query = execute_db.call_args.args[0]
        self.assertNotIn("emp_password", query)
        self.assertNotIn("SELECT *", query)

    def test_logout_clears_session(self):
        self.login_session(role="admin", user_id=1)
        response = self.client.post("/logout")
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)

    def test_post_without_csrf_token_is_rejected(self):
        app_module.app2.config["CSRF_ENABLED"] = True
        response = self.client.post("/login", data={})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
