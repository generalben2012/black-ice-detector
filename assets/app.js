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
const avgBlackIceEl = document.getElementById('avgBlackIce');
const measurementDurationLabelEl = document.getElementById('measurementDurationLabel');
const cameraIframeEl = document.getElementById('dynamicIframe');
const cameraPlaceholderEl = document.getElementById('videoPlaceholder');
const locationSelectEl = document.getElementById('locationInput');

// Connection status
let isConnected = false;
let lastUpdateTime = null;
let isMeasuring = false;
let measurementDurationSec = null;
let countdownIntervalId = null;
let measurementEndTime = null;
let measurementSamplesInfo = null;
let distanceStatusMode = 'connecting';
let cameraStatusMode = 'connecting';
let cameraRetryState = { retryCount: 0, maxRetries: 0 };
let measurementStatusState = { mode: 'idle' };
let currentLang = 'en';
let locationEntries = null;
let locationLoadError = false;

// 마지막으로 측정된 유효한 거리 값 저장
let lastValidDistance = null;

const LANG_STORAGE_KEY = 'bid_lang';
const DEFAULT_LANG = 'en';
const I18N = {
    en: {
        page_title_main: 'Black Ice Detector',
        main_title: 'Black Ice Environment Monitor',
        results_button: 'View Results',
        results_hint: 'Open measurement history in a new tab.',
        distance_label: 'Distance',
        ldr_label: 'Light Sensor (LDR)',
        result_label_distance: 'Distance',
        result_label_ldr: 'Light',
        result_label_temp: 'Temperature',
        result_label_humidity: 'Humidity',
        result_label_location: 'Location',
        result_label_black_ice: 'Black Ice',
        input_title: 'Manual Input',
        input_temp_label: 'Temperature (°C)',
        input_temp_placeholder: 'e.g. 3.5',
        input_humidity_label: 'Humidity (%)',
        input_humidity_placeholder: 'e.g. 65',
        input_location_label: 'Location ID',
        input_location_placeholder: 'Select location...',
        input_location_none: 'No location data',
        input_location_load_fail: 'Failed to load locations.',
        location_option: 'Location {key}: {name}',
        input_black_ice_label: 'Black ice occurrence',
        radio_occurred: 'Occurred',
        radio_not_occurred: 'Not occurred',
        measure_button: 'Measure',
        measure_button_busy: 'Measuring...',
        measurement_status_idle: 'Idle',
        measurement_status_requesting: 'Requesting measurement...',
        measurement_status_measuring: 'Measuring... ({duration})',
        measurement_status_completed: 'Measurement complete',
        measurement_status_failed: 'Measurement failed',
        measurement_status_remaining: '{seconds}s remaining{samples}',
        measurement_duration_text: '{seconds}s',
        camera_label: 'Camera',
        camera_connecting: 'Connecting camera...',
        camera_not_found: 'Camera not found. Check USB camera and restart the app.',
        camera_retrying: 'Trying to connect camera... ({retry}/{max})',
        info_title: 'Sensor Info',
        info_sensor_model_label: 'Sensor model:',
        info_measure_range_label: 'Measurement range:',
        info_update_rate_label: 'Update rate:',
        connection_connected: 'Connected',
        connection_connecting: 'Connecting...',
        connection_disconnected: 'Disconnected',
        status_normal: 'Measuring normally',
        status_using_last: 'Measuring... (showing last value)',
        status_out_of_range: 'Out of measurement range',
        status_waiting_update: 'Waiting for data update...',
        status_waiting_update_last: 'Waiting for data update... (showing last value)',
        error_server_disconnected: 'Server connection lost. Check the connection.',
        error_prefix: 'Error: ',
        error_input_numbers: 'Enter temperature, humidity, and location as numbers.',
        error_humidity_range: 'Humidity must be between 0 and 100.',
        error_black_ice_required: 'Select black ice occurrence.',
        black_ice_occurred: 'Occurred',
        black_ice_not_occurred: 'Not occurred',
        measurement_result_title: 'Measurement result (avg {seconds}s)'
    },
    ko: {
        page_title_main: 'Black Ice Detector',
        main_title: '블랙 아이스(Black Ice) 발생 환경 측정기',
        results_button: '측정 결과 보기',
        results_hint: '새 탭에서 측정 기록을 확인합니다.',
        distance_label: '거리',
        ldr_label: '조도 센서 (LDR)',
        result_label_distance: '거리',
        result_label_ldr: '조도',
        result_label_temp: '온도',
        result_label_humidity: '습도',
        result_label_location: '위치',
        result_label_black_ice: '블랙 아이스',
        input_title: '수동 입력',
        input_temp_label: '온도 (°C)',
        input_temp_placeholder: '예: 3.5',
        input_humidity_label: '습도 (%)',
        input_humidity_placeholder: '예: 65',
        input_location_label: '위치 번호',
        input_location_placeholder: '위치 선택...',
        input_location_none: '위치 정보 없음',
        input_location_load_fail: '위치 정보를 불러오지 못했습니다.',
        location_option: '{key}번: {name}',
        input_black_ice_label: '블랙 아이스 발생 여부',
        radio_occurred: '발생',
        radio_not_occurred: '미발생',
        measure_button: '측정',
        measure_button_busy: '측정 중...',
        measurement_status_idle: '대기 중',
        measurement_status_requesting: '측정 요청 중...',
        measurement_status_measuring: '측정 중... ({duration})',
        measurement_status_completed: '측정 완료',
        measurement_status_failed: '측정 실패',
        measurement_status_remaining: '{seconds}초 남음{samples}',
        measurement_duration_text: '{seconds}초 소요',
        camera_label: '카메라',
        camera_connecting: '카메라 연결 중...',
        camera_not_found: '카메라를 찾을 수 없습니다. USB 카메라 연결과 앱 재시작을 확인하세요.',
        camera_retrying: '카메라 연결 시도 중... ({retry}/{max})',
        info_title: '센서 정보',
        info_sensor_model_label: '센서 모델:',
        info_measure_range_label: '측정 범위:',
        info_update_rate_label: '업데이트 주기:',
        connection_connected: '연결됨',
        connection_connecting: '센서 연결 중...',
        connection_disconnected: '연결 끊김',
        status_normal: '정상 측정 중',
        status_using_last: '측정 중... (이전 값 표시)',
        status_out_of_range: '측정 범위를 벗어났습니다',
        status_waiting_update: '데이터 업데이트 대기 중...',
        status_waiting_update_last: '데이터 업데이트 대기 중... (이전 값 표시)',
        error_server_disconnected: '서버 연결이 끊어졌습니다. 연결을 확인하세요.',
        error_prefix: '오류: ',
        error_input_numbers: '온도, 습도, 위치 번호를 숫자로 입력하세요.',
        error_humidity_range: '습도는 0~100 범위로 입력하세요.',
        error_black_ice_required: '블랙 아이스 발생 여부를 선택하세요.',
        black_ice_occurred: '발생',
        black_ice_not_occurred: '미발생',
        measurement_result_title: '측정 결과 ({seconds}초 평균)'
    }
};

