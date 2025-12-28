#line 1 "/home/arduino/ArduinoApps/black-ice-detector/sketch/pulseInCustom.h"
// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

#ifndef PULSE_IN_CUSTOM_H
#define PULSE_IN_CUSTOM_H

#include <Arduino.h>

// micros() 오버플로우를 고려한 안전한 시간 차이 계산
unsigned long safeMicrosDiff(unsigned long start, unsigned long end);

// pulseIn 함수를 직접 구현 (Zephyr 플랫폼용)
// timeout은 선택적 파라미터 (기본값: 1000000us = 1초)
unsigned long pulseInCustom(uint8_t pin, uint8_t state, unsigned long timeout = 1000000);

#endif // PULSE_IN_CUSTOM_H
