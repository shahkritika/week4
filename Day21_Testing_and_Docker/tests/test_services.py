import os
import sys
import unittest
from fastapi import HTTPException

# Ensure services can be imported
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, base_dir)

os.environ["AUTH_DB_PATH"] = "test_auth.db"
os.environ["INVENTORY_DB_PATH"] = "test_inventory.db"

from Day19_Microservices_Architecture.services.auth_service import main as auth_svc
from Day19_Microservices_Architecture.services.auth_service import database as auth_db
from Day19_Microservices_Architecture.services.inventory_service import main as inv_svc
from Day19_Microservices_Architecture.services.inventory_service import database as inv_db
from Day19_Microservices_Architecture.services.auth_service.schemas import UserRegister, UserLogin
from Day19_Microservices_Architecture.services.inventory_service.schemas import ItemCreate, StockUpdate

class TestMicroservicesSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize isolated test databases
        for db in ["test_auth.db", "test_inventory.db"]:
            if os.path.exists(db):
                try:
                    os.remove(db)
                except Exception:
                    pass
        auth_db.init_db()
        inv_db.init_db()
        cls.saved_token = None

    @classmethod
    def tearDownClass(cls):
        for db in ["test_auth.db", "test_inventory.db"]:
            if os.path.exists(db):
                try:
                    os.remove(db)
                except Exception:
                    pass

    # TEST 1: Service Health Check
    def test_01_auth_service_health(self):
        """Test 1: Health probe returns status 'healthy'"""
        res = auth_svc.health_check()
        self.assertEqual(res["status"], "healthy")
        self.assertEqual(res["service"], "auth_service")

    # TEST 2: User Registration Success
    def test_02_user_registration_success(self):
        """Test 2: Successful user registration creates record in auth database"""
        user_in = UserRegister(
            username="intern_developer",
            email="intern@company.com",
            password="StrongPassword123!",
            role="developer"
        )
        res = auth_svc.register(user_in)
        self.assertEqual(res["username"], "intern_developer")
        self.assertEqual(res["email"], "intern@company.com")
        self.assertIn("id", res)

    # TEST 3: Duplicate Registration Conflict Guard
    def test_03_duplicate_registration_fails(self):
        """Test 3: Duplicate username or email raises 400 Bad Request"""
        user_in = UserRegister(
            username="intern_developer",
            email="another_email@company.com",
            password="Password456!"
        )
        with self.assertRaises(HTTPException) as ctx:
            auth_svc.register(user_in)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("already registered", ctx.exception.detail)

    # TEST 4: Successful Login and JWT Generation
    def test_04_user_login_success(self):
        """Test 4: Valid credentials return JWT access token with bearer type"""
        creds = UserLogin(username="intern_developer", password="StrongPassword123!")
        res = auth_svc.login(creds)
        self.assertIn("access_token", res)
        self.assertEqual(res["token_type"], "bearer")
        self.assertEqual(res["username"], "intern_developer")
        TestMicroservicesSuite.saved_token = res["access_token"]

    # TEST 5: FAILED-AUTH CASE (Wrong password)
    def test_05_failed_auth_invalid_password(self):
        """Test 5 (CRITICAL REQUIREMENT): Invalid password returns 401 Unauthorized"""
        creds = UserLogin(username="intern_developer", password="INCORRECT_PASSWORD_999")
        with self.assertRaises(HTTPException) as ctx:
            auth_svc.login(creds)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "Invalid username or password")

    # TEST 6: FAILED-AUTH CASE (Tampered JWT Token)
    def test_06_failed_auth_tampered_token(self):
        """Test 6: Tampered / malformed token returns 401 Unauthorized"""
        tampered_header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.INVALID_SIGNATURE"
        with self.assertRaises(HTTPException) as ctx:
            auth_svc.verify_token(authorization=tampered_header)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "Invalid or expired token")

    # TEST 7: Inventory Catalog Retrieval
    def test_07_inventory_get_items(self):
        """Test 7: Inventory listing retrieves active items from inventory.db"""
        items = inv_svc.get_items()
        self.assertIsInstance(items, list)
        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(items[0]["sku"], "SKU-LAPTOP-01")

    # TEST 8: Protected Item Creation & Stock Mutation
    def test_08_inventory_create_item_and_stock(self):
        """Test 8: Item creation adds record with valid SKU and stock quantity"""
        new_item = ItemCreate(
            sku="SKU-MICROSERVICE-HUB",
            name="Microservice Edge Gateway",
            description="High throughput API router hardware",
            price=899.00,
            stock_quantity=25,
            category="Infrastructure"
        )
        res = inv_svc.create_item(new_item)
        self.assertEqual(res["sku"], "SKU-MICROSERVICE-HUB")
        self.assertEqual(res["stock_quantity"], 25)

        # Test stock adjustment
        stock_delta = StockUpdate(delta=5)
        updated = inv_svc.update_stock(res["id"], stock_delta)
        self.assertEqual(updated["stock_quantity"], 30)

if __name__ == "__main__":
    unittest.main()