function t(key, params = {}) {
    const table = I18N[currentLang] || I18N.en;
    let text = table[key] || I18N.en[key] || key;
    Object.entries(params).forEach(([paramKey, value]) => {
        text = text.replaceAll(`{${paramKey}}`, value);
    });
    return text;
}

function getStoredLang() {
    const stored = localStorage.getItem(LANG_STORAGE_KEY);
    return stored === 'ko' || stored === 'en' ? stored : DEFAULT_LANG;
}

function setLanguage(lang, persist = true) {
    currentLang = lang === 'ko' ? 'ko' : 'en';
    if (persist) {
        localStorage.setItem(LANG_STORAGE_KEY, currentLang);
    }
    applyTranslations();
}

function applyTranslations() {
    document.documentElement.lang = currentLang;
    document.title = t('page_title_main');

    const mainTitleEl = document.getElementById('mainTitle');
    if (mainTitleEl) {
        mainTitleEl.textContent = t('main_title');
    }

    const resultsButtonEl = document.getElementById('resultsButton');
    if (resultsButtonEl) {
        resultsButtonEl.textContent = t('results_button');
    }
    const resultsHintEl = document.getElementById('resultsHint');
    if (resultsHintEl) {
        resultsHintEl.textContent = t('results_hint');
    }

    document.querySelectorAll('[data-i18n]').forEach((el) => {
        const key = el.getAttribute('data-i18n');
        if (key) {
            el.textContent = t(key);
        }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (key && 'placeholder' in el) {
            el.placeholder = t(key);
        }
    });

    document.querySelectorAll('[data-i18n-aria]').forEach((el) => {
        const key = el.getAttribute('data-i18n-aria');
        if (key) {
            el.setAttribute('aria-label', t(key));
        }
    });

    updateMeasurementResultTitle();
    updateMeasureButton();
    renderMeasurementStatus();
    applyDistanceStatus();
    applyCameraStatus();
    loadLocationNames();
    updateLangButtons();
}

