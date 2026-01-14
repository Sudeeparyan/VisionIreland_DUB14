"""End-to-end test for the comic audio narrator pipeline."""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_pipeline():
    """Test the complete pipeline end-to-end."""
    print("=" * 60)
    print("Comic Audio Narrator - End-to-End Pipeline Test")
    print("=" * 60)
    
    # Test 1: Check imports
    print("\n[1/7] Testing imports...")
    try:
        from src.config import settings
        from src.pdf_processing import PDFExtractor
        from src.bedrock_analysis import BedrockPanelAnalyzer, ContextManager
        from src.polly_generation import PollyAudioGenerator, VoiceProfileManager
        from src.storage import LibraryManager, LocalStorageManager, S3StorageManager
        from src.processing.pipeline_orchestrator import PipelineOrchestrator
        print("  ✓ All imports successful")
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False
    
    # Test 2: Check AWS configuration
    print("\n[2/7] Checking AWS configuration...")
    print(f"  AWS Region: {settings.aws_region}")
    print(f"  S3 Bucket: {settings.s3_bucket_name}")
    print(f"  Polly Engine: {settings.polly_engine}")
    
    has_credentials = bool(settings.aws_access_key_id and settings.aws_secret_access_key)
    if has_credentials:
        print("  ✓ AWS credentials configured (from env)")
    else:
        print("  ⚠ No explicit AWS credentials - will use default credential chain")
    
    # Test 3: Check PDF extraction (PyMuPDF)
    print("\n[3/7] Testing PDF extraction setup...")
    try:
        import fitz  # PyMuPDF
        print(f"  ✓ PyMuPDF is installed (version {fitz.version[0]})")
    except ImportError:
        print("  ✗ PyMuPDF not installed - run: pip install PyMuPDF")
        return False
    
    # Test 4: Test AWS Bedrock connection
    print("\n[4/7] Testing AWS Bedrock connection...")
    try:
        from src.aws_clients import aws_clients
        
        # Try a simple inference test directly with bedrock-runtime
        # Use the cross-region inference profile format
        test_response = aws_clients.bedrock.converse(
            modelId="us.amazon.nova-lite-v1:0",
            messages=[{"role": "user", "content": [{"text": "Say hello in one word"}]}],
            inferenceConfig={"maxTokens": 10}
        )
        response_text = test_response.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
        print(f"  ✓ Bedrock inference working (response: {response_text[:50]})")
    except Exception as e:
        error_str = str(e)
        if 'security token' in error_str.lower() or 'expired' in error_str.lower() or 'invalid' in error_str.lower():
            print(f"  ✗ AWS credentials expired or invalid")
            print("    Please refresh your AWS credentials in .env file")
            print("    If using temporary credentials, get new ones from AWS console")
            return False
        elif 'AccessDeniedException' in error_str:
            print(f"  ✗ Access denied to Bedrock model")
            print("    Check that your IAM role has bedrock:InvokeModel permission")
            return False
        else:
            print(f"  ✗ Bedrock connection failed: {e}")
            print("    Check your AWS credentials and region")
            return False
    
    # Test 5: Test AWS Polly connection
    print("\n[5/7] Testing AWS Polly connection...")
    try:
        response = aws_clients.polly.describe_voices(Engine='neural')
        voice_count = len(response.get('Voices', []))
        print(f"  ✓ Polly connection successful ({voice_count} neural voices available)")
    except Exception as e:
        print(f"  ✗ Polly connection failed: {e}")
        return False
    
    # Test 6: Test S3 connection
    print("\n[6/7] Testing AWS S3 connection...")
    try:
        response = aws_clients.s3.head_bucket(Bucket=settings.s3_bucket_name)
        print(f"  ✓ S3 bucket '{settings.s3_bucket_name}' accessible")
    except Exception as e:
        error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', '')
        if error_code == '404':
            print(f"  ⚠ S3 bucket '{settings.s3_bucket_name}' does not exist")
            print("    Will fall back to local storage")
        elif error_code == '403':
            print(f"  ⚠ S3 bucket '{settings.s3_bucket_name}' access denied")
            print("    Will fall back to local storage")
        else:
            print(f"  ⚠ S3 connection issue: {e}")
            print("    Will fall back to local storage")
    
    # Test 7: Initialize pipeline orchestrator
    print("\n[7/7] Testing pipeline orchestrator initialization...")
    try:
        # Create storage managers
        local_manager = LocalStorageManager(storage_path=settings.local_storage_path)
        
        try:
            s3_manager = S3StorageManager(
                bucket_name=settings.s3_bucket_name,
                region=settings.aws_region
            )
        except Exception:
            s3_manager = None
            print("  ⚠ S3 manager initialization failed, using local storage only")
        
        library_manager = LibraryManager(
            local_manager=local_manager,
            s3_manager=s3_manager
        )
        
        pipeline = PipelineOrchestrator(
            library_manager=library_manager,
            use_neural_voices=settings.polly_engine == "neural",
            enable_caching=True,
            batch_size=10
        )
        print("  ✓ Pipeline orchestrator initialized successfully")
    except Exception as e:
        print(f"  ✗ Pipeline initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("All tests passed! Pipeline is ready for use.")
    print("=" * 60)
    
    print("\nTo process a PDF, start the backend server:")
    print("  cd Kiro_gen/backend")
    print("  python run.py")
    print("\nThen upload a PDF via the API:")
    print("  POST http://localhost:8000/api/upload")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_pipeline())
    sys.exit(0 if success else 1)
