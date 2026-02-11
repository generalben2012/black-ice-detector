# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from base64 import b64decode, b64encode
import json
import os
import time
import yaml
from datetime import datetime, UTC, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen


def enable_fhd_stream():

    video_device = os.getenv("VIDEO_DEVICE", "/dev/video1")
    default_args = (
        f"v4l2src device={video_device} ! video/x-raw,width=1920,height=1080,framerate=5/1 "
        "! videoconvert ! jpegenc quality=70"
    )
    os.environ.setdefault("GST_LAUNCH_ARGS", default_args)

    try:
        compose_path = Path(VideoObjectDetection.__module__.replace(".", "/")).with_suffix("")
        compose_path = Path("/usr/local/lib/python3.13/site-packages") / compose_path / "brick_compose.yaml"
        if not compose_path.exists():
            return False

        compose = yaml.safe_load(compose_path.read_text())
        services = compose.get("services", {})
        service = services.get("ei-video-obj-detection-runner", {})
        command = service.get("command", [])
        if isinstance(command, list):
            if "--gst-launch-args" not in command:
                insert_at = command.index("--camera") if "--camera" in command else len(command)
                command[insert_at:insert_at] = ["--gst-launch-args", "${GST_LAUNCH_ARGS}"]
                service["command"] = command
                services["ei-video-obj-detection-runner"] = service
                compose["services"] = services
                compose_path.write_text(yaml.safe_dump(compose, sort_keys=False))
        return True
    except Exception as e:
        print(f"⚠️ FHD setup skipped: {e}")
        return False

# Initialize WebUI
ui = WebUI()
enable_fhd_stream()
camera_stream = VideoObjectDetection(confidence=0.5, debounce_sec=0.0)

# Distance measurement settings
UPDATE_INTERVAL = 0.05  # Update every 50ms (20 readings per second)
last_update_time = 0.0
MEASUREMENT_DURATION = 30.0
MEASUREMENT_INTERVAL = 5.0
measurement_session = None
KST_TZ = timezone(timedelta(hours=9))
PHOTO_DIR = Path(__file__).parent / "photos"
CAMERA_HOST = os.getenv("EI_VIDEO_HOST", "ei-video-obj-detection-runner")
CAMERA_BASE_URL = f"http://{CAMERA_HOST}:4912"

print("Python backend starting...")
print("WebUI initialized")

MEASUREMENTS_PATH = Path(__file__).parent / "measurements.jsonl"
PHOTO_DIR.mkdir(parents=True, exist_ok=True)


