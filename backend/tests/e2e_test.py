#!/usr/bin/env python
"""
End-to-End System Test
Verifies full voice agent pipeline: WebSocket → STT → LLM → Tools → TTS
"""
import asyncio
import json
import sys
import time
from pathlib import Path

import websockets

API_URL = "ws://localhost:8000/ws/voice/patient_e2e_test"


async def send_wav_file(websocket, file_path: str) -> None:
    """Send WAV file as binary chunks"""
    with open(file_path, "rb") as f:
        audio_data = f.read()
    print(f"[TEST] Sending {len(audio_data)} bytes of audio...")
    await websocket.send(audio_data)


async def end_audio(websocket) -> None:
    """Send END_AUDIO marker"""
    await websocket.send(b"END_AUDIO")
    print("[TEST] Sent END_AUDIO marker")


async def receive_responses(websocket, timeout: int = 30) -> dict:
    """Receive all messages until response is complete"""
    results = {
        "session_id": None,
        "transcript": None,
        "reasoning": None,
        "response_text": None,
        "latency_metrics": None,
        "errors": [],
    }

    try:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                message_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(message_raw)

                if message.get("type") == "session_start":
                    results["session_id"] = message.get("session_id")
                    print(f"✅ Session: {results['session_id']}")

                elif message.get("type") == "transcript":
                    results["transcript"] = message.get("text")
                    lang = message.get("language", "unknown")
                    print(f"✅ STT: {results['transcript']} (lang: {lang})")

                elif message.get("type") == "reasoning_trace":
                    results["reasoning"] = {
                        "intent": message.get("intent"),
                        "confidence": message.get("confidence"),
                        "entities": message.get("entities"),
                    }
                    print(
                        f"✅ Intent: {results['reasoning']['intent']} "
                        f"({results['reasoning']['confidence']:.0%})"
                    )
                    if results["reasoning"]["entities"]:
                        print(f"   Entities: {results['reasoning']['entities']}")

                elif message.get("type") == "response":
                    results["response_text"] = message.get("text")
                    has_audio = bool(message.get("audio"))
                    print(f"✅ Response: {results['response_text']}")
                    print(f"   Audio included: {has_audio}")

                elif message.get("type") == "latency_metrics":
                    results["latency_metrics"] = {
                        "total_ms": message.get("total_latency_ms"),
                        "breakdown": message.get("breakdown", {}),
                    }
                    print(f"✅ Latency: {results['latency_metrics']['total_ms']:.1f}ms total")
                    for component, duration in results["latency_metrics"]["breakdown"].items():
                        print(f"   {component}: {duration:.1f}ms")

                elif message.get("type") == "error":
                    results["errors"].append(message.get("message"))
                    print(f"❌ Error: {message.get('message')}")

                # Check if we have complete response
                if (
                    results["response_text"]
                    and results["latency_metrics"]
                ):
                    print("\n[TEST] ✅ Complete response received!")
                    return results

            except asyncio.TimeoutError:
                pass

    except Exception as e:
        print(f"\n[TEST] ❌ Exception while receiving: {e}")
        results["errors"].append(str(e))

    if not results["response_text"]:
        results["errors"].append("No response received")
        print("\n[TEST] ❌ Timeout or incomplete response")

    return results


async def test_voice_pipeline(audio_file: str) -> bool:
    """Test full voice pipeline with sample audio"""
    print(f"\n{'='*60}")
    print("🎤 VOICE AGENT E2E TEST")
    print(f"{'='*60}\n")

    if not Path(audio_file).exists():
        print(f"❌ Audio file not found: {audio_file}")
        print(
            "   Create a test audio file using: rec test_audio.wav rate 16000 channels 1\n"
            "   Or use: ffmpeg -f lavfi -i sine=f=440:d=2 test_audio.wav"
        )
        return False

    try:
        print(f"[TEST] Connecting to WebSocket: {API_URL}")
        async with websockets.connect(API_URL) as websocket:
            print("✅ Connected!")

            print(f"\n[TEST] Sending audio file: {audio_file}")
            await send_wav_file(websocket, audio_file)

            print("[TEST] Signaling end of audio...")
            await end_audio(websocket)

            print("\n[TEST] Waiting for responses...\n")
            results = await receive_responses(websocket)

            print(f"\n{'='*60}")
            print("📊 TEST RESULTS")
            print(f"{'='*60}\n")

            # Validation checks
            checks = {
                "Session started": results["session_id"] is not None,
                "STT recognized speech": results["transcript"] is not None,
                "LLM parsed intent": results["reasoning"] is not None,
                "Agent responded": results["response_text"] is not None,
                "Latency measured": results["latency_metrics"] is not None,
                "No errors": len(results["errors"]) == 0,
            }

            if results["latency_metrics"]:
                total_ms = results["latency_metrics"]["total_ms"]
                checks["Latency <450ms"] = total_ms < 450

            all_passed = all(checks.values())

            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"{status} {check}")

            if results["errors"]:
                print(f"\n⚠️  Errors encountered:")
                for error in results["errors"]:
                    print(f"   - {error}")

            print(f"\n{'='*60}")
            if all_passed:
                print("🎉 ALL TESTS PASSED!")
            else:
                print("⚠️  SOME TESTS FAILED")
            print(f"{'='*60}\n")

            return all_passed

    except ConnectionRefusedError:
        print("❌ Connection refused. Is backend running on localhost:8000?")
        print("   Start it with: uvicorn main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_appointment_api():
    """Test REST appointment endpoints"""
    print(f"\n{'='*60}")
    print("📅 APPOINTMENT API TEST")
    print(f"{'='*60}\n")

    try:
        import httpx

        async with httpx.AsyncClient() as client:
            base_url = "http://localhost:8000"

            # Test GET appointments
            print("[TEST] GET /api/appointments/patient_e2e_test")
            resp = await client.get(f"{base_url}/api/appointments/patient_e2e_test")
            if resp.status_code == 200:
                print(f"✅ Status 200, data: {resp.json()}")
            else:
                print(f"❌ Status {resp.status_code}: {resp.text}")

            # Test GET doctors
            print("\n[TEST] GET /api/doctors")
            resp = await client.get(f"{base_url}/api/doctors")
            if resp.status_code == 200:
                doctors = resp.json().get("data", [])
                print(f"✅ Found {len(doctors)} doctors")
            else:
                print(f"❌ Status {resp.status_code}")

            # Test TTS
            print("\n[TEST] POST /api/tts")
            resp = await client.post(
                f"{base_url}/api/tts",
                json={
                    "text": "Your appointment has been confirmed",
                    "language": "en",
                    "session_id": "test_session",
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                has_audio = bool(data.get("audio"))
                print(f"✅ TTS success, audio: {has_audio}")
            else:
                print(f"❌ Status {resp.status_code}")

            print("\n✅ Appointment API tests complete!\n")

    except Exception as e:
        print(f"❌ API test failed: {e}")


async def main():
    """Run all tests"""
    # Check if audio file provided
    audio_file = sys.argv[1] if len(sys.argv) > 1 else "test_audio.wav"

    # Run voice pipeline test
    voice_passed = await test_voice_pipeline(audio_file)

    # Run API tests
    await test_appointment_api()

    # Exit code
    sys.exit(0 if voice_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
