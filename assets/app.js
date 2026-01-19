// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

const socket = io(`http://${window.location.host}`);
let errorContainer = document.getElementById('errorContainer');

// DOM elements
const distanceValueEl = document.getElementById('distanceValue');
const distanceStatusEl = document.getElementById('distanceStatus');
const statusIndicatorEl = document.getElementById('statusIndicator');
const statusTextEl = document.getElementById('statusText');
const ldrValueEl = document.getElementById('ldrValue');
const temperatureInputEl = document.getElementById('temperatureInput');
const humidityInputEl = document.getElementById('humidityInput');
const locationInputEl = document.getElementById('locationInput');
const measureButtonEl = document.getElementById('measureButton');
const measurementStatusEl = document.getElementById('measurementStatus');
const avgDistanceEl = document.getElementById('avgDistance');
const avgLdrEl = document.getElementById('avgLdr');
const avgTempEl = document.getElementById('avgTemp');
const avgHumidityEl = document.getElementById('avgHumidity');
const avgLocationEl = document.getElementById('avgLocation');
const measurementDurationLabelEl = document.getElementById('measurementDurationLabel');

// Connection status
let isConnected = false;
let lastUpdateTime = null;
let isMeasuring = false;
let measurementDurationSec = null;
let countdownIntervalId = null;
let measurementEndTime = null;
let measurementSamplesInfo = null;

// 마지막으로 측정된 유효한 거리 값 저장
let lastValidDistance = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, initializing...');
    initSocketIO();
    updateConnectionStatus(false);

    if (measureButtonEl) {
        measureButtonEl.addEventListener('click', handleMeasurementRequest);
    }
    
    // 디버깅: DOM 요소 확인
    if (!distanceValueEl) {
        console.error('distanceValueEl not found!');
    }
    if (!statusIndicatorEl) {
        console.error('statusIndicatorEl not found!');
    }
    if (!statusTextEl) {
        console.error('statusTextEl not found!');
    }
    if (!ldrValueEl) {
        console.error('ldrValueEl not found!');
    }
    if (!measureButtonEl) {
        console.error('measureButtonEl not found!');
    }
    if (!locationInputEl) {
        console.error('locationInputEl not found!');
    }
    if (measurementDurationLabelEl) {
        const initialDuration = parseInt(measurementDurationLabelEl.textContent, 10);
        if (!Number.isNaN(initialDuration)) {
            measurementDurationSec = initialDuration;
        }
    }
});

function initSocketIO() {
    console.log('Initializing Socket.IO connection...');
    console.log('Socket URL:', `http://${window.location.host}`);
    
    socket.on('connect', () => {
        console.log('✅ Connected to server');
        isConnected = true;
        updateConnectionStatus(true);
        if (errorContainer) {
            errorContainer.style.display = 'none';
            errorContainer.textContent = '';
        }
        
        // Request initial distance reading
        console.log('Requesting initial distance reading...');
        socket.emit('client_connected', {});
    });
    
    socket.on('connect_error', (error) => {
        console.error('❌ Connection error:', error);
        isConnected = false;
        updateConnectionStatus(false);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        isConnected = false;
        updateConnectionStatus(false);
        if (errorContainer) {
            errorContainer.textContent = '서버 연결이 끊어졌습니다. 연결을 확인하세요.';
            errorContainer.style.display = 'block';
        }
    });

    socket.on('distance_update', (data) => {
        console.log('Received distance_update:', data);
        updateDistanceDisplay(data);
    });

    socket.on('config', (data) => {
        if (!data) {
            return;
        }
        updateConfigDisplay(data);
    });

    socket.on('measurement_status', (data) => {
        if (!data) {
            return;
        }
        updateMeasurementStatus(data);
    });

    socket.on('measurement_result', (data) => {
        if (!data) {
            return;
        }
        updateMeasurementResult(data);
    });

    socket.on('error', (error) => {
        console.error('Server error:', error);
        if (errorContainer) {
            errorContainer.textContent = '오류: ' + error;
            errorContainer.style.display = 'block';
        }
    });
}

