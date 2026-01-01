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

// Connection status
let isConnected = false;
let lastUpdateTime = null;

// 마지막으로 측정된 유효한 거리 값 저장
let lastValidDistance = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, initializing...');
    initSocketIO();
    updateConnectionStatus(false);
    
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

    socket.on('error', (error) => {
        console.error('Server error:', error);
        if (errorContainer) {
            errorContainer.textContent = '오류: ' + error;
            errorContainer.style.display = 'block';
        }
    });
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

