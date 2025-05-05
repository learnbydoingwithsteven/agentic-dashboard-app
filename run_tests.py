import os
import sys
import unittest
import subprocess

def run_backend_tests():
    """Run all backend tests"""
    print("Running backend tests...")
    
    # Create the tests directory if it doesn't exist
    os.makedirs('backend/tests', exist_ok=True)
    
    # Create an __init__.py file in the tests directory if it doesn't exist
    init_file = os.path.join('backend', 'tests', '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# This file is required to make Python treat the directory as a package')
    
    # Discover and run all tests in the backend/tests directory
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('backend/tests')
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return result.wasSuccessful()

def run_frontend_tests():
    """Run all frontend tests using Jest"""
    print("Running frontend tests...")
    
    # Change to the frontend directory
    os.chdir('frontend')
    
    try:
        # Run the tests using pnpm
        result = subprocess.run(['pnpm', 'test'], capture_output=True, text=True)
        
        # Print the output
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        # Change back to the root directory
        os.chdir('..')
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running frontend tests: {e}")
        
        # Change back to the root directory
        os.chdir('..')
        
        return False

def run_all_tests():
    """Run all tests and return True if all passed"""
    backend_success = run_backend_tests()
    frontend_success = run_frontend_tests()
    
    return backend_success and frontend_success

if __name__ == '__main__':
    success = run_all_tests()
    
    if success:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)
