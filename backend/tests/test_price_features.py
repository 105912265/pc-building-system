import unittest
from decimal import Decimal
from unittest.mock import patch

from backend.price_auth import hash_password, verify_password, require_admin
from fastapi import HTTPException
from backend.price_web_search import PriceLookupError, validate_offer, product_match


class PasswordTests(unittest.TestCase):
    def test_scrypt_password_verification(self):
        hashed = hash_password("long-test-password!123")
        self.assertTrue(verify_password("long-test-password!123", hashed))
        self.assertFalse(verify_password("wrong password", hashed))
        self.assertNotIn("long-test-password!123", hashed)


class RolesTests(unittest.TestCase):
    def test_non_admin_cannot_change_tier(self):
        with self.assertRaises(HTTPException) as cm:
            require_admin({"role": "user"})
        self.assertEqual(cm.exception.status_code, 403)


class PriceValidationTests(unittest.TestCase):
    def setUp(self):
        self.url = "https://shop.example.com/product/5070"
        self.offer = {"found": True, "price_aud": 999.50, "currency": "AUD", "product_title": "MSI RTX 5070 12GB graphics card", "seller": "Example Retailer", "condition": "new", "source_url": self.url, "reason": "Current listing"}

    def test_accepts_matching_cited_price(self):
        result = validate_offer(self.offer, {self.url}, "GPU", "RTX 5070")
        self.assertEqual(result.price, Decimal("999.50"))

    def test_rejects_uncited_price(self):
        with self.assertRaises(PriceLookupError):
            validate_offer(self.offer, set(), "GPU", "RTX 5070")

    def test_rejects_wrong_currency(self):
        offer = dict(self.offer, currency="USD")
        with self.assertRaises(PriceLookupError):
            validate_offer(offer, {self.url}, "GPU", "RTX 5070")

    def test_rejects_laptop(self):
        offer = dict(self.offer, product_title="Gaming laptop RTX 5070")
        with self.assertRaises(PriceLookupError):
            validate_offer(offer, {self.url}, "GPU", "RTX 5070")

    def test_rejects_variant(self):
        self.assertFalse(product_match("GPU", "RTX 5070 Ti", "RTX 5070"))

    def test_rejects_unreasonable_price(self):
        offer = dict(self.offer, price_aud=0)
        with self.assertRaises(PriceLookupError):
            validate_offer(offer, {self.url}, "GPU", "RTX 5070")


if __name__ == "__main__":
    unittest.main()