function updateConfigDisplay(data) {
    if (measurementDurationLabelEl && typeof data.measurement_duration === 'number') {
        measurementDurationSec = Math.round(data.measurement_duration);
        measurementDurationLabelEl.textContent = measurementDurationSec;
    }
}

function handleMeasurementRequest() {
    if (isMeasuring) {
        return;
    }

    const tempValue = parseFloat(temperatureInputEl?.value);
    const humidityValue = parseFloat(humidityInputEl?.value);
    const locationValue = parseInt(locationInputEl?.value, 10);

    if (Number.isNaN(tempValue) || Number.isNaN(humidityValue) || Number.isNaN(locationValue)) {
        showError('온도, 습도, 위치 번호를 숫자로 입력하세요.');
        return;
    }

    if (humidityValue < 0 || humidityValue > 100) {
        showError('습도는 0~100 범위로 입력하세요.');
        return;
    }

    clearError();
    setMeasurementBusy(true, '측정 요청 중...');

    socket.emit('measurement_request', {
        temperature: tempValue,
        humidity: humidityValue,
        location: locationValue
    });
}

function updateMeasurementStatus(data) {
    const state = data.state;
    const remaining = data.remaining_seconds;
    const samplesTaken = data.samples_taken;
    const samplesTotal = data.samples_total;

    if (state === 'started') {
        const durationText = typeof measurementDurationSec === 'number'
            ? `${measurementDurationSec}초 소요`
            : '측정 중...';
        setMeasurementBusy(true, `측정 중... (${durationText})`);
        startCountdown(remaining, samplesTaken, samplesTotal);
    } else if (state === 'progress') {
        startCountdown(remaining, samplesTaken, samplesTotal);
    } else if (state === 'completed') {
        stopCountdown();
        setMeasurementBusy(false, '측정 완료');
    } else if (state === 'error') {
        stopCountdown();
        setMeasurementBusy(false, data.message || '측정 실패');
    }
}

function updateMeasurementResult(data) {
    const distance = data.distance_cm_avg;
    const ldr = data.ldr_avg;
    const temperature = data.temperature;
    const humidity = data.humidity;
    const location = data.location;

    if (typeof distance === 'number' && distance >= 0) {
        avgDistanceEl.textContent = distance.toFixed(2);
    } else {
        avgDistanceEl.textContent = '--';
    }

    if (typeof ldr === 'number' && ldr >= 0) {
        avgLdrEl.textContent = Math.round(ldr);
    } else {
        avgLdrEl.textContent = '--';
    }

    if (typeof temperature === 'number') {
        avgTempEl.textContent = temperature.toFixed(1);
    } else {
        avgTempEl.textContent = '--';
    }

    if (typeof humidity === 'number') {
        avgHumidityEl.textContent = humidity.toFixed(1);
    } else {
        avgHumidityEl.textContent = '--';
    }

    if (typeof location === 'number') {
        avgLocationEl.textContent = location.toString();
    } else if (typeof location === 'string') {
        avgLocationEl.textContent = location;
    } else {
        avgLocationEl.textContent = '--';
    }

    setMeasurementBusy(false, '측정 완료');
}

function startCountdown(remainingSeconds, samplesTaken, samplesTotal) {
    if (typeof remainingSeconds === 'number') {
        measurementEndTime = Date.now() + remainingSeconds * 1000;
    }
    measurementSamplesInfo = {
        samplesTaken,
        samplesTotal
    };

    if (countdownIntervalId) {
        return;
    }

    countdownIntervalId = setInterval(() => {
        if (!measurementEndTime || !measurementStatusEl) {
            return;
        }
        const remainingMs = Math.max(0, measurementEndTime - Date.now());
        const remainingSec = Math.ceil(remainingMs / 1000);
        const samplesText = measurementSamplesInfo &&
            typeof measurementSamplesInfo.samplesTaken === 'number' &&
            typeof measurementSamplesInfo.samplesTotal === 'number'
            ? ` (${measurementSamplesInfo.samplesTaken}/${measurementSamplesInfo.samplesTotal})`
            : '';
        setMeasurementBusy(true, `${remainingSec}초 남음${samplesText}`);
        if (remainingSec <= 0) {
            stopCountdown();
        }
    }, 250);
}

