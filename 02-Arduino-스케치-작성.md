# 2단계: Arduino 스케치 작성

이 문서는 HC-SR04 초음파 센서를 제어하는 Arduino 스케치를 작성하는 방법을 설명합니다.

## 목표

HC-SR04 초음파 센서를 사용하여 거리를 측정하고, Python 백엔드에서 호출할 수 있는 함수를 제공합니다.

## HC-SR04 초음파 센서 작동 원리

HC-SR04는 초음파를 사용하여 거리를 측정하는 센서입니다:

1. **트리거 신호**: Trig 핀에 10마이크로초 이상의 HIGH 신호를 보냅니다.
2. **초음파 발사**: 센서가 40kHz 초음파를 발사합니다.
3. **반사 신호 수신**: 물체에 반사된 초음파를 Echo 핀으로 받습니다.
4. **시간 측정**: 발사부터 수신까지의 시간을 측정합니다.
5. **거리 계산**: `거리 = (시간 × 음속) / 2` 공식으로 거리를 계산합니다.

## 센서 연결

HC-SR04를 Arduino UNO Q에 다음과 같이 연결합니다:

| HC-SR04 핀 | Arduino UNO Q 핀 | 설명 |
|-----------|-----------------|------|
| VCC | 5V | 전원 (5V) |
| GND | GND | 그라운드 |
| Trig | D2 | 트리거 신호 (출력) |
| Echo | D3 | 에코 신호 (입력) |

**주의사항:**
- VCC는 반드시 5V에 연결해야 합니다 (3.3V는 작동하지 않을 수 있습니다).
- Echo 핀은 5V 신호를 출력하지만, Arduino UNO Q의 디지털 핀은 5V를 허용합니다.

## 스케치 코드 작성

**파일 위치:** `black-ice-detector/sketch/sketch.ino`

### 전체 코드

```cpp
// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

#include <Arduino_RouterBridge.h>

// HC-SR04 Ultrasonic Sensor Pin Configuration
const int TRIG_PIN = 2;  // 트리거 핀
const int ECHO_PIN = 3;  // 에코 핀

// Speed of sound in cm/us (at 20°C)
const float SOUND_SPEED = 0.034;

// Maximum distance to measure (in cm)
const float MAX_DISTANCE = 400.0;

// Minimum distance to measure (in cm)
const float MIN_DISTANCE = 2.0;

void setup() {
    Serial.begin(9600);
    
    // Configure pins
    pinMode(TRIG_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    
    // Initialize trigger pin to LOW
    digitalWrite(TRIG_PIN, LOW);
    
    Bridge.begin();
    
    // Provide function to Python backend
    Bridge.provide("get_distance", get_distance);
    
    Serial.println("Black Ice Detector initialized");
}

void loop() {
    // Main loop is handled by Bridge
    delay(100);
}

// Function to measure distance using HC-SR04
float get_distance() {
    // Clear the trigger pin
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    
    // Send 10 microsecond pulse to trigger pin
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    
    // Read the echo pin, returns the sound wave travel time in microseconds
    long duration = pulseIn(ECHO_PIN, HIGH, 30000); // Timeout after 30ms
    
    // Calculate distance
    // Distance = (Time * Speed of sound) / 2
    // Divide by 2 because sound travels to object and back
    float distance = (duration * SOUND_SPEED) / 2.0;
    
    // Validate distance reading
    if (distance < MIN_DISTANCE || distance > MAX_DISTANCE || duration == 0) {
        return -1.0; // Invalid reading
    }
    
    return distance;
}
```

## 코드 설명

### 1. 헤더 및 상수 정의

```cpp
#include <Arduino_RouterBridge.h>
```

- `Arduino_RouterBridge.h`: Python 백엔드와 통신하기 위한 Bridge 라이브러리

```cpp
const int TRIG_PIN = 2;
const int ECHO_PIN = 3;
```

- 센서 연결 핀 번호 정의

```cpp
const float SOUND_SPEED = 0.034;
```

- 음속 상수 (20°C 기준, cm/마이크로초)
- 공식: 340 m/s = 0.034 cm/μs

### 2. setup() 함수