def fetch_url_bytes(url, timeout=3, data=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    if data is not None:
        headers["Content-Type"] = "text/plain;charset=UTF-8"
    request = Request(url, data=data, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        return response.read(), content_type

def parse_engineio_payload(payload_text):
    if "\x1e" in payload_text:
        return [part for part in payload_text.split("\x1e") if part]
    packets = []
    idx = 0
    length = len(payload_text)
    while idx < length:
        if payload_text[idx].isdigit():
            j = idx
            while j < length and payload_text[j].isdigit():
                j += 1
            if j < length and payload_text[j] == ":":
                packet_len = int(payload_text[idx:j])
                start = j + 1
                end = start + packet_len
                packets.append(payload_text[start:end])
                idx = end
                continue
        packets.append(payload_text[idx:])
        break
    return packets

def parse_socketio_event(packet):
    if not packet.startswith("42"):
        return None, None
    try:
        payload = json.loads(packet[2:])
        if isinstance(payload, list) and len(payload) >= 2:
            return payload[0], payload[1]
    except Exception:
        return None, None
    return None, None

def decode_data_url(data_url):
    if not isinstance(data_url, str):
        return None, None
    if data_url.startswith("data:") and "," in data_url:
        header, b64_data = data_url.split(",", 1)
        mime_type = header.split(";")[0].replace("data:", "")
        return b64decode(b64_data), mime_type
    return None, None

def capture_image_via_socketio(timeout_sec=3, max_polls=6):
    try:
        open_payload, _ = fetch_url_bytes(
            f"{CAMERA_BASE_URL}/socket.io/?EIO=4&transport=polling&t={int(time.time() * 1000)}",
            timeout=timeout_sec,
        )
        packets = parse_engineio_payload(open_payload.decode("utf-8", errors="ignore"))
        sid = None
        for packet in packets:
            if packet.startswith("0"):
                info = json.loads(packet[1:])
                sid = info.get("sid")
                break
        if not sid:
            return None, None

        fetch_url_bytes(
            f"{CAMERA_BASE_URL}/socket.io/?EIO=4&transport=polling&sid={sid}",
            timeout=timeout_sec,
            data=b"40",
        )
        fetch_url_bytes(
            f"{CAMERA_BASE_URL}/socket.io/?EIO=4&transport=polling&sid={sid}",
            timeout=timeout_sec,
            data=b'42["hello"]',
        )

        for _ in range(max_polls):
            poll_payload, _ = fetch_url_bytes(
                f"{CAMERA_BASE_URL}/socket.io/?EIO=4&transport=polling&sid={sid}&t={int(time.time() * 1000)}",
                timeout=timeout_sec,
            )
            packets = parse_engineio_payload(poll_payload.decode("utf-8", errors="ignore"))
            for packet in packets:
                if packet == "2":
                    fetch_url_bytes(
                        f"{CAMERA_BASE_URL}/socket.io/?EIO=4&transport=polling&sid={sid}",
                        timeout=timeout_sec,
                        data=b"3",
                    )
                    continue
                event, data = parse_socketio_event(packet)
                if event == "image" and isinstance(data, dict):
                    img_data = data.get("img")
                    image_bytes, mime_type = decode_data_url(img_data)
                    if image_bytes:
                        return image_bytes, mime_type or "image/jpeg"
            time.sleep(0.2)
    except Exception:
        return None, None
    return None, None

def get_camera_snapshot():
    return capture_image_via_socketio()

def capture_photo(measured_at):
    image_bytes, mime_type = get_camera_snapshot()
    if not image_bytes:
        return None, False, "camera snapshot failed"
    ext = "jpg"
    if mime_type == "image/png" or image_bytes.startswith(b"\x89PNG"):
        ext = "png"
    filename = f"{measured_at.isoformat()}.{ext}"
    photo_path = PHOTO_DIR / filename
    try:
        photo_path.write_bytes(image_bytes)
        return filename, True, None
    except Exception as e:
        return filename, False, str(e)

def get_sensor_data():
    """Get duration, distance_mm, and ldr_value from Arduino sensor via Bridge"""
    try:
        # Bridge.call() with shorter timeout (1 second - 더 빠른 응답)
        duration = Bridge.call("get_duration", timeout=1)
        distance_mm = Bridge.call("get_distance_mm", timeout=1)
        ldr_value = Bridge.call("get_ldr_value", timeout=1)
        
        if duration is not None and distance_mm is not None and ldr_value is not None:
            return {
                "duration": int(duration),
                "distance_mm": float(distance_mm),
                "ldr_value": int(ldr_value)
            }
        else:
            # 조용히 처리 (로그 스팸 방지)
            return None
    except TimeoutError:
        # Bridge 통신 타임아웃 - 조용히 처리
        return None
    except Exception as e:
        # 심각한 오류만 출력
        print(f"❌ Error reading sensor data: {e}")
        return None


def start_measurement_session(temperature, road_surface_temp, humidity, location, black_ice_status):
    """Start a 1-minute averaging session for distance and LDR."""
    global measurement_session
    now = time.time()
    measured_at = datetime.now(KST_TZ).replace(microsecond=0)
    photo_filename, photo_saved, photo_error = capture_photo(measured_at)
    measurement_session = {
        "start_time": now,
        "next_sample_time": now,
        "samples": [],
        "temperature": float(temperature),
        "road_surface_temp": float(road_surface_temp),
        "humidity": float(humidity),
        "location": location,
        "black_ice_status": black_ice_status,
        "measured_at": measured_at,
        "photo_filename": photo_filename,
        "photo_saved": photo_saved,
        "photo_error": photo_error,
    }
    total_samples = int(MEASUREMENT_DURATION / MEASUREMENT_INTERVAL)
    ui.send_message("measurement_status", {
        "state": "started",
        "remaining_seconds": int(MEASUREMENT_DURATION),
        "samples_taken": 0,
        "samples_total": total_samples,
    })


def update_measurement_session():
    """Collect samples and finalize when the session ends."""
    global measurement_session
    if not measurement_session:
        return

    now = time.time()
    elapsed = now - measurement_session["start_time"]
    total_samples = int(MEASUREMENT_DURATION / MEASUREMENT_INTERVAL)

    if elapsed >= MEASUREMENT_DURATION:
        finalize_measurement_session(total_samples)
        measurement_session = None
        return

    while now >= measurement_session["next_sample_time"]:
        sensor_data = get_sensor_data()
        if sensor_data and sensor_data["distance_mm"] > 0 and sensor_data["ldr_value"] >= 0:
            measurement_session["samples"].append({
                "distance_mm": sensor_data["distance_mm"],
                "ldr_value": sensor_data["ldr_value"],
            })
        measurement_session["next_sample_time"] += MEASUREMENT_INTERVAL
        now = time.time()
        elapsed = now - measurement_session["start_time"]

        ui.send_message("measurement_status", {
            "state": "progress",
            "remaining_seconds": max(0, int(MEASUREMENT_DURATION - elapsed)),
            "samples_taken": len(measurement_session["samples"]),
            "samples_total": total_samples,
        })


def finalize_measurement_session(total_samples):
    """Compute averages and send result to the UI."""
    samples = measurement_session["samples"]
    if samples:
        distance_mm_avg = sum(s["distance_mm"] for s in samples) / len(samples)
        ldr_avg = sum(s["ldr_value"] for s in samples) / len(samples)
        distance_cm_avg = distance_mm_avg / 10.0
    else:
        distance_cm_avg = -1.0
        ldr_avg = -1.0

    result = {
        "distance_cm_avg": distance_cm_avg,
        "ldr_avg": ldr_avg,
        "temperature": measurement_session["temperature"],
        "road_surface_temp": measurement_session["road_surface_temp"],
        "humidity": measurement_session["humidity"],
        "location": measurement_session["location"],
        "black_ice_status": measurement_session["black_ice_status"],
        "photo_filename": measurement_session["photo_filename"],
        "photo_saved": measurement_session["photo_saved"],
        "photo_error": measurement_session["photo_error"],
        "samples_taken": len(samples),
        "samples_total": total_samples,
    }
    save_measurement_result(result, measurement_session["measured_at"])
    ui.send_message("measurement_result", result)
    ui.send_message("measurement_status", {
        "state": "completed",
        "remaining_seconds": 0,
        "samples_taken": len(samples),
        "samples_total": total_samples,
    })


def save_measurement_result(result, measured_at):
    """Append measurement result to JSONL file with date/time fields."""
    record = {
        "measured_at": measured_at.isoformat(),
        "date": measured_at.date().isoformat(),
        "time": measured_at.time().replace(microsecond=0).isoformat(),
        "measurement_duration_sec": MEASUREMENT_DURATION,
        "measurement_interval_sec": MEASUREMENT_INTERVAL,
        **result,
    }
    try:
        with MEASUREMENTS_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"❌ Failed to write measurement log: {e}")


def send_distance_update():
    """Send distance update to all connected clients"""
    global last_update_time
    
    current_time = time.time()
    
    # Check if enough time has passed since last update
    if current_time - last_update_time >= UPDATE_INTERVAL:
        sensor_data = get_sensor_data()
        
        # Always send message, even if sensor data is invalid
        if sensor_data is not None:
            # Prepare message with distance, duration, distance_mm, ldr_value
            distance_mm = sensor_data["distance_mm"]
            distance_cm = distance_mm / 10.0  # mm to cm
            message = {
                "distance": distance_cm,
                "duration": sensor_data["duration"],
                "distance_mm": distance_mm,
                "ldr_value": sensor_data["ldr_value"],
                "timestamp": datetime.now(UTC).isoformat(),
                "unit": "cm",
                "valid": distance_cm > 0 and sensor_data["duration"] > 0
            }
            
            # Send to all connected clients
            ui.send_message("distance_update", message)
            
            # Print to console for debugging
            #if distance_cm > 0 and sensor_data["duration"] > 0:
            #    print(f"✅ Distance: {distance_cm:.2f} cm ({distance_mm:.2f} mm), Duration: {sensor_data['duration']} us")
            #else:
            #    print(f"⚠️ Invalid distance: {distance_cm:.2f} cm, Duration: {sensor_data['duration']} us")
        else:
            # Send error message if sensor reading failed
            message = {
                "distance": -1.0,
                "duration": -1,
                "distance_mm": -1.0,
                "ldr_value": -1,
                "timestamp": datetime.now(UTC).isoformat(),
                "unit": "cm",
                "valid": False
            }
            ui.send_message("distance_update", message)
        
        last_update_time = current_time

def on_client_connected(client_id, data):
    """Send initial distance reading when client connects"""
    print(f"Client connected: {client_id}")
    ui.send_message("config", {
        "measurement_duration": MEASUREMENT_DURATION,
        "measurement_interval": MEASUREMENT_INTERVAL,
    })
    sensor_data = get_sensor_data()
    if sensor_data is not None:
        distance_mm = sensor_data["distance_mm"]
        distance_cm = distance_mm / 10.0  # mm to cm
        message = {
            "distance": distance_cm,
            "duration": sensor_data["duration"],
            "distance_mm": distance_mm,
            "ldr_value": sensor_data["ldr_value"],
            "timestamp": datetime.now(UTC).isoformat(),
            "unit": "cm",
            "valid": distance_cm > 0 and sensor_data["duration"] > 0
        }
        ui.send_message("distance_update", message)
        print(f"Sent initial distance: {distance_cm:.2f} cm ({distance_mm:.2f} mm), Duration: {sensor_data['duration']} us")
    else:
        # Even if sensor reading fails, send -1 to show connection is working
        message = {
            "distance": -1.0,
            "duration": -1,
            "distance_mm": -1.0,
            "ldr_value": -1,
            "timestamp": datetime.now(UTC).isoformat(),
            "unit": "cm",
            "valid": False
        }
        ui.send_message("distance_update", message)
        print("Sent initial message (sensor reading failed)")


def on_measurement_request(client_id, data):
    """Handle measurement request from UI."""
    try:
        temperature = data.get("temperature")
        road_surface_temp = data.get("road_surface_temp")
        humidity = data.get("humidity")
        location = data.get("location")
        black_ice_status = data.get("black_ice_status")
        if temperature is None or road_surface_temp is None or humidity is None or location is None or black_ice_status is None:
            raise ValueError("missing temperature, road_surface_temp, humidity, location, or black_ice_status")
        if black_ice_status not in ("occurred", "not_occurred", "unknown"):
            raise ValueError("invalid black_ice_status")
        start_measurement_session(temperature, road_surface_temp, humidity, location, black_ice_status)
    except Exception as e:
        ui.send_message("measurement_status", {
            "state": "error",
            "message": f"측정 시작 실패: {e}",
        })

def read_measurements():
    if not MEASUREMENTS_PATH.exists():
        return []
    items = []
    try:
        with MEASUREMENTS_PATH.open("r", encoding="utf-8") as file:
            for index, line in enumerate(file):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    record["record_id"] = record.get("measured_at") or f"line-{index}"
                    items.append(record)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"❌ Failed to read measurements: {e}")
    items.sort(key=lambda x: x.get("measured_at", ""), reverse=True)
    return items

