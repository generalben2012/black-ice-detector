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