function updateLangButtons() {
    document.querySelectorAll('.lang-button').forEach((btn) => {
        const lang = btn.dataset.lang;
        btn.classList.toggle('active', lang === currentLang);
    });
}

function initLanguageSwitcher() {
    setLanguage(getStoredLang(), false);
    updateLangButtons();
    document.querySelectorAll('.lang-button').forEach((btn) => {
        btn.addEventListener('click', () => {
            setLanguage(btn.dataset.lang);
        });
    });
}

function updateMeasurementResultTitle() {
    const titleEl = document.getElementById('measurementResultTitle');
    if (!titleEl || !measurementDurationLabelEl) {
        return;
    }
    const seconds = measurementDurationLabelEl.textContent?.trim() || '60';
    const prefixSuffix = t('measurement_result_title', { seconds: '{seconds}' }).split('{seconds}');
    const prefix = prefixSuffix[0] || '';
    const suffix = prefixSuffix[1] || '';
    measurementDurationLabelEl.textContent = seconds;
    titleEl.innerHTML = '';
    titleEl.append(prefix);
    titleEl.append(measurementDurationLabelEl);
    titleEl.append(suffix);
}

function renderLocationOptions() {
    if (!locationSelectEl) {
        return;
    }
    if (locationLoadError) {
        locationSelectEl.innerHTML = `<option value="" disabled selected>${t('input_location_load_fail')}</option>`;
        return;
    }
    if (locationEntries == null) {
        locationSelectEl.innerHTML = `<option value="" disabled selected>${t('input_location_placeholder')}</option>`;
        return;
    }
    if (locationEntries.length === 0) {
        locationSelectEl.innerHTML = `<option value="" disabled selected>${t('input_location_none')}</option>`;
        return;
    }
    const placeholder = `<option value="" disabled selected>${t('input_location_placeholder')}</option>`;
    const options = locationEntries
        .map(([key, value]) => `<option value="${key}">${t('location_option', { key, name: value })}</option>`)
        .join('');
    locationSelectEl.innerHTML = placeholder + options;
}

function updateMeasureButton() {
    if (measureButtonEl) {
        measureButtonEl.textContent = isMeasuring ? t('measure_button_busy') : t('measure_button');
    }
}

function renderMeasurementStatus() {
    if (!measurementStatusEl) {
        return;
    }
    const mode = measurementStatusState?.mode || 'idle';
    if (mode === 'requesting') {
        measurementStatusEl.textContent = t('measurement_status_requesting');
    } else if (mode === 'measuring') {
        const durationSeconds = measurementStatusState.durationSeconds;
        const duration = typeof durationSeconds === 'number'
            ? t('measurement_duration_text', { seconds: durationSeconds })
            : t('measurement_status_measuring', { duration: '' }).replace(' ()', '');
        measurementStatusEl.textContent = t('measurement_status_measuring', { duration });
    } else if (mode === 'remaining') {
        const samples = measurementStatusState.samplesTaken != null && measurementStatusState.samplesTotal != null
            ? ` (${measurementStatusState.samplesTaken}/${measurementStatusState.samplesTotal})`
            : '';
        measurementStatusEl.textContent = t('measurement_status_remaining', {
            seconds: measurementStatusState.remainingSeconds ?? 0,
            samples
        });
    } else if (mode === 'completed') {
        measurementStatusEl.textContent = t('measurement_status_completed');
    } else if (mode === 'error') {
        measurementStatusEl.textContent = measurementStatusState.message || t('measurement_status_failed');
    } else {
        measurementStatusEl.textContent = t('measurement_status_idle');
    }
}

function setMeasurementStatusMode(mode, details = {}) {
    measurementStatusState = { mode, ...details };
    renderMeasurementStatus();
}

function applyDistanceStatus() {
    setDistanceStatus(distanceStatusMode);
}

