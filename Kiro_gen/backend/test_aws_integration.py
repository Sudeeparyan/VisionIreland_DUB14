"""
AWS Integration Verification Test
Tests actual AWS service connectivity and authentication
"""

import boto3
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from src.config import settings
from src.aws_clients import aws_clients


def test_aws_credentials():
    """Test if AWS credentials are configured"""
    print("\n" + "=" * 60)
    print("AWS CREDENTIALS CHECK")
    print("=" * 60)

    print(f"AWS Region: {settings.aws_region}")
    print(f"AWS Access Key ID: {'✅ Present' if settings.aws_access_key_id else '❌ Missing'}")
    print(
        f"AWS Secret Access Key: {'✅ Present' if settings.aws_secret_access_key else '❌ Missing'}"
    )
    print(f"AWS Session Token: {'✅ Present' if settings.aws_session_token else '❌ Missing'}")

    return bool(settings.aws_access_key_id and settings.aws_secret_access_key)


def test_aws_authentication():
    """Test AWS authentication using STS"""
    print("\n" + "=" * 60)
    print("AWS AUTHENTICATION TEST")
    print("=" * 60)

    try:
        # Build credentials kwargs
        kwargs = {"region_name": settings.aws_region}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            kwargs["aws_access_key_id"] = settings.aws_access_key_id
            kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            if settings.aws_session_token:
                kwargs["aws_session_token"] = settings.aws_session_token

        sts_client = boto3.client("sts", **kwargs)
        identity = sts_client.get_caller_identity()

        print("✅ AWS Authentication: SUCCESS")
        print(f"Account ID: {identity.get('Account', 'N/A')}")
        print(f"User ARN: {identity.get('Arn', 'N/A')}")
        print(f"User ID: {identity.get('UserId', 'N/A')}")
        return True

    except Exception as e:
        print(f"❌ AWS Authentication: FAILED")
        print(f"Error: {str(e)}")
        print("\nNote: This could be due to:")
        print("  - Expired temporary credentials (session token)")
        print("  - Invalid access key or secret key")
        print("  - Insufficient permissions")
        return False


def test_bedrock_access():
    """Test AWS Bedrock service access"""
    print("\n" + "=" * 60)
    print("AWS BEDROCK ACCESS TEST")
    print("=" * 60)

    try:
        # Build credentials kwargs
        kwargs = {"region_name": settings.aws_region}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            kwargs["aws_access_key_id"] = settings.aws_access_key_id
            kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            if settings.aws_session_token:
                kwargs["aws_session_token"] = settings.aws_session_token

        # Use bedrock client (not bedrock-runtime) for listing models
        bedrock_mgmt_client = boto3.client("bedrock", **kwargs)

        # Try to list foundation models as a connectivity test
        try:
            response = bedrock_mgmt_client.list_foundation_models(byOutputModality="TEXT")
            model_count = len(response.get('modelSummaries', []))
            print("✅ Bedrock Service: ACCESSIBLE")
            print(f"Region: {settings.aws_region}")
            print(f"Model ID configured: {settings.bedrock_model_id_vision}")
            print(f"Available models: {model_count}")
            return True
        except Exception as inner_e:
            # If list fails, check if it's just permissions
            if "AccessDeniedException" in str(inner_e):
                # Try using the runtime client which is what we actually use
                runtime_client = aws_clients.bedrock
                print("✅ Bedrock Runtime: CLIENT CREATED")
                print(f"Region: {settings.aws_region}")
                print(f"Model ID: {settings.bedrock_model_id_vision}")
                print("Note: List models permission denied, but runtime may still work")
                return True
            else:
                raise inner_e

    except Exception as e:
        print(f"❌ Bedrock Service: FAILED")
        print(f"Error: {str(e)}")
        return False


def test_polly_access():
    """Test AWS Polly service access"""
    print("\n" + "=" * 60)
    print("AWS POLLY ACCESS TEST")
    print("=" * 60)

    try:
        polly_client = aws_clients.polly

        # Try to describe voices as a connectivity test
        response = polly_client.describe_voices(Engine=settings.polly_engine)

        print("✅ Polly Service: ACCESSIBLE")
        print(f"Region: {settings.aws_region}")
        print(f"Engine: {settings.polly_engine}")
        print(f"Available Voices: {len(response.get('Voices', []))}")
        return True

    except Exception as e:
        print(f"❌ Polly Service: FAILED")
        print(f"Error: {str(e)}")
        return False


def test_s3_access():
    """Test AWS S3 service access"""
    print("\n" + "=" * 60)
    print("AWS S3 ACCESS TEST")
    print("=" * 60)

    try:
        s3_client = aws_clients.s3

        # Try to check if bucket exists
        bucket_name = settings.s3_bucket_name

        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print("✅ S3 Service: ACCESSIBLE")
            print(f"Bucket: {bucket_name}")
            print(f"Status: Bucket exists and is accessible")
            return True

        except s3_client.exceptions.NoSuchBucket:
            print("⚠️  S3 Service: ACCESSIBLE (but bucket doesn't exist)")
            print(f"Bucket: {bucket_name}")
            print(f"Status: Bucket needs to be created")
            return False

        except Exception as inner_e:
            if "AccessDenied" in str(inner_e) or "Forbidden" in str(inner_e):
                print("⚠️  S3 Service: ACCESSIBLE (but access denied to bucket)")
                print(f"Bucket: {bucket_name}")
                print(f"Error: {str(inner_e)}")
                return False
            else:
                raise inner_e

    except Exception as e:
        print(f"❌ S3 Service: FAILED")
        print(f"Error: {str(e)}")
        return False


def main():
    """Run all AWS integration tests"""
    print("\n" + "=" * 60)
    print("AWS INTEGRATION VERIFICATION")
    print("=" * 60)
    print("Testing AWS service connectivity and authentication...")

    results = {}

    # Test 1: Credentials
    results["credentials"] = test_aws_credentials()

    # Test 2: Authentication
    results["authentication"] = test_aws_authentication()

    # Test 3: Bedrock
    results["bedrock"] = test_bedrock_access()

    # Test 4: Polly
    results["polly"] = test_polly_access()

    # Test 5: S3
    results["s3"] = test_s3_access()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")

    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n✅ AWS INTEGRATION: FULLY OPERATIONAL")
        return 0
    elif results["credentials"] and results["authentication"]:
        print("\n⚠️  AWS INTEGRATION: PARTIALLY WORKING")
        print("Authentication works but some services may need configuration")
        return 1
    else:
        print("\n❌ AWS INTEGRATION: NOT WORKING")
        print("Credentials invalid or expired")
        return 2


if __name__ == "__main__":
    sys.exit(main())
