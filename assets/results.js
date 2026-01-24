const socket = io(`http://${window.location.host}`);

const resultsListEl = document.getElementById('resultsList');
const resultsDetailEl = document.getElementById('resultsDetail');
const refreshButtonEl = document.getElementById('refreshButton');
const resultsErrorEl = document.getElementById('resultsError');

let locationNames = {};
let measurementIndex = new Map();

function loadLocationNames() {
    return fetch('location_names.json')
        .then((res) => (res.ok ? res.json() : {}))
        .then((data) => {
            locationNames = data || {};
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
        resultsListEl.innerHTML = '<div class="results-empty">데이터를 불러오는 중...</div>';
    }
    socket.emit('measurement_list_request', {});
}

function renderList(items) {
    if (!resultsListEl) {
        return;
    }
    if (!items || items.length === 0) {
        resultsListEl.innerHTML = '<div class="results-empty">저장된 측정 기록이 없습니다.</div>';
        return;
    }

    measurementIndex = new Map(items.map((item) => [item.record_id, item]));
    resultsListEl.innerHTML = '';

    items.forEach((item) => {
        const listItem = document.createElement('div');
        listItem.className = 'results-item';
        listItem.dataset.recordId = item.record_id;

        const locationLabel = locationNames[item.location] || `위치 ${item.location ?? '-'}`;
        const timeText = item.measured_at ? new Date(item.measured_at).toLocaleString() : '--';
        const statusText = item.black_ice_status === 'occurred' ? '발생' : '미발생';
        const statusClass = item.black_ice_status === 'occurred' ? 'occurred' : 'not-occurred';

        listItem.innerHTML = `
            <div class="results-meta">
                <div><strong>일시</strong> ${timeText}</div>
                <div><strong>장소</strong> ${locationLabel}</div>
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
        resultsDetailEl.textContent = '상세 정보를 불러오는 중...';
    }
    socket.emit('measurement_detail_request', { record_id: recordId });
}

function renderDetail(detail) {
    if (!resultsDetailEl || !detail) {
        return;
    }
    const locationLabel = locationNames[detail.location] || `위치 ${detail.location ?? '-'}`;
    const statusText = detail.black_ice_status === 'occurred' ? '발생' : '미발생';
    const timeText = detail.measured_at ? new Date(detail.measured_at).toLocaleString() : '--';

    const photoHtml = detail.photo_data
        ? `<div class="detail-photo"><img src="data:${detail.photo_mime};base64,${detail.photo_data}" alt="측정 사진"></div>`
        : '<div class="results-empty">사진이 없습니다.</div>';

    resultsDetailEl.innerHTML = `
        <div class="detail-grid">
            <div class="detail-item"><span class="detail-label">일시</span><span class="detail-value">${timeText}</span></div>
            <div class="detail-item"><span class="detail-label">장소</span><span class="detail-value">${locationLabel}</span></div>
            <div class="detail-item"><span class="detail-label">블랙 아이스</span><span class="detail-value">${statusText}</span></div>
            <div class="detail-item"><span class="detail-label">거리</span><span class="detail-value">${formatNumber(detail.distance_cm_avg, 2)} cm</span></div>
            <div class="detail-item"><span class="detail-label">조도</span><span class="detail-value">${formatNumber(detail.ldr_avg, 0)}</span></div>
            <div class="detail-item"><span class="detail-label">온도</span><span class="detail-value">${formatNumber(detail.temperature, 1)} °C</span></div>
            <div class="detail-item"><span class="detail-label">습도</span><span class="detail-value">${formatNumber(detail.humidity, 1)} %</span></div>
            <div class="detail-item"><span class="detail-label">샘플</span><span class="detail-value">${detail.samples_taken ?? '-'} / ${detail.samples_total ?? '-'}</span></div>
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
    renderList(data?.items || []);
});

socket.on('measurement_detail', (data) => {
    if (!data?.detail) {
        resultsDetailEl.textContent = '상세 정보를 찾지 못했습니다.';
        return;
    }
    renderDetail(data.detail);
});

socket.on('error', (error) => {
    showError(typeof error === 'string' ? error : '서버 오류가 발생했습니다.');
});

if (refreshButtonEl) {
    refreshButtonEl.addEventListener('click', requestList);
}

loadLocationNames().then(requestList);
