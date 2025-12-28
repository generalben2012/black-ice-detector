// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

#include "pulseInCustom.h"

// micros() 오버플로우를 고려한 안전한 시간 차이 계산
unsigned long safeMicrosDiff(unsigned long start, unsigned long end) {
  if (end >= start) {
    return end - start;
  } else {
    // 오버플로우 발생: (ULONG_MAX - start) + end + 1
    return (ULONG_MAX - start) + end + 1;
  }
}

// pulseIn 함수를 직접 구현 (Zephyr 플랫폼용)
// timeout은 선택적 파라미터 (기본값: 1000000us = 1초)
unsigned long pulseInCustom(uint8_t pin, uint8_t state, unsigned long timeout) {
  unsigned long timeoutMicros = timeout; // 이미 마이크로초 단위
  unsigned long overallStart = micros();

  // 먼저 핀이 반대 상태인지 확인하고 기다림
  unsigned long waitStart = micros();
  while (digitalRead(pin) == state) {
    unsigned long current = micros();
    unsigned long elapsed = safeMicrosDiff(waitStart, current);
    if (elapsed > timeoutMicros) {
      return 0; // Timeout - 핀이 계속 같은 상태
    }
    // 전체 타임아웃도 확인
    unsigned long overallElapsed = safeMicrosDiff(overallStart, current);
    if (overallElapsed > timeoutMicros) {
      return 0; // Overall timeout
    }
  }

  // 핀이 원하는 상태로 변할 때까지 대기
  waitStart = micros();
  while (digitalRead(pin) != state) {
    unsigned long current = micros();
    unsigned long elapsed = safeMicrosDiff(waitStart, current);
    if (elapsed > timeoutMicros) {
      return 0; // Timeout - 핀이 변하지 않음
    }
    // 전체 타임아웃도 확인
    unsigned long overallElapsed = safeMicrosDiff(overallStart, current);
    if (overallElapsed > timeoutMicros) {
      return 0; // Overall timeout
    }
  }

  // 펄스 시작 시간 기록
  unsigned long pulseStart = micros();

  // 펄스가 끝날 때까지 대기
  while (digitalRead(pin) == state) {
    unsigned long current = micros();
    unsigned long elapsed = safeMicrosDiff(pulseStart, current);
    if (elapsed > timeoutMicros) {
      return 0; // Timeout - 펄스가 너무 김
    }
    // 전체 타임아웃도 확인
    unsigned long overallElapsed = safeMicrosDiff(overallStart, current);
    if (overallElapsed > timeoutMicros) {
      return 0; // Overall timeout
    }
  }

  // 펄스 종료 시간
  unsigned long pulseEnd = micros();

  // 펄스 길이 계산 (오버플로우 고려)
  return safeMicrosDiff(pulseStart, pulseEnd);
}

