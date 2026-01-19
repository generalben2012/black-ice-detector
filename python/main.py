# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import json
import time
from datetime import datetime, UTC
from pathlib import Path

# Initialize WebUI
ui = WebUI()

# Distance measurement settings
UPDATE_INTERVAL = 0.05  # Update every 50ms (20 readings per second)
last_update_time = 0.0
MEASUREMENT_DURATION = 30.0
MEASUREMENT_INTERVAL = 5.0
measurement_session = None

print("Python backend starting...")
print("WebUI initialized")

MEASUREMENTS_PATH = Path(__file__).parent / "measurements.jsonl"

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


def start_measurement_session(temperature, humidity, location):
    """Start a 1-minute averaging session for distance and LDR."""
    global measurement_session
    now = time.time()
    measurement_session = {
        "start_time": now,
        "next_sample_time": now,
        "samples": [],
        "temperature": float(temperature),
        "humidity": float(humidity),
        "location": location,
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
        "humidity": measurement_session["humidity"],
        "location": measurement_session["location"],
        "samples_taken": len(samples),
        "samples_total": total_samples,
    }
    save_measurement_result(result)
    ui.send_message("measurement_result", result)
    ui.send_message("measurement_status", {
        "state": "completed",
        "remaining_seconds": 0,
        "samples_taken": len(samples),
        "samples_total": total_samples,
    })


def save_measurement_result(result):
    """Append measurement result to JSONL file with date/time fields."""
    now = datetime.now().astimezone()
    record = {
        "measured_at": now.isoformat(),
        "date": now.date().isoformat(),
        "time": now.time().replace(microsecond=0).isoformat(),
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
        humidity = data.get("humidity")
        location = data.get("location")
        if temperature is None or humidity is None or location is None:
            raise ValueError("missing temperature, humidity, or location")
        start_measurement_session(temperature, humidity, location)
    except Exception as e:
        ui.send_message("measurement_status", {
            "state": "error",
            "message": f"측정 시작 실패: {e}",
        })


# Register WebSocket event handlers
ui.on_message("client_connected", on_client_connected)
ui.on_message("measurement_request", on_measurement_request)

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

