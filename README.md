# Black Ice Detector

Arduino UNO Q와 각종 센서를 사용하여 블랙아이스를 감지하고 웹 인터페이스에 표시하는 프로젝트입니다.


## 프로젝트 개요

이 프로젝트는 각종 센서를 사용하여 도로 표면의 Black Ice를 찾아 내고, Arduino UNO Q의 Bridge 기능을 통해 Python 백엔드로 데이터를 전송하며, 웹 인터페이스를 통해 블랙아이스 감지 상태를 실시간으로 표시합니다.

### 주요 기능

- **블랙아이스 감지**: 각종종 센서를 사용하여 도로 표면과의 거리를 측정하여 블랙아이스 감지
- **웹 인터페이스**: 실시간으로 거리 값과 감지 상태를 웹 브라우저에 표시
- **자동 업데이트**: 100ms마다 거리 값 자동 업데이트 (초당 10회)
- **연결 상태 표시**: 센서 연결 상태 및 측정 상태를 시각적으로 표시

## 하드웨어 요구사항

- **Arduino UNO Q** (x1)
- **HC-SR04 초음파 센서** (x1)
- **점퍼 와이어** (x4)
- **USB-C 케이블** (전원 및 프로그래밍용)

## 소프트웨어 요구사항

- Arduino App Lab

## 센서 연결 방법

HC-SR04 초음파 센서를 Arduino UNO Q에 다음과 같이 연결합니다:
**아래 표가 마크다운 표 형식에 맞게 잘 만들어졌습니다.**

| HC-SR04 핀 | Arduino UNO Q 핀 | 설명        |
|------------|-----------------|-------------|
| VCC        | 5V              | 전원 공급   |
| GND        | GND             | 그라운드    |
| Trig       | D2              | 트리거 신호 (출력) |
| Echo       | D3              | 에코 신호 (입력)  |



### 연결 다이어그램

```
HC-SR04                    Arduino UNO Q
┌─────────┐                ┌──────────┐
│  VCC    │───────────────▶│   5V     │
│  GND    │───────────────▶│   GND    │
│  Trig   │───────────────▶│   D2     │
│  Echo   │───────────────▶│   D3     │
└─────────┘                └──────────┘
```

## 사용 방법

1. **하드웨어 연결**
   - 위의 연결 방법에 따라 HC-SR04 센서를 Arduino UNO Q에 연결합니다.

2. **앱 실행**
   - Arduino App Lab에서 이 프로젝트를 엽니다.
   - "Run App" 버튼을 클릭하여 앱을 실행합니다.

3. **웹 인터페이스 접속**
   - 앱이 자동으로 웹 브라우저를 엽니다.
   - 또는 수동으로 `<board-name>.local:7000`으로 접속할 수 있습니다.

4. **거리 측정 확인**
   - 센서 앞에 물체를 두면 실시간으로 거리가 표시됩니다.
   - 거리는 센티미터(cm) 단위로 표시됩니다.

## 프로젝트 구조

```
black-ice-detector/
├── app.yaml              # 앱 설정 파일
├── python/
│   └── main.py          # Python 백엔드 (Bridge 통신)
├── sketch/
│   └── sketch.ino       # Arduino 스케치 (센서 제어)
├── assets/
│   ├── index.html        # 웹 인터페이스 HTML
│   ├── app.js           # 웹 인터페이스 JavaScript
│   ├── style.css        # 웹 인터페이스 스타일
│   └── libs/
│       └── socket.io.min.js  # WebSocket 라이브러리
└── README.md            # 프로젝트 설명서
```

## 작동 원리

### 1. Arduino 스케치 (`sketch.ino`)

Arduino 스케치는 HC-SR04 센서를 제어하고 거리를 측정합니다:

- **트리거 신호**: D2 핀으로 10마이크로초 펄스를 보냅니다.
- **에코 신호**: D3 핀에서 반사된 신호의 시간을 측정합니다.
- **거리 계산**: `거리 = (시간 × 음속) / 2` 공식을 사용하여 거리를 계산합니다.
- **Bridge 통신**: Python 백엔드에서 호출할 수 있도록 `get_distance()` 함수를 제공합니다.

### 2. Python 백엔드 (`main.py`)

Python 백엔드는 Bridge를 통해 Arduino에서 거리 값을 읽고 웹 클라이언트에 전송합니다:

- **Bridge 통신**: `Bridge.call("get_distance")`를 사용하여 Arduino에서 거리 값을 읽습니다.
- **WebSocket 통신**: `WebUI` Brick을 사용하여 웹 클라이언트와 실시간 통신합니다.
- **자동 업데이트**: 100ms마다 거리 값을 읽어 웹 클라이언트에 전송합니다.

### 3. 웹 인터페이스 (`index.html`, `app.js`, `style.css`)

웹 인터페이스는 WebSocket을 통해 실시간으로 거리 값을 받아 표시합니다:

- **WebSocket 연결**: Socket.IO를 사용하여 Python 백엔드에 연결합니다.
- **실시간 업데이트**: `distance_update` 이벤트를 받아 거리 값을 업데이트합니다.
- **상태 표시**: 연결 상태 및 측정 상태를 시각적으로 표시합니다.

## 커스터마이징

### 측정 범위 변경

`sketch.ino` 파일에서 다음 상수를 수정할 수 있습니다:

```cpp
const float MAX_DISTANCE = 400.0;  // 최대 측정 거리 (cm)
const float MIN_DISTANCE = 2.0;     // 최소 측정 거리 (cm)
```

### 업데이트 주기 변경

`python/main.py` 파일에서 다음 상수를 수정할 수 있습니다:

```python
UPDATE_INTERVAL = 0.1  # 업데이트 주기 (초)
```

### 핀 번호 변경

`sketch.ino` 파일에서 다음 상수를 수정할 수 있습니다:

```cpp
const int TRIG_PIN = 2;  // 트리거 핀
const int ECHO_PIN = 3;  // 에코 핀
```

## 문제 해결

### 거리 값이 표시되지 않음

1. 센서 연결 확인: VCC, GND, Trig, Echo 핀이 올바르게 연결되었는지 확인합니다.
2. 전원 확인: 센서에 5V 전원이 공급되고 있는지 확인합니다.
3. 센서 위치 확인: 센서 앞에 물체가 2cm ~ 400cm 범위 내에 있는지 확인합니다.

### 연결 오류

1. Arduino UNO Q 연결 확인: USB 케이블이 올바르게 연결되었는지 확인합니다.
2. 앱 재시작: Arduino App Lab에서 앱을 재시작합니다.
3. 브라우저 콘솔 확인: 브라우저 개발자 도구의 콘솔에서 오류 메시지를 확인합니다.

### 측정 값이 부정확함

1. 센서 정렬 확인: 센서가 물체를 정확히 향하고 있는지 확인합니다.
2. 환경 확인: 센서 주변에 반사되는 물체가 없는지 확인합니다.
3. 센서 교체: 센서가 손상되었을 수 있으므로 다른 센서로 교체해봅니다.

## 참고 자료

- [Arduino UNO Q 공식 문서](https://docs.arduino.cc/hardware/uno-q)
- [HC-SR04 초음파 센서 데이터시트](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf)
- [Arduino App Lab 문서](https://docs.arduino.cc/arduino-cloud/app-lab)

## 라이선스

SPDX-License-Identifier: MPL-2.0

