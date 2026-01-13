"""Test which models are available and support live audio"""

import google.generativeai as genai
from app.config import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)

print("Testing available models for live audio support...")
print("=" * 60)

# List all models
models = genai.list_models()

# Filter for models that might support live/streaming
audio_capable = []
for model in models:
    name = model.name
    methods = getattr(model, "supported_generation_methods", [])

    # Check for bidi or live support
    if any("bidi" in str(m).lower() or "stream" in str(m).lower() for m in methods):
        audio_capable.append((name, methods))

    # Also check if name suggests audio support
    if "audio" in name.lower() or "live" in name.lower() or "exp" in name.lower():
        if (name, methods) not in audio_capable:
            audio_capable.append((name, methods))

print("\nModels potentially supporting live audio:")
for name, methods in audio_capable:
    print(f"\n{name}")
    print(f"  Methods: {methods}")

# Try to check quota by making a simple request
print("\n" + "=" * 60)
print("\nTesting API quota with a simple request...")

try:
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    response = model.generate_content("Say 'test'")
    print(f"✓ gemini-2.0-flash-exp: API working! Response: {response.text[:50]}")
except Exception as e:
    print(f"✗ gemini-2.0-flash-exp: {str(e)[:100]}")

try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content("Say 'test'")
    print(f"✓ gemini-2.5-flash: API working! Response: {response.text[:50]}")
except Exception as e:
    print(f"✗ gemini-2.5-flash: {str(e)[:100]}")

try:
    model = genai.GenerativeModel("gemini-2.5-flash-native-audio-latest")
    response = model.generate_content("Say 'test'")
    print(
        f"✓ gemini-2.5-flash-native-audio-latest: API working! Response: {response.text[:50]}"
    )
except Exception as e:
    print(f"✗ gemini-2.5-flash-native-audio-latest: {str(e)[:100]}")
