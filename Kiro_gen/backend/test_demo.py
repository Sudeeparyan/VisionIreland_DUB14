"""End-to-end demo test for Comic Audio Narrator."""

import asyncio
import httpx
import time
import sys
from pathlib import Path


async def test_demo():
    """Run end-to-end demo test."""
    
    base_url = "http://localhost:8000"
    pdf_path = Path("d:/AI/VisionIreland_DUB14_clean/pdf/test-1.pdf")
    
    print("=" * 60)
    print("Comic Audio Narrator - End-to-End Demo")
    print("=" * 60)
    
    # Verify PDF exists
    if not pdf_path.exists():
        print(f"ERROR: PDF file not found at {pdf_path}")
        return False
    
    print(f"\n✅ PDF file found: {pdf_path}")
    print(f"   Size: {pdf_path.stat().st_size / 1024:.2f} KB")
    
    async with httpx.AsyncClient(timeout=300) as client:
        
        # Step 1: Check backend health
        print("\n1️⃣ Checking backend health...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print(f"   ✅ Backend is healthy: {response.json()}")
            else:
                print(f"   ❌ Backend unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Cannot connect to backend: {e}")
            return False
        
        # Step 2: Upload PDF
        print("\n2️⃣ Uploading PDF to backend...")
        try:
            with open(pdf_path, "rb") as f:
                files = {"file": ("test-1.pdf", f, "application/pdf")}
                response = await client.post(f"{base_url}/api/upload", files=files)
            
            if response.status_code == 200:
                upload_result = response.json()
                job_id = upload_result["job_id"]
                print(f"   ✅ Upload successful!")
                print(f"   Job ID: {job_id}")
                print(f"   File: {upload_result['filename']}")
                print(f"   Size: {upload_result['file_size']} bytes")
            else:
                print(f"   ❌ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Upload error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 3: Poll for job completion
        print("\n3️⃣ Processing comic (Frontend → Backend → AWS → Backend)...")
        max_wait = 300  # 5 minutes max
        poll_interval = 3
        elapsed = 0
        
        while elapsed < max_wait:
            try:
                response = await client.get(f"{base_url}/api/jobs/{job_id}")
                
                if response.status_code == 200:
                    job_status = response.json()
                    status = job_status.get("status", "unknown")
                    progress = job_status.get("progress", 0)
                    
                    print(f"   📊 Status: {status} | Progress: {progress}%", end="\r")
                    
                    if status == "completed":
                        print(f"\n   ✅ Processing completed!")
                        print(f"   Result: {job_status}")
                        break
                    elif status == "failed":
                        error = job_status.get("error", "Unknown error")
                        print(f"\n   ❌ Processing failed: {error}")
                        return False
                    elif status in ["processing", "pending", "queued"]:
                        pass  # Continue polling
                    else:
                        print(f"\n   ⚠️ Unknown status: {status}")
                        
                elif response.status_code == 404:
                    print(f"   ⏳ Job not found yet, waiting...")
                else:
                    print(f"\n   ⚠️ Unexpected response: {response.status_code}")
                    print(f"   {response.text}")
                    
            except Exception as e:
                print(f"\n   ⚠️ Poll error: {e}")
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        if elapsed >= max_wait:
            print(f"\n   ⏰ Timeout waiting for job completion")
            return False
        
        # Step 4: Get audio output
        print("\n4️⃣ Retrieving audio output...")
        try:
            # Try to get audio from library
            response = await client.get(f"{base_url}/api/library")
            if response.status_code == 200:
                library = response.json()
                print(f"   📚 Library entries: {library}")
                
                # Get the audio for our comic
                if library.get("comics"):
                    comic = library["comics"][0] if isinstance(library["comics"], list) else None
                    if comic:
                        audio_id = comic.get("audio_id")
                        if audio_id:
                            audio_response = await client.get(f"{base_url}/api/audio/{audio_id}")
                            if audio_response.status_code == 200:
                                print(f"   ✅ Audio retrieved successfully!")
                                print(f"   Audio size: {len(audio_response.content)} bytes")
                            else:
                                print(f"   ⚠️ Could not retrieve audio: {audio_response.status_code}")
            else:
                print(f"   ⚠️ Could not get library: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Error getting audio: {e}")
        
        print("\n" + "=" * 60)
        print("Demo completed!")
        print("=" * 60)
        
        return True


if __name__ == "__main__":
    result = asyncio.run(test_demo())
    sys.exit(0 if result else 1)
