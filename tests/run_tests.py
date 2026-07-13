import unittest
import sys
import os

def run_suite():
    print("==================================================")
    print("      Starting ZeroDay Daily Unit Test Suite      ")
    print("==================================================")
    
    # Ensure project root is in path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        
    loader = unittest.TestLoader()
    # Discover tests inside "tests" folder matching test_unit_*.py
    tests_dir = os.path.join(project_root, "tests")
    suite = loader.discover(start_dir=tests_dir, pattern="test_unit_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n==================================================")
    print("                  Test Summary                    ")
    print("==================================================")
    print(f"Ran: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print("==================================================")
    
    if result.wasSuccessful():
        print("[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("[FAILURE] Some tests failed or encountered errors.")
        sys.exit(1)

if __name__ == "__main__":
    run_suite()
