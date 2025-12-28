# 3단계: Python 백엔드 작성

이 문서는 Arduino Bridge를 통해 거리 값을 읽고 웹 클라이언트에 전송하는 Python 백엔드를 작성하는 방법을 설명합니다.

## 목표

- Arduino Bridge를 통해 거리 값을 읽기
- WebSocket을 사용하여 웹 클라이언트에 실시간으로 거리 값 전송
- 주기적으로 거리 값을 업데이트

## Arduino Bridge란?

Arduino Bridge는 Python 백엔드와 Arduino 스케치 간의 통신을 가능하게 하는 메커니즘입니다:

- **Bridge.provide()**: Arduino에서 Python으로 함수 제공
- **Bridge.call()**: Python에서 Arduino 함수 호출
- 양방향 통신 지원

## Python 백엔드 코드 작성

**파일 위치:** `black-ice-detector/python/main.py`

### 전체 코드

```python
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

def get_distance_from_sensor():
    """Get distance measurement from Arduino sensor via Bridge"""
    try:
        result = Bridge.call("get_distance").result()
        if result is not None:
            distance = float(result)
            return distance
        return None
    except Exception as e:
        print(f"Error reading distance: {e}")
        return None

def send_distance_update():
    """Send distance update to all connected clients"""
    global last_update_time
    
    current_time = time.time()
    
    # Check if enough time has passed since last update
    if current_time - last_update_time >= UPDATE_INTERVAL:
        distance = get_distance_from_sensor()
        
        if distance is not None:
            # Prepare message with distance and timestamp
            message = {
                "distance": distance,
                "timestamp": datetime.now(UTC).isoformat(),
                "unit": "cm",
                "valid": distance > 0
            }
            
            # Send to all connected clients
            ui.send_message("distance_update", message)
            
            # Print to console for debugging
            if distance > 0:
                print(f"Distance: {distance:.2f} cm")
            else:
                print("Invalid distance reading")
        
        last_update_time = current_time

def on_client_connected(client_id, data):
    """Send initial distance reading when client connects"""
    distance = get_distance_from_sensor()
    if distance is not None:
        ui.send_message("distance_update", {
            "distance": distance,
            "timestamp": datetime.now(UTC).isoformat(),
            "unit": "cm",
            "valid": distance > 0
        })

# Register WebSocket event handlers
ui.on_message("client_connected", on_client_connected)

# Main application loop
def main_loop():
    """Main loop to continuously send distance updates"""
    while True:
        send_distance_update()
        time.sleep(0.05)  # Small delay to prevent CPU overload

# Run the app with custom loop
App.run(user_loop=main_loop)
```

## 코드 설명

### 1. 라이브러리 임포트

```python
from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import time
from datetime import datetime, UTC
```

- `arduino.app_utils`: Arduino App Lab의 유틸리티 함수
- `arduino.app_bricks.web_ui`: WebSocket 통신을 위한 WebUI Brick
- `time`: 시간 관련 함수
- `datetime`: 타임스탬프 생성

### 2. WebUI 초기화

```python
ui = WebUI()
```

- WebSocket 서버를 생성하여 웹 클라이언트와 실시간 통신

### 3. 거리 값 읽기 함수

```python
def get_distance_from_sensor():
    """Get distance measurement from Arduino sensor via Bridge"""
    try:
        result = Bridge.call("get_distance").result()
        if result is not None:
            distance = float(result)
            return distance
        return None
    except Exception as e:
        print(f"Error reading distance: {e}")
        return None
```

**동작 과정:**
1. `Bridge.call("get_distance")`: Arduino의 `get_distance()` 함수 호출
2. `.result()`: 결과 값 가져오기
3. `float(result)`: 문자열을 실수로 변환
4. 예외 처리: 오류 발생 시 None 반환

### 4. 거리 값 전송 함수

```python
def send_distance_update():
    """Send distance update to all connected clients"""
    global last_update_time
    
    current_time = time.time()
    
    # Check if enough time has passed since last update
    if current_time - last_update_time >= UPDATE_INTERVAL:
        distance = get_distance_from_sensor()
        
        if distance is not None:
            # Prepare message with distance and timestamp
            message = {
                "distance": distance,
                "timestamp": datetime.now(UTC).isoformat(),
                "unit": "cm",
                "valid": distance > 0
            }
            
            # Send to all connected clients
            ui.send_message("distance_update", message)
            
            # Print to console for debugging
            if distance > 0:
                print(f"Distance: {distance:.2f} cm")
            else:
                print("Invalid distance reading")
        
        last_update_time = current_time
```