def on_measurement_list_request(client_id, data):
    items = read_measurements()
    summary = []
    for record in items:
        summary.append({
            "record_id": record.get("record_id"),
            "measured_at": record.get("measured_at"),
            "location": record.get("location"),
            "black_ice_status": record.get("black_ice_status"),
        })
    ui.send_message("measurement_list", {"items": summary})

def on_measurement_detail_request(client_id, data):
    record_id = data.get("record_id") if isinstance(data, dict) else None
    if not record_id:
        ui.send_message("measurement_detail", {"detail": None})
        return
    items = read_measurements()
    match = next((item for item in items if item.get("record_id") == record_id), None)
    if not match:
        ui.send_message("measurement_detail", {"detail": None})
        return
    photo_filename = match.get("photo_filename")
    if photo_filename:
        photo_path = PHOTO_DIR / photo_filename
        if photo_path.exists():
            try:
                photo_bytes = photo_path.read_bytes()
                match["photo_data"] = b64encode(photo_bytes).decode("utf-8")
                match["photo_mime"] = "image/jpeg" if photo_filename.lower().endswith(".jpg") else "image/png"
            except Exception as e:
                match["photo_error"] = str(e)
    ui.send_message("measurement_detail", {"detail": match})


# Register WebSocket event handlers
ui.on_message("client_connected", on_client_connected)
ui.on_message("measurement_request", on_measurement_request)
ui.on_message("measurement_list_request", on_measurement_list_request)
ui.on_message("measurement_detail_request", on_measurement_detail_request)

# Main application loop
def main_loop():
    """Main loop to continuously send distance updates"""
    print("✅ Main loop started")
    loop_count = 0
    while True:
        try:
            send_distance_update()
            update_measurement_session()
            loop_count += 1
            # Print status every 50 loops (about every 2.5 seconds)
            if loop_count % 50 == 0:
                print(f"🔄 Main loop running... (loop {loop_count}, {loop_count * UPDATE_INTERVAL:.1f}s elapsed)")
            time.sleep(0.05)  # Small delay to prevent CPU overload
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(0.1)  # Wait a bit before retrying

# Run the app with custom loop
print("Starting App.run()...")
App.run(user_loop=main_loop)

