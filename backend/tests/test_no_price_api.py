"""Smoke tests for the local database-only pricing backend."""
import unittest
from unittest.mock import patch
from fastapi import HTTPException

from backend.price_auth import require_admin, hash_password, verify_password, create_token
from backend.price_routes import read_component_price


class FakeCursor:
    def execute(self, statement, params):
        self.statement = statement
        self.params = params
    def fetchone(self):
        return {
            "component_id": 129,
            "manufacturer": "EVGA",
            "model": "GeForce GTX 1080 Ti",
            "price": 260,
            "specifications": '{"price_metadata": {"type": "synthetic_estimate"}}',
        }
    def close(self):
        pass


class FakeConnection:
    def cursor(self, **kwargs):
        return FakeCursor()
    def close(self):
        pass


class CleanupTests(unittest.TestCase):
    def test_password_hashing(self):
        hashed = hash_password("long-test-password")
        self.assertNotEqual(hashed, "long-test-password")
        self.assertTrue(verify_password("long-test-password", hashed))
        self.assertFalse(verify_password("wrong-password", hashed))

    def test_admin_dependency(self):
        self.assertEqual(require_admin({"role": "admin"})["role"], "admin")
        with self.assertRaises(HTTPException) as err:
            require_admin({"role": "user"})
        self.assertEqual(err.exception.status_code, 403)

    @patch("backend.price_routes.get_db_connection", return_value=FakeConnection())
    def test_reads_estimated_price_without_ai(self, _db):
        response = read_component_price(129)
        self.assertEqual(response["price_aud"], 260)
        self.assertEqual(response["price_type"], "synthetic_estimate")

    def test_routes_have_no_live_price_check(self):
        from backend.main import app

        paths = app.openapi()["paths"]

        # Required endpoints must exist
        self.assertIn("/components/{component_id}/price", paths)
        self.assertIn("/auth/register", paths)
        self.assertIn("/auth/login", paths)
        self.assertIn("/auth/me", paths)

        # Removed AI functionality must not exist
        self.assertNotIn("/components/{component_id}/price-check", paths)
        self.assertFalse(any("/tier" in path for path in paths))


if __name__ == "__main__":
    unittest.main()