function setDistanceStatus(mode) {
    distanceStatusMode = mode;
    if (!statusIndicatorEl || !statusTextEl) {
        return;
    }
    if (mode === 'connected') {
        statusIndicatorEl.className = 'status-indicator active';
        statusTextEl.textContent = t('connection_connected');
    } else if (mode === 'connecting') {
        statusIndicatorEl.className = 'status-indicator warning';
        statusTextEl.textContent = t('connection_connecting');
    } else if (mode === 'disconnected') {
        statusIndicatorEl.className = 'status-indicator error';
        statusTextEl.textContent = t('connection_disconnected');
    } else if (mode === 'normal') {
        statusIndicatorEl.className = 'status-indicator active';
        statusTextEl.textContent = t('status_normal');
    } else if (mode === 'using_last') {
        statusIndicatorEl.className = 'status-indicator warning';
        statusTextEl.textContent = t('status_using_last');
    } else if (mode === 'out_of_range') {
        statusIndicatorEl.className = 'status-indicator error';
        statusTextEl.textContent = t('status_out_of_range');
    } else if (mode === 'waiting') {
        statusIndicatorEl.className = 'status-indicator warning';
        statusTextEl.textContent = t('status_waiting_update');
    } else if (mode === 'waiting_with_last') {
        statusIndicatorEl.className = 'status-indicator warning';
        statusTextEl.textContent = t('status_waiting_update_last');
    } else {
        statusIndicatorEl.className = 'status-indicator warning';
        statusTextEl.textContent = t('status_waiting_update');
    }
}

function setCameraStatus(mode, details = {}) {
    cameraStatusMode = mode;
    cameraRetryState = { ...cameraRetryState, ...details };
    applyCameraStatus();
}

function applyCameraStatus() {
    if (!cameraPlaceholderEl) {
        return;
    }
    if (cameraStatusMode === 'not_found') {
        cameraPlaceholderEl.textContent = t('camera_not_found');
    } else if (cameraStatusMode === 'retrying') {
        cameraPlaceholderEl.textContent = t('camera_retrying', {
            retry: cameraRetryState.retryCount,
            max: cameraRetryState.maxRetries
        });
    } else {
        cameraPlaceholderEl.textContent = t('camera_connecting');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, initializing...');
    initLanguageSwitcher();
    initSocketIO();
    updateConnectionStatus(false);
    initCamera();
    loadLocationNames();

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
            updateMeasurementResultTitle();
        }
    }
});

function resolveLocationData(data) {
    if (!data) {
        return null;
    }
    if (data.en || data.ko) {
        return data[currentLang] || data.en || data.ko || {};
    }
    return data;
}

function loadLocationNames() {
    if (!locationSelectEl) {
        return;
    }
    fetch('location_names.json')
        .then((res) => (res.ok ? res.json() : {}))
        .then((data) => {
            const entries = Object.entries(resolveLocationData(data) || {});
            locationEntries = entries;
            locationLoadError = false;
            renderLocationOptions();
        })
        .catch(() => {
            locationEntries = [];
            locationLoadError = true;
            renderLocationOptions();
        });
}

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
            errorContainer.textContent = t('error_server_disconnected');
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
            errorContainer.textContent = t('error_prefix') + error;
            errorContainer.style.display = 'block';
        }
    });
}

function initCamera() {
    if (!cameraIframeEl) {
        return;
    }

    const currentHostname = window.location.hostname;
    const streamUrl = `http://${currentHostname}:4912/embed`;
    let intervalId;
    let retryCount = 0;
    const maxRetries = 30;

    cameraIframeEl.onload = () => {
        if (intervalId) {
            clearInterval(intervalId);
        }
        if (cameraPlaceholderEl) {
            cameraPlaceholderEl.style.display = 'none';
        }
        cameraIframeEl.style.display = 'block';
        retryCount = 0;
    };

    const startLoading = () => {
        if (retryCount >= maxRetries) {
            if (intervalId) {
                clearInterval(intervalId);
            }
            if (cameraPlaceholderEl) {
                setCameraStatus('not_found');
            }
            return;
        }
        retryCount += 1;
        if (retryCount > 1) {
            setCameraStatus('retrying', { retryCount, maxRetries });
        } else {
            setCameraStatus('connecting', { retryCount, maxRetries });
        }
        cameraIframeEl.src = streamUrl;
    };

    intervalId = setInterval(startLoading, 1000);
}

function updateConfigDisplay(data) {
    if (measurementDurationLabelEl && typeof data.measurement_duration === 'number') {
        measurementDurationSec = Math.round(data.measurement_duration);
        measurementDurationLabelEl.textContent = measurementDurationSec;
        updateMeasurementResultTitle();
    }
}

