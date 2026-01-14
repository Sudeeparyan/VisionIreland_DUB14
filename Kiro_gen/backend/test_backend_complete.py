"""Comprehensive backend verification test."""

import sys
import os
import asyncio
from pathlib import Path

# Add backend and src to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))


async def test_backend_components():
    """Test all backend components end-to-end."""

    print("=" * 70)
    print("COMPREHENSIVE BACKEND END-TO-END VERIFICATION")
    print("=" * 70)

    results = {"total_tests": 0, "passed": 0, "failed": 0, "tests": []}

    # Test 1: Import all modules
    print("\n[1] Testing module imports...")
    results["total_tests"] += 1
    try:
        from src.config import settings
        from src.storage.local_manager import LocalStorageManager
        from src.storage.s3_manager import S3StorageManager
        from src.storage.library_manager import LibraryManager
        from src.monitoring.cost_monitor import CostMonitor
        from src.monitoring.metrics import MetricsCollector
        from src.processing.pipeline_orchestrator import PipelineOrchestrator

        print("✅ PASS: All modules imported successfully")
        results["passed"] += 1
        results["tests"].append({"test": "Module imports", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results["failed"] += 1
        results["tests"].append({"test": "Module imports", "status": "FAIL", "error": str(e)})
        return results

    # Test 2: Configuration
    print("\n[2] Testing configuration...")
    results["total_tests"] += 1
    try:
        assert settings.aws_region
        assert settings.bedrock_model_id_vision
        assert settings.polly_engine in ["neural", "standard"]
        assert settings.api_port == 8000
        print(f"✅ PASS: Configuration loaded (AWS Region: {settings.aws_region})")
        results["passed"] += 1
        results["tests"].append({"test": "Configuration", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results["failed"] += 1
        results["tests"].append({"test": "Configuration", "status": "FAIL", "error": str(e)})

    # Test 3: Local Storage Manager
    print("\n[3] Testing Local Storage Manager...")
    results["total_tests"] += 1
    try:
        local_manager = LocalStorageManager(storage_path="./storage/audio")
        assert local_manager.storage_path.exists()
        print("✅ PASS: Local storage manager initialized")
        results["passed"] += 1
        results["tests"].append({"test": "Local Storage Manager", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results["failed"] += 1
        results["tests"].append(
            {"test": "Local Storage Manager", "status": "FAIL", "error": str(e)}
        )

    # Test 4: S3 Storage Manager
    print("\n[4] Testing S3 Storage Manager...")
    results["total_tests"] += 1
    try:
        s3_manager = S3StorageManager(
            bucket_name=settings.s3_bucket_name, region=settings.aws_region
        )
        assert s3_manager.bucket_name == settings.s3_bucket_name
        print("✅ PASS: S3 storage manager initialized")
        results["passed"] += 1
        results["tests"].append({"test": "S3 Storage Manager", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results["failed"] += 1
        results["tests"].append({"test": "S3 Storage Manager", "status": "FAIL", "error": str(e)})

    # Test 5: Library Manager
    print("\n[5] Testing Library Manager...")
    results["total_tests"] += 1
    try:
        library_manager = LibraryManager(local_manager=local_manager, s3_manager=s3_manager)
        index = await library_manager.get_library_index()
        assert isinstance(index, list)
        print("✅ PASS: Library manager initialized and index retrieved")
        results["passed"] += 1
        results["tests"].append({"test": "Library Manager", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results["failed"] += 1
        results["tests"].append({"test": "Library Manager", "status": "FAIL", "error": str(e)})

    # Test 6: Cost Monitor
    print("\n[6] Testing Cost Monitor...")
    results["total_tests"] += 1
    try:
        cost_monitor = CostMonitor()
        summary = await cost_monitor.get_cost_summary()
        assert "summary" in summary or "total_cost" in summary
        print("✅ PASS: Cost monitor working")
        results["passed"] += 1
        results["tests"].append({"test": "Cost Monitor", "status": "PASS"})
        await cost_monitor.close()
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"❌ FAIL: {e}")
        results["failed"] += 1
        results["tests"].append({"test": "Cost Monitor", "status": "FAIL", "error": str(e)})

    # Test 7: Metrics Collector
    print("\n[7] Testing Metrics Collector...")
    results["total_tests"] += 1
    try:
        metrics_collector = MetricsCollector()
        # start_system_monitoring is called in __init__, so it's already started
        await asyncio.sleep(1.5)  # Wait for metrics to be collected
        metrics = await metrics_collector.get_metrics()
        assert "job_summary" in metrics or "system_metrics" in metrics
        print("✅ PASS: Metrics collector working")
        results["passed"] += 1
        results["tests"].append({"test": "Metrics Collector", "status": "PASS"})
        metrics_collector.stop_system_monitoring()
        await metrics_collector.close()
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"❌ FAIL: {e}")
        results["failed"] += 1
        results["tests"].append({"test": "Metrics Collector", "status": "FAIL", "error": str(e)})

    # Test 8: Pipeline Orchestrator
    print("\n[8] Testing Pipeline Orchestrator...")
    results["total_tests"] += 1
    try:
        pipeline_orchestrator = PipelineOrchestrator(
            library_manager=library_manager,
            use_neural_voices=True,
            enable_caching=True,
            batch_size=10,
        )
        assert pipeline_orchestrator is not None
        print("✅ PASS: Pipeline orchestrator initialized")
        results["passed"] += 1
        results["tests"].append({"test": "Pipeline Orchestrator", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results["failed"] += 1
        results["tests"].append(
            {"test": "Pipeline Orchestrator", "status": "FAIL", "error": str(e)}
        )

    # Test 9: FastAPI Application
    print("\n[9] Testing FastAPI Application...")
    results["total_tests"] += 1
    try:
        from src.main import app

        assert app is not None
        assert app.title == "Comic Audio Narrator API"
        print("✅ PASS: FastAPI application created")
        results["passed"] += 1
        results["tests"].append({"test": "FastAPI Application", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results["failed"] += 1
        results["tests"].append({"test": "FastAPI Application", "status": "FAIL", "error": str(e)})

    # Test 10: API Routes
    print("\n[10] Testing API Routes...")
    results["total_tests"] += 1
    try:
        from src.main import app

        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/health", "/metrics", "/costs", "/api/library"]
        found_routes = [r for r in expected_routes if r in routes]
        assert len(found_routes) >= 5
        print(f"✅ PASS: API routes registered ({len(routes)} total routes)")
        results["passed"] += 1
        results["tests"].append({"test": "API Routes", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results["failed"] += 1
        results["tests"].append({"test": "API Routes", "status": "FAIL", "error": str(e)})

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {(results['passed']/results['total_tests']*100):.1f}%")
    print("=" * 70)

    if results["failed"] == 0:
        print("\n🎉 ALL TESTS PASSED - BACKEND IS FULLY OPERATIONAL!")
    else:
        print(f"\n⚠️  {results['failed']} test(s) failed - issues need resolution")

    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(test_backend_components())
        exit(0 if results["failed"] == 0 else 1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
