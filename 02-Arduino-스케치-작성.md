# 2단계: Arduino 스케치 작성

이 문서는 HC-SR04 초음파 센서와 LDR 조도 센서를 제어하는 Arduino 스케치를 작성하는 방법을 설명합니다.

## 목표

- HC-SR04 초음파 센서를 사용하여 거리를 측정
- LDR 조도 센서를 사용하여 주변 밝기 측정
- Python 백엔드에서 호출할 수 있는 함수 제공

## 센서 개요

### HC-SR04 초음파 센서

HC-SR04는 초음파를 사용하여 거리를 측정하는 센서입니다:

1. **트리거 신호**: Trig 핀에 10마이크로초 이상의 HIGH 신호를 보냅니다.
2. **초음파 발사**: 센서가 40kHz 초음파를 발사합니다.
3. **반사 신호 수신**: 물체에 반사된 초음파를 Echo 핀으로 받습니다.
4. **시간 측정**: 발사부터 수신까지의 시간을 측정합니다.
5. **거리 계산**: `거리 = (시간 × 음속) / 2` 공식으로 거리를 계산합니다.

### LDR 조도 센서

LDR (Light Dependent Resistor)은 빛에 따라 저항이 변하는 센서입니다:

- **분압 회로**: LDR과 고정 저항(10kΩ)을 사용한 분압 회로로 구성
- **아날로그 읽기**: A1 핀에서 0~1023 범위의 값 읽기
- **값 해석**: 값이 클수록 밝고, 작을수록 어둡습니다

## 센서 연결

### HC-SR04 연결

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

### LDR 조도 센서 연결

LDR 조도 센서는 분압 회로로 구성합니다:

**회로 구성:**
```
5V ──[LDR]──┬──[10kΩ 저항]── GND
             │
            A1
```

**연결 방법:**
1. LDR의 한쪽을 5V에 연결
2. LDR의 다른 쪽을 10kΩ 저항과 연결
3. LDR과 저항의 중간점을 A1에 연결
4. 10kΩ 저항의 다른 쪽을 GND에 연결

**주의사항:**
- Arduino UNO Q에서는 아날로그 핀에 `pinMode()`를 설정하지 않아야 합니다.
- 저항 값은 10kΩ을 권장합니다 (다른 값도 가능하지만 측정 범위가 달라집니다).

## 스케치 코드 작성

**파일 위치:** `black-ice-detector/sketch/sketch.ino`

### 전체 코드

```cpp
#include <Arduino_RouterBridge.h>
#include "pulseInCustom.h"

#define TRIG_PIN 2
#define ECHO_PIN 3
#define LDR_PIN A1          // 조도 센서 입력 (LDR 분압 노드)

// 최신 측정값 저장
long latest_duration = 0;
float latest_distance_mm = 0.0;
int latest_ldr_value = 0;

// Bridge를 통해 Python에서 호출할 함수들
long get_duration() {
  return latest_duration;
}

float get_distance_mm() {
  return latest_distance_mm;
}

int get_ldr_value() {
  return latest_ldr_value;
}

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  // 아날로그 핀(A1)은 pinMode 설정 불필요 (일부 보드에서는 설정 시 문제 발생)

  Serial.begin(9600);

  // Bridge 초기화
  Bridge.begin();

  // Python 백엔드에서 호출할 수 있도록 함수 제공
  Bridge.provide("get_duration", get_duration);
  Bridge.provide("get_distance_mm", get_distance_mm);
  Bridge.provide("get_ldr_value", get_ldr_value);
}

void loop() {
  long duration;
  float distance_mm;

  // Trig 핀 초기화
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  // 10us 펄스 출력
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Echo 핀에서 펄스 길이 측정 (Zephyr용 pulseInCustom 사용)
  duration = pulseInCustom(ECHO_PIN, HIGH, 30000); // 30ms 타임아웃

  // 거리 계산 (mm)
  distance_mm = duration * 0.343 / 2;

  // 최신 측정값 저장
  latest_duration = duration;
  latest_distance_mm = distance_mm;

  // 조도 센서 읽기
  int ldrValue = analogRead(LDR_PIN);
  latest_ldr_value = ldrValue;

  // 시리얼 출력
  Serial.print("Distance: ");
  Serial.print(distance_mm);
  Serial.print(" mm (");
  Serial.print(distance_mm / 10.0);
  Serial.print(" cm), Duration: ");
  Serial.print(duration);
  Serial.print(" us, LDR: ");
  Serial.print(ldrValue);
  Serial.print(" (");
  Serial.print((ldrValue * 100) / 1023);
  Serial.println("%)");

  delay(200);
}
```

## 코드 설명

### 1. 헤더 및 상수 정의

```cpp
#include <Arduino_RouterBridge.h>
#include "pulseInCustom.h"
```

- `Arduino_RouterBridge.h`: Python 백엔드와 통신하기 위한 Bridge 라이브러리
- `pulseInCustom.h`: Zephyr 플랫폼용 pulseIn 함수 (별도 파일)

```cpp
#define TRIG_PIN 2
#define ECHO_PIN 3
#define LDR_PIN A1
```

- 센서 연결 핀 번호 정의

### 2. 전역 변수

```cpp
long latest_duration = 0;
float latest_distance_mm = 0.0;
int latest_ldr_value = 0;
```

- 최신 측정값을 저장하는 전역 변수
- Python에서 Bridge를 통해 읽을 수 있도록 저장

### 3. Bridge 함수

```cpp
long get_duration() {
  return latest_duration;
}

float get_distance_mm() {
  return latest_distance_mm;
}

int get_ldr_value() {
  return latest_ldr_value;
}
```

