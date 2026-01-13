"""Test WebSocket connection to verify audio streaming works"""

import asyncio
import json
import websockets
import base64


async def test_websocket():
    uri = "ws://localhost:8000/ws/test123?is_audio=true"

    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connected!")

            # Send a simple text message
            message = {
                "mime_type": "text/plain",
                "data": "Hello, please say hi",
                "role": "user",
            }

            print(f"Sending message: {message['data']}")
            await websocket.send(json.dumps(message))

            # Wait for responses
            print("Waiting for responses...")

            received_audio = False
            received_text = False

            # Set a timeout
            for _ in range(30):  # Wait up to 30 seconds
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)

                    if data.get("mime_type") == "audio/pcm":
                        audio_len = len(data.get("data", ""))
                        print(f"✓ Received audio data: {audio_len} bytes (base64)")
                        received_audio = True
                    elif data.get("mime_type") == "text/plain":
                        print(f"✓ Received text: {data.get('data', '')[:100]}")
                        received_text = True
                    elif data.get("turn_complete"):
                        print(f"✓ Turn complete!")
                        break
                    else:
                        print(f"Received: {str(data)[:100]}")

                except asyncio.TimeoutError:
                    continue

            if received_audio:
                print("\n✓✓✓ SUCCESS: Audio streaming is working!")
            elif received_text:
                print("\n⚠ Partial success: Text received but no audio")
            else:
                print("\n✗ No response received")

    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