function handleMeasurementRequest() {
    if (isMeasuring) {
        return;
    }

    const tempValue = parseFloat(temperatureInputEl?.value);
    const humidityValue = parseFloat(humidityInputEl?.value);
    const locationValue = parseInt(locationInputEl?.value, 10);
    const blackIceSelection = document.querySelector('input[name="blackIceOccurrence"]:checked');

    if (Number.isNaN(tempValue) || Number.isNaN(humidityValue) || Number.isNaN(locationValue)) {
        showError(t('error_input_numbers'));
        return;
    }

    if (humidityValue < 0 || humidityValue > 100) {
        showError(t('error_humidity_range'));
        return;
    }

    if (!blackIceSelection) {
        showError(t('error_black_ice_required'));
        return;
    }

    clearError();
    setMeasurementBusy(true);
    setMeasurementStatusMode('requesting');

    socket.emit('measurement_request', {
        temperature: tempValue,
        humidity: humidityValue,
        location: locationValue,
        black_ice_status: blackIceSelection.value
    });
}

function updateMeasurementStatus(data) {
    const state = data.state;
    const remaining = data.remaining_seconds;
    const samplesTaken = data.samples_taken;
    const samplesTotal = data.samples_total;

    if (state === 'started') {
        setMeasurementBusy(true);
        const durationText = typeof measurementDurationSec === 'number'
            ? t('measurement_duration_text', { seconds: measurementDurationSec })
            : null;
        setMeasurementStatusMode('measuring', { durationSeconds: measurementDurationSec, durationText });
        startCountdown(remaining, samplesTaken, samplesTotal);
    } else if (state === 'progress') {
        startCountdown(remaining, samplesTaken, samplesTotal);
    } else if (state === 'completed') {
        stopCountdown();
        setMeasurementBusy(false);
        setMeasurementStatusMode('completed');
    } else if (state === 'error') {
        stopCountdown();
        setMeasurementBusy(false);
        setMeasurementStatusMode('error', { message: data.message });
    }
}

function updateMeasurementResult(data) {
    const distance = data.distance_cm_avg;
    const ldr = data.ldr_avg;
    const temperature = data.temperature;
    const humidity = data.humidity;
    const location = data.location;
    const blackIceStatus = data.black_ice_status;

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

    if (avgBlackIceEl) {
        avgBlackIceEl.classList.remove('badge', 'badge--danger', 'badge--success', 'badge--neutral');
        if (blackIceStatus === 'occurred') {
            avgBlackIceEl.textContent = t('black_ice_occurred');
            avgBlackIceEl.classList.add('badge', 'badge--danger');
        } else if (blackIceStatus === 'not_occurred') {
            avgBlackIceEl.textContent = t('black_ice_not_occurred');
            avgBlackIceEl.classList.add('badge', 'badge--success');
        } else {
            avgBlackIceEl.textContent = '--';
            avgBlackIceEl.classList.add('badge', 'badge--neutral');
        }
    }

    setMeasurementBusy(false);
    setMeasurementStatusMode('completed');
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
        setMeasurementStatusMode('remaining', {
            remainingSeconds: remainingSec,
            samplesTaken: measurementSamplesInfo?.samplesTaken,
            samplesTotal: measurementSamplesInfo?.samplesTotal
        });
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

function setMeasurementBusy(isBusy) {
    isMeasuring = isBusy;
    if (measureButtonEl) {
        measureButtonEl.disabled = isBusy;
        updateMeasureButton();
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
        setDistanceStatus('normal');
    } else {
        // 유효하지 않은 값(-1)이 들어왔을 때
        if (lastValidDistance !== null) {
            // 이전에 유효한 값이 있으면 그 값을 유지
            distanceValueEl.textContent = lastValidDistance.toFixed(2);
            distanceValueEl.classList.remove('invalid');
            setDistanceStatus('using_last');
        } else {
            // 이전 값이 없으면 -- 표시
            distanceValueEl.textContent = '--';
            distanceValueEl.classList.add('invalid');
            setDistanceStatus('out_of_range');
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
                setDistanceStatus('waiting_with_last');
            } else {
                setDistanceStatus('waiting');
            }
        }
    }, 2000);
}

function updateConnectionStatus(connected) {
    if (connected) {
        setDistanceStatus('connected');
    } else {
        setDistanceStatus('disconnected');
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

