# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import time
from datetime import datetime, UTC

# Initialize WebUI
ui = WebUI()

# Distance measurement settings
UPDATE_INTERVAL = 0.1  # Update every 100ms (10 readings per second)
last_update_time = 0.0

print("Python backend starting...")
print("WebUI initialized")

def get_sensor_data():
    """Get duration and distance_mm from Arduino sensor via Bridge"""
    try:
        # Bridge.call() with shorter timeout (1 second - 더 빠른 응답)
        duration = Bridge.call("get_duration", timeout=1)
        distance_mm = Bridge.call("get_distance_mm", timeout=1)
        
        if duration is not None and distance_mm is not None:
            return {
                "duration": int(duration),
                "distance_mm": float(distance_mm)
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


def send_distance_update():
    """Send distance update to all connected clients"""
    global last_update_time
    
    current_time = time.time()
    
    # Check if enough time has passed since last update
    if current_time - last_update_time >= UPDATE_INTERVAL:
        sensor_data = get_sensor_data()
        
        # Always send message, even if sensor data is invalid
        if sensor_data is not None:
            # Prepare message with distance, duration, distance_mm
            distance_mm = sensor_data["distance_mm"]
            distance_cm = distance_mm / 10.0  # mm to cm
            message = {
                "distance": distance_cm,
                "duration": sensor_data["duration"],
                "distance_mm": distance_mm,
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
                "timestamp": datetime.now(UTC).isoformat(),
                "unit": "cm",
                "valid": False
            }
            ui.send_message("distance_update", message)
        
        last_update_time = current_time

def on_client_connected(client_id, data):
    """Send initial distance reading when client connects"""
    print(f"Client connected: {client_id}")
    sensor_data = get_sensor_data()
    if sensor_data is not None:
        distance_mm = sensor_data["distance_mm"]
        distance_cm = distance_mm / 10.0  # mm to cm
        message = {
            "distance": distance_cm,
            "duration": sensor_data["duration"],
            "distance_mm": distance_mm,
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
            "timestamp": datetime.now(UTC).isoformat(),
            "unit": "cm",
            "valid": False
        }
        ui.send_message("distance_update", message)
        print("Sent initial message (sensor reading failed)")

# Register WebSocket event handlers
ui.on_message("client_connected", on_client_connected)

# Main application loop
def main_loop():
    """Main loop to continuously send distance updates"""
    print("✅ Main loop started")
    loop_count = 0
    while True:
        try:
            send_distance_update()
            loop_count += 1
            # Print status every 50 loops (about every 2.5 seconds)
            if loop_count % 50 == 0:
                print(f"🔄 Main loop running... (loop {loop_count}, {loop_count * 0.1:.1f}s elapsed)")
            time.sleep(0.05)  # Small delay to prevent CPU overload
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(0.1)  # Wait a bit before retrying

# Run the app with custom loop
print("Starting App.run()...")
App.run(user_loop=main_loop)