**동작 과정:**
1. **업데이트 주기 확인**: `UPDATE_INTERVAL` (0.1초)마다 실행
2. **거리 값 읽기**: Bridge를 통해 Arduino에서 거리 값 읽기
3. **메시지 생성**: 거리, 타임스탬프, 단위, 유효성 포함
4. **전송**: `ui.send_message()`로 모든 연결된 클라이언트에 전송

### 5. 클라이언트 연결 핸들러

```python
def on_client_connected(client_id, data):
    """Send initial distance reading when client connects"""
    distance = get_distance_from_sensor()
    if distance is not None:
        ui.send_message("distance_update", {
            "distance": distance,
            "timestamp": datetime.now(UTC).isoformat(),
            "unit": "cm",
            "valid": distance > 0
        })
```

- 새 클라이언트가 연결되면 즉시 현재 거리 값을 전송

### 6. 메인 루프

```python
def main_loop():
    """Main loop to continuously send distance updates"""
    while True:
        send_distance_update()
        time.sleep(0.05)  # Small delay to prevent CPU overload

App.run(user_loop=main_loop)
```

- `App.run(user_loop=main_loop)`: 사용자 정의 루프로 앱 실행
- 0.05초마다 거리 업데이트 함수 호출

## WebSocket 메시지 형식

웹 클라이언트로 전송되는 메시지 형식:

```json
{
    "distance": 25.5,
    "timestamp": "2025-01-20T10:30:45.123456+00:00",
    "unit": "cm",
    "valid": true
}
```

**필드 설명:**
- `distance`: 측정된 거리 값 (cm)
- `timestamp`: 측정 시간 (ISO 8601 형식)
- `unit`: 거리 단위 ("cm")
- `valid`: 유효한 측정인지 여부 (true/false)

## 커스터마이징

### 업데이트 주기 변경

더 빠른 업데이트를 원하면:

```python
UPDATE_INTERVAL = 0.05  # 50ms (20 readings per second)
```

더 느린 업데이트를 원하면:

```python
UPDATE_INTERVAL = 0.5  # 500ms (2 readings per second)
```

### 메시지 형식 변경

추가 정보를 포함하려면:

```python
message = {
    "distance": distance,
    "timestamp": datetime.now(UTC).isoformat(),
    "unit": "cm",
    "valid": distance > 0,
    "sensor_id": "HC-SR04",  # 추가 필드
    "temperature": 20.0       # 추가 필드
}
```

## 디버깅

### 콘솔 출력 확인

Arduino App Lab의 콘솔에서 다음 메시지를 확인할 수 있습니다:

```
Distance: 25.50 cm
Distance: 30.25 cm
Invalid distance reading
Error reading distance: ...
```

### Bridge 통신 오류 처리

Bridge 통신이 실패하는 경우:

```python
def get_distance_from_sensor():
    try:
        result = Bridge.call("get_distance").result()
        if result is None:
            print("Warning: Bridge returned None")
            return None
        distance = float(result)
        return distance
    except Exception as e:
        print(f"Error reading distance: {e}")
        import traceback
        traceback.print_exc()  # 상세한 오류 정보 출력
        return None
```

## 문제 해결

### Bridge.call()이 None을 반환함

**원인:**
- Arduino 스케치가 업로드되지 않음
- Bridge.provide()가 제대로 설정되지 않음

**해결:**
1. Arduino 스케치 업로드 확인
2. 시리얼 모니터에서 "Black Ice Detector initialized" 메시지 확인
3. Bridge.provide("get_distance", get_distance) 코드 확인

### WebSocket 연결 오류

**원인:**
- WebUI Brick이 제대로 초기화되지 않음
- 포트 충돌

**해결:**
1. app.yaml에 `web_ui` Brick이 포함되어 있는지 확인
2. 다른 앱이 같은 포트를 사용하고 있는지 확인

### 업데이트가 너무 느림/빠름

**해결:**
- `UPDATE_INTERVAL` 값을 조정
- `main_loop()`의 `time.sleep()` 값 조정

## 다음 단계

Python 백엔드가 완성되었으므로 다음 단계로 진행합니다:

- [4단계: 웹 인터페이스 작성](04-웹-인터페이스-작성.md) - HTML, CSS, JavaScript로 UI 구현

## 체크리스트

- [ ] Python 백엔드 코드 작성 완료
- [ ] Bridge 통신 함수 구현 완료
- [ ] WebSocket 메시지 전송 구현 완료
- [ ] 업데이트 루프 구현 완료
- [ ] 콘솔에서 거리 값 출력 확인 완료

