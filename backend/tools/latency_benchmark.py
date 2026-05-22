"""
Simple async WebSocket benchmark harness.
Requires: `websockets` and `aiofiles` (optional) installed in environment.
Usage:
    python backend/tools/latency_benchmark.py --url ws://localhost:10000/ws/voice/patient_001 --file test.wav

It will open a websocket, send the file as binary in a single message, then send a text message "END_AUDIO" and measure round-trip time from END_AUDIO to audio_response.
"""
import asyncio
import argparse
import time
import base64
import os

import websockets


async def run(url: str, file_path: str):
    async with websockets.connect(url) as ws:
        print("Connected to", url)

        # wait for session_start
        start_msg = await ws.recv()
        print("Server sent:", start_msg)

        # send audio bytes
        with open(file_path, "rb") as f:
            data = f.read()

        # send as a single binary message
        await ws.send(data)
        print(f"Sent {len(data)} bytes of audio")

        # send END_AUDIO signal and measure
        await asyncio.sleep(0.1)
        t0 = time.perf_counter()
        await ws.send("END_AUDIO")

        while True:
            msg = await ws.recv()
            # websocket library returns bytes or str
            if isinstance(msg, bytes):
                print("Received binary message of length", len(msg))
                continue

            # try parse as JSON-like
            try:
                import json
                m = json.loads(msg)
            except Exception:
                print("Received non-json message:", msg)
                continue

            if m.get("type") == "audio_response":
                t1 = time.perf_counter()
                print("Received audio_response (base64) length", len(m.get("audio","")))
                print(f"End-to-end latency: {(t1-t0)*1000.0:.1f} ms")
                break
            else:
                print("Message:", m)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--file", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print("Audio file not found:", args.file)
        raise SystemExit(1)

    asyncio.run(run(args.url, args.file))
