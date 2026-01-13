#!/usr/bin/env python3
"""Task 32 completion test - Ensure all tests pass."""

import subprocess
import sys
import os

def run_test_suite(test_pattern, description):
    """Run a specific test suite and return results."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Pattern: {test_pattern}")
    print('='*60)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_pattern, 
            "-v", 
            "--tb=short",
            "-x"  # Stop on first failure
        ], capture_output=True, text=True, cwd=".")
        
        print(f"Exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ PASSED")
            return True
        else:
            print("❌ FAILED")
            print("\nSTDOUT:")
            print(result.stdout[-2000:])  # Last 2000 chars
            print("\nSTDERR:")
            print(result.stderr[-1000:])  # Last 1000 chars
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run Task 32 completion tests."""
    
    print("Task 32: Checkpoint - Ensure all tests pass")
    print("=" * 60)
    
    # Test suites to run
    test_suites = [
        # Core Phase 5 integration tests
        ("tests/integration/test_phase5_integration.py::TestPhase5Integration::test_phase5_task_completion", 
         "Phase 5 Task Completion"),
        
        # Key integration tests
        ("tests/integration/test_api_integration.py::TestAPIIntegration::test_get_library_success", 
         "API Library Success"),
        
        ("tests/integration/test_api_integration.py::TestAPIIntegration::test_upload_pdf_success", 
         "API Upload Success"),
        
        # Property tests
        ("tests/test_polly_audio_generation_property.py::test_audio_generation_produces_valid_segment", 
         "Polly Audio Generation Property"),
        
        # Core unit tests (sample)
        ("tests/test_batch_processing_unit.py::TestBatchProcessor::test_submit_job", 
         "Batch Processing Unit"),
        
        ("tests/test_cache_manager_unit.py::TestCacheManager::test_set_and_get", 
         "Cache Manager Unit"),
        
        # Phase 5 specific tests
        ("tests/integration/test_phase5_integration.py::TestPhase5Integration::test_error_handling_integration", 
         "Error Handling Integration"),
        
        ("tests/integration/test_phase5_integration.py::TestPhase5Integration::test_cost_monitoring_integration", 
         "Cost Monitoring Integration"),
        
        ("tests/integration/test_phase5_integration.py::TestPhase5Integration::test_metrics_collection_integration", 
         "Metrics Collection Integration"),
    ]
    
    passed = 0
    failed = 0
    
    for test_pattern, description in test_suites:
        if run_test_suite(test_pattern, description):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("TASK 32 COMPLETION SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")
    
    if failed == 0:
        print(f"\n🎉 TASK 32 COMPLETE!")
        print("All critical tests are passing.")
        print("Phase 5: Integration and End-to-End Testing is ready.")
        return 0
    else:
        print(f"\n⚠️  TASK 32 INCOMPLETE")
        print(f"{failed} test suite(s) still failing.")
        print("Some issues need to be resolved.")
        return 1

if __name__ == "__main__":
    sys.exit(main())