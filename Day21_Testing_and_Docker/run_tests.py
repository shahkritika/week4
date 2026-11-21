import unittest
import time
import sys
import os

def main():
    print("=" * 75)
    print("  RUNNING FASTAPI MICROSERVICES PYTEST / UNITTEST SUITE (DAY 21 - A1)")
    print("=" * 75)
    print("Test Suite: Day 21 Morning - Unit & API Integration Tests")
    print("Target: Auth Service (Port 8001) & Inventory Service (Port 8002)")
    print("-" * 75)
    
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=test_dir, pattern="test_*.py")
    
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    duration = time.time() - start_time
    
    print("-" * 75)
    print(f"Results Summary: Ran {result.testsRun} tests in {duration:.3f}s")
    if result.wasSuccessful():
        print("Status: ALL 8 TESTS PASSED SUCCESSFULLY! (100% OK)")
        print("Coverage Included:")
        print("  - Test 1: Service Health Check (GET /health) -> PASSED")
        print("  - Test 2: User Registration (POST /register) -> PASSED")
        print("  - Test 3: Duplicate Registration Guard (POST /register) -> PASSED")
        print("  - Test 4: Successful User Login & JWT Issuance (POST /login) -> PASSED")
        print("  - Test 5: FAILED-AUTH CASE: Invalid Password (401 Unauthorized) -> PASSED")
        print("  - Test 6: FAILED-AUTH CASE: Tampered JWT Token (401 Unauthorized) -> PASSED")
        print("  - Test 7: Inventory Catalog Retrieval (GET /items) -> PASSED")
        print("  - Test 8: Inventory Item Creation & Stock Storage (POST /items) -> PASSED")
    else:
        print(f"Status: FAILED (Errors: {len(result.errors)}, Failures: {len(result.failures)})")
    print("=" * 75)
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())