```cpp
pinMode(TRIG_PIN, OUTPUT);
pinMode(ECHO_PIN, INPUT);
```

- Trig 핀을 출력으로 설정 (초음파 발사 신호)
- Echo 핀을 입력으로 설정 (반사 신호 수신)

```cpp
Bridge.begin();
Bridge.provide("get_distance", get_distance);
```

- Bridge 초기화
- Python에서 호출할 수 있도록 `get_distance` 함수 제공

### 3. get_distance() 함수

이 함수는 HC-SR04 센서로 거리를 측정합니다:

1. **트리거 신호 전송**
   ```cpp
   digitalWrite(TRIG_PIN, LOW);
   delayMicroseconds(2);
   digitalWrite(TRIG_PIN, HIGH);
   delayMicroseconds(10);
   digitalWrite(TRIG_PIN, LOW);
   ```
   - Trig 핀에 10마이크로초 HIGH 펄스 전송

2. **에코 신호 측정**
   ```cpp
   long duration = pulseIn(ECHO_PIN, HIGH, 30000);
   ```
   - Echo 핀에서 HIGH 신호의 지속 시간 측정 (마이크로초)
   - 최대 30ms 대기 (약 5m 거리)

3. **거리 계산**
   ```cpp
   float distance = (duration * SOUND_SPEED) / 2.0;
   ```
   - 시간 × 음속으로 거리 계산
   - 2로 나누는 이유: 초음파가 물체까지 갔다가 돌아오므로

4. **유효성 검사**
   ```cpp
   if (distance < MIN_DISTANCE || distance > MAX_DISTANCE || duration == 0) {
       return -1.0;
   }
   ```
   - 측정 범위를 벗어나거나 오류가 있으면 -1 반환

## 테스트

### 시리얼 모니터로 테스트

스케치를 업로드한 후 시리얼 모니터를 열어 센서가 작동하는지 확인합니다:

1. Arduino IDE에서 시리얼 모니터 열기 (115200 baud)
2. "Black Ice Detector initialized" 메시지 확인
3. 센서 앞에 물체를 두고 거리 값이 출력되는지 확인

### Bridge 통신 테스트

Python 백엔드에서 `Bridge.call("get_distance")`를 호출하여 거리 값을 읽을 수 있는지 확인합니다.

## 커스터마이징

### 핀 번호 변경

다른 핀을 사용하려면 다음을 수정합니다:

```cpp
const int TRIG_PIN = 4;  // 원하는 핀 번호
const int ECHO_PIN = 5;  // 원하는 핀 번호
```

### 측정 범위 변경

```cpp
const float MAX_DISTANCE = 500.0;  // 최대 거리 (cm)
const float MIN_DISTANCE = 1.0;     // 최소 거리 (cm)
```

### 타임아웃 조정

더 먼 거리를 측정하려면 타임아웃을 늘립니다:

```cpp
long duration = pulseIn(ECHO_PIN, HIGH, 50000); // 50ms 타임아웃
```

## 문제 해결

### 항상 -1이 반환됨

**원인:**
- 센서 연결 오류
- 측정 범위를 벗어남
- 센서 손상

**해결:**
1. 연결 확인: VCC, GND, Trig, Echo 핀 확인
2. 거리 확인: 센서 앞 2cm ~ 400cm 범위에 물체가 있는지 확인
3. 센서 교체: 다른 센서로 테스트

### 거리 값이 부정확함

**원인:**
- 온도 변화 (음속은 온도에 따라 변함)
- 센서 정렬 문제
- 주변 반사

**해결:**
1. 온도 보정: 온도에 따른 음속 보정 공식 사용
2. 센서 정렬: 센서가 물체를 정확히 향하도록 조정
3. 환경 확인: 주변 반사 물체 제거

## 다음 단계

Arduino 스케치가 완성되었으므로 다음 단계로 진행합니다:

- [3단계: Python 백엔드 작성](03-Python-백엔드-작성.md) - Bridge를 통한 거리 값 읽기 및 WebSocket 통신

## 체크리스트

- [ ] HC-SR04 센서 연결 완료
- [ ] 스케치 코드 작성 완료
- [ ] Bridge 통신 설정 완료
- [ ] 시리얼 모니터로 테스트 완료

