const socket = io(`http://${window.location.host}`);

const resultsListEl = document.getElementById('resultsList');
const resultsDetailEl = document.getElementById('resultsDetail');
const refreshButtonEl = document.getElementById('refreshButton');
const resultsErrorEl = document.getElementById('resultsError');

let locationNames = {};
let measurementIndex = new Map();
let latestListItems = [];
let latestDetail = null;

const LANG_STORAGE_KEY = 'bid_lang';
const DEFAULT_LANG = 'en';
let currentLang = DEFAULT_LANG;
const I18N = {
    en: {
        page_title_results: 'Measurement Results - Black Ice Detector',
        results_title: 'Measurement Results',
        results_list_title: 'Measurement List',
        refresh_button: 'Refresh',
        loading_results: 'Loading data...',
        empty_results: 'No saved measurement records.',
        results_detail_title: 'Measurement Details',
        results_detail_hint: 'Select an item in the list to see details.',
        loading_detail: 'Loading details...',
        detail_not_found: 'Could not find the detail.',
        list_time_label: 'Time',
        list_location_label: 'Location',
        status_occurred: 'Occurred',
        status_not_occurred: 'Not occurred',
        location_fallback: 'Location {number}',
        detail_time_label: 'Time',
        detail_location_label: 'Location',
        detail_black_ice_label: 'Black Ice',
        detail_distance_label: 'Distance',
        detail_light_label: 'Light',
        detail_temp_label: 'Temperature',
        detail_humidity_label: 'Humidity',
        detail_samples_label: 'Samples',
        photo_missing: 'No photo available.',
        photo_alt: 'Measurement photo',
        error_server_generic: 'A server error occurred.'
    },
    ko: {
        page_title_results: '측정 결과 목록 - Black Ice Detector',
        results_title: '측정 결과 목록',
        results_list_title: '측정 리스트',
        refresh_button: '새로고침',
        loading_results: '데이터를 불러오는 중...',
        empty_results: '저장된 측정 기록이 없습니다.',
        results_detail_title: '측정 상세',
        results_detail_hint: '리스트에서 항목을 선택하면 상세 결과가 표시됩니다.',
        loading_detail: '상세 정보를 불러오는 중...',
        detail_not_found: '상세 정보를 찾지 못했습니다.',
        list_time_label: '일시',
        list_location_label: '장소',
        status_occurred: '발생',
        status_not_occurred: '미발생',
        location_fallback: '위치 {number}',
        detail_time_label: '일시',
        detail_location_label: '장소',
        detail_black_ice_label: '블랙 아이스',
        detail_distance_label: '거리',
        detail_light_label: '조도',
        detail_temp_label: '온도',
        detail_humidity_label: '습도',
        detail_samples_label: '샘플',
        photo_missing: '사진이 없습니다.',
        photo_alt: '측정 사진',
        error_server_generic: '서버 오류가 발생했습니다.'
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
    document.title = t('page_title_results');
    document.querySelectorAll('[data-i18n]').forEach((el) => {
        const key = el.getAttribute('data-i18n');
        if (key) {
            el.textContent = t(key);
        }
    });
    updateLangButtons();
    loadLocationNames().then(() => {
        renderList(latestListItems);
        if (latestDetail) {
            renderDetail(latestDetail);
        } else if (resultsDetailEl) {
            resultsDetailEl.textContent = t('results_detail_hint');
        }
    });
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
    return fetch('location_names.json')
        .then((res) => (res.ok ? res.json() : {}))
        .then((data) => {
            locationNames = resolveLocationData(data) || {};
        })
        .catch(() => {
            locationNames = {};
        });
}

function showError(message) {
    if (resultsErrorEl) {
        resultsErrorEl.textContent = message;
        resultsErrorEl.style.display = 'block';
    }
}

function clearError() {
    if (resultsErrorEl) {
        resultsErrorEl.textContent = '';
        resultsErrorEl.style.display = 'none';
    }
}

function requestList() {
    clearError();
    if (resultsListEl) {
        resultsListEl.innerHTML = `<div class="results-empty">${t('loading_results')}</div>`;
    }
    socket.emit('measurement_list_request', {});
}

function renderList(items) {
    if (!resultsListEl) {
        return;
    }
    if (!items || items.length === 0) {
        resultsListEl.innerHTML = `<div class="results-empty">${t('empty_results')}</div>`;
        return;
    }

    measurementIndex = new Map(items.map((item) => [item.record_id, item]));
    resultsListEl.innerHTML = '';

    items.forEach((item) => {
        const listItem = document.createElement('div');
        listItem.className = 'results-item';
        listItem.dataset.recordId = item.record_id;

        const locationLabel = locationNames[item.location] || t('location_fallback', { number: item.location ?? '-' });
        const timeText = item.measured_at
            ? new Date(item.measured_at).toLocaleString(currentLang === 'ko' ? 'ko-KR' : 'en-US')
            : '--';
        const statusText = item.black_ice_status === 'occurred' ? t('status_occurred') : t('status_not_occurred');
        const statusClass = item.black_ice_status === 'occurred' ? 'occurred' : 'not-occurred';

        listItem.innerHTML = `
            <div class="results-meta">
                <div><strong>${t('list_time_label')}</strong> ${timeText}</div>
                <div><strong>${t('list_location_label')}</strong> ${locationLabel}</div>
                <div class="results-status ${statusClass}">${statusText}</div>
            </div>
        `;

        listItem.addEventListener('click', () => {
            setActiveItem(listItem);
            requestDetail(item.record_id);
        });

        resultsListEl.appendChild(listItem);
    });
}

function setActiveItem(activeEl) {
    const items = resultsListEl?.querySelectorAll('.results-item') || [];
    items.forEach((el) => el.classList.remove('active'));
    activeEl.classList.add('active');
}

function requestDetail(recordId) {
    if (!recordId) {
        return;
    }
    if (resultsDetailEl) {
        resultsDetailEl.textContent = t('loading_detail');
    }
    socket.emit('measurement_detail_request', { record_id: recordId });
}

function renderDetail(detail) {
    if (!resultsDetailEl || !detail) {
        return;
    }
    const locationLabel = locationNames[detail.location] || t('location_fallback', { number: detail.location ?? '-' });
    const statusText = detail.black_ice_status === 'occurred' ? t('status_occurred') : t('status_not_occurred');
    const timeText = detail.measured_at
        ? new Date(detail.measured_at).toLocaleString(currentLang === 'ko' ? 'ko-KR' : 'en-US')
        : '--';

    const photoHtml = detail.photo_data
        ? `<div class="detail-photo"><img src="data:${detail.photo_mime};base64,${detail.photo_data}" alt="${t('photo_alt')}"></div>`
        : `<div class="results-empty">${t('photo_missing')}</div>`;

    resultsDetailEl.innerHTML = `
        <div class="detail-grid">
            <div class="detail-item"><span class="detail-label">${t('detail_time_label')}</span><span class="detail-value">${timeText}</span></div>
            <div class="detail-item"><span class="detail-label">${t('detail_location_label')}</span><span class="detail-value">${locationLabel}</span></div>
            <div class="detail-item"><span class="detail-label">${t('detail_black_ice_label')}</span><span class="detail-value">${statusText}</span></div>
            <div class="detail-item"><span class="detail-label">${t('detail_distance_label')}</span><span class="detail-value">${formatNumber(detail.distance_cm_avg, 2)} cm</span></div>
            <div class="detail-item"><span class="detail-label">${t('detail_light_label')}</span><span class="detail-value">${formatNumber(detail.ldr_avg, 0)}</span></div>
            <div class="detail-item"><span class="detail-label">${t('detail_temp_label')}</span><span class="detail-value">${formatNumber(detail.temperature, 1)} °C</span></div>
            <div class="detail-item"><span class="detail-label">${t('detail_humidity_label')}</span><span class="detail-value">${formatNumber(detail.humidity, 1)} %</span></div>
            <div class="detail-item"><span class="detail-label">${t('detail_samples_label')}</span><span class="detail-value">${detail.samples_taken ?? '-'} / ${detail.samples_total ?? '-'}</span></div>
        </div>
        ${photoHtml}
    `;
}

function formatNumber(value, digits) {
    if (typeof value !== 'number') {
        return '--';
    }
    return digits > 0 ? value.toFixed(digits) : Math.round(value).toString();
}

socket.on('connect', () => {
    requestList();
});

socket.on('measurement_list', (data) => {
    latestListItems = data?.items || [];
    renderList(latestListItems);
});

socket.on('measurement_detail', (data) => {
    if (!data?.detail) {
        latestDetail = null;
        resultsDetailEl.textContent = t('detail_not_found');
        return;
    }
    latestDetail = data.detail;
    renderDetail(latestDetail);
});

socket.on('error', (error) => {
    showError(typeof error === 'string' ? error : t('error_server_generic'));
});

if (refreshButtonEl) {
    refreshButtonEl.addEventListener('click', requestList);
}

initLanguageSwitcher();
loadLocationNames().then(requestList);