function stopCountdown() {
    if (countdownIntervalId) {
        clearInterval(countdownIntervalId);
        countdownIntervalId = null;
    }
    measurementEndTime = null;
    measurementSamplesInfo = null;
}

function setMeasurementBusy(isBusy, statusText) {
    isMeasuring = isBusy;
    if (measureButtonEl) {
        measureButtonEl.disabled = isBusy;
        measureButtonEl.textContent = isBusy ? '측정 중...' : '측정';
    }
    if (measurementStatusEl && statusText) {
        measurementStatusEl.textContent = statusText;
    }
}

function showError(message) {
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
    }
}

function clearError() {
    if (errorContainer) {
        errorContainer.textContent = '';
        errorContainer.style.display = 'none';
    }
}

function updateDistanceDisplay(data) {
    if (!data) {
        console.log('No data received');
        return;
    }

    console.log('Updating display with data:', data);
    const distance = data.distance;
    const isValid = data.valid !== false && distance > 0;

    // Update distance value (distance_mm을 cm로 변환한 값 표시)
    if (isValid) {
        // 유효한 값이면 저장하고 표시
        lastValidDistance = distance;
        distanceValueEl.textContent = distance.toFixed(2);  // cm 단위, 소수점 2자리 표시
        distanceValueEl.classList.remove('invalid');
        
        // Update status
        statusIndicatorEl.className = 'status-indicator active';
        statusTextEl.textContent = '정상 측정 중';
    } else {
        // 유효하지 않은 값(-1)이 들어왔을 때
        if (lastValidDistance !== null) {
            // 이전에 유효한 값이 있으면 그 값을 유지
            distanceValueEl.textContent = lastValidDistance.toFixed(2);
            distanceValueEl.classList.remove('invalid');
            statusIndicatorEl.className = 'status-indicator warning';
            statusTextEl.textContent = '측정 중... (이전 값 표시)';
        } else {
            // 이전 값이 없으면 -- 표시
            distanceValueEl.textContent = '--';
            distanceValueEl.classList.add('invalid');
            statusIndicatorEl.className = 'status-indicator error';
            statusTextEl.textContent = '측정 범위를 벗어났습니다';
        }
    }

    // Update LDR value
    if (data.ldr_value !== undefined && data.ldr_value >= 0) {
        ldrValueEl.textContent = data.ldr_value;
        ldrValueEl.classList.remove('invalid');
    } else {
        ldrValueEl.textContent = '--';
        ldrValueEl.classList.add('invalid');
    }

    lastUpdateTime = Date.now();

    // Check for stale data (no update for 2 seconds)
    setTimeout(() => {
        const timeSinceUpdate = Date.now() - lastUpdateTime;
        if (timeSinceUpdate > 2000 && isConnected) {
            if (lastValidDistance !== null) {
                // 이전 값이 있으면 경고만 표시
                statusIndicatorEl.className = 'status-indicator warning';
                statusTextEl.textContent = '데이터 업데이트 대기 중... (이전 값 표시)';
            } else {
                statusIndicatorEl.className = 'status-indicator warning';
                statusTextEl.textContent = '데이터 업데이트 대기 중...';
            }
        }
    }, 2000);
}

function updateConnectionStatus(connected) {
    if (connected) {
        statusIndicatorEl.className = 'status-indicator active';
        statusTextEl.textContent = '연결됨';
    } else {
        statusIndicatorEl.className = 'status-indicator error';
        statusTextEl.textContent = '연결 끊김';
        // 연결이 끊겨도 이전 값이 있으면 유지
        if (lastValidDistance !== null) {
            distanceValueEl.textContent = lastValidDistance.toFixed(2);
            distanceValueEl.classList.remove('invalid');
        } else {
            distanceValueEl.textContent = '--';
            distanceValueEl.classList.add('invalid');
        }
    }
}