- Python에서 호출할 수 있는 함수들
- 각각 duration, distance_mm, ldr_value를 반환

### 4. setup() 함수

```cpp
pinMode(TRIG_PIN, OUTPUT);
pinMode(ECHO_PIN, INPUT);
// 아날로그 핀(A1)은 pinMode 설정 불필요
```

- Trig 핀을 출력으로 설정 (초음파 발사 신호)
- Echo 핀을 입력으로 설정 (반사 신호 수신)
- 아날로그 핀은 pinMode 설정 불필요 (Arduino UNO Q 특성)

```cpp
Bridge.begin();
Bridge.provide("get_duration", get_duration);
Bridge.provide("get_distance_mm", get_distance_mm);
Bridge.provide("get_ldr_value", get_ldr_value);
```

- Bridge 초기화
- Python에서 호출할 수 있도록 함수 제공

### 5. loop() 함수

#### HC-SR04 센서 읽기

```cpp
// Trig 핀 초기화
digitalWrite(TRIG_PIN, LOW);
delayMicroseconds(2);

// 10us 펄스 출력
digitalWrite(TRIG_PIN, HIGH);
delayMicroseconds(10);
digitalWrite(TRIG_PIN, LOW);

// Echo 핀에서 펄스 길이 측정
duration = pulseInCustom(ECHO_PIN, HIGH, 30000); // 30ms 타임아웃

// 거리 계산 (mm)
distance_mm = duration * 0.343 / 2;
```

- Trig 핀에 10마이크로초 HIGH 펄스 전송
- Echo 핀에서 HIGH 신호의 지속 시간 측정 (마이크로초)
- 최대 30ms 대기 (약 5m 거리)
- 시간 × 음속으로 거리 계산 (mm 단위)
- 2로 나누는 이유: 초음파가 물체까지 갔다가 돌아오므로

#### LDR 센서 읽기

```cpp
int ldrValue = analogRead(LDR_PIN);
latest_ldr_value = ldrValue;
```

- A1 핀에서 아날로그 값 읽기 (0~1023)
- 전역 변수에 저장하여 Bridge로 제공

## pulseInCustom 함수

Zephyr RTOS를 사용하는 Arduino UNO Q에서는 표준 `pulseIn()` 함수가 작동하지 않을 수 있으므로, `pulseInCustom()` 함수를 별도 파일로 구현합니다.

**파일 위치:** `sketch/pulseInCustom.h`, `sketch/pulseInCustom.cpp`

이 함수는 `pulseInCustom.h`에 선언되어 있고, `pulseInCustom.cpp`에 구현되어 있습니다.

## 테스트

### 시리얼 모니터로 테스트

스케치를 업로드한 후 시리얼 모니터를 열어 센서가 작동하는지 확인합니다:

1. Arduino App Lab에서 시리얼 모니터 열기 (9600 baud)
2. 센서 앞에 물체를 두고 거리 값이 출력되는지 확인
3. 빛을 가리거나 밝히면 LDR 값이 변하는지 확인

**예상 출력:**
```
Distance: 250.0 mm (25.0 cm), Duration: 1457 us, LDR: 512 (50%)
```

### Bridge 통신 테스트

Python 백엔드에서 다음 함수들을 호출하여 값을 읽을 수 있는지 확인합니다:

- `Bridge.call("get_duration")`
- `Bridge.call("get_distance_mm")`
- `Bridge.call("get_ldr_value")`

## 커스터마이징

### 핀 번호 변경

다른 핀을 사용하려면 다음을 수정합니다:

```cpp
#define TRIG_PIN 4   // 원하는 핀 번호
#define ECHO_PIN 5   // 원하는 핀 번호
#define LDR_PIN A2   // 원하는 아날로그 핀
```

### 타임아웃 조정

더 먼 거리를 측정하려면 타임아웃을 늘립니다:

```cpp
duration = pulseInCustom(ECHO_PIN, HIGH, 50000); // 50ms 타임아웃
```

### 루프 지연 조정

센서 읽기 주기를 변경하려면:

```cpp
delay(200);  // 200ms마다 읽기 (기본값)
delay(100);  // 100ms마다 읽기 (더 빠름)
delay(500);  // 500ms마다 읽기 (더 느림)
```

## 문제 해결

### 항상 duration이 0이 반환됨

**원인:**
- 센서 연결 오류
- 측정 범위를 벗어남
- 센서 손상

**해결:**
1. 연결 확인: VCC, GND, Trig, Echo 핀 확인
2. 거리 확인: 센서 앞 2cm ~ 400cm 범위에 물체가 있는지 확인
3. 센서 교체: 다른 센서로 테스트

### LDR 값이 변하지 않음

**원인:**
- 회로 구성 오류
- LDR 손상
- 저항 값 문제

**해결:**
1. 회로 확인: 분압 회로가 올바르게 구성되었는지 확인
2. 연결 확인: A1 핀이 올바르게 연결되었는지 확인
3. 저항 확인: 10kΩ 저항이 올바르게 연결되었는지 확인
4. LDR 교체: 다른 LDR로 테스트

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

- [3단계: Python 백엔드 작성](03-Python-백엔드-작성.md) - Bridge를 통한 센서 값 읽기 및 WebSocket 통신

## 체크리스트

- [ ] HC-SR04 센서 연결 완료
- [ ] LDR 센서 회로 구성 완료
- [ ] 스케치 코드 작성 완료
- [ ] Bridge 통신 설정 완료
- [ ] 시리얼 모니터로 테스트 완료
- [ ] LDR 값이 정상적으로 변하는지 확인 완료
