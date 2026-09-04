// Leaflet 地圖操作與定位邏輯
let map;
let currentMarker = null;
let targetMarker = null;
let routePolyline = null;
let waypoints = []; // [{lat, lng}, ...]

// 目前假定位狀態
let curLat = 25.033964;
let curLon = 121.564468;
let currentMode = "teleport"; // 'teleport', 'joystick', 'route'
let currentSpeedKmh = 3.6;

// 冷卻倒數計時器
let cooldownInterval = null;
let cooldownRemainingSec = 0;

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initUIEvents();
    initLicenseEvents();
    setTimeout(checkLicenseStatus, 300);
    setTimeout(refreshDevices, 500);
});

// PyWebView API 注入完成事件
window.addEventListener('pywebviewready', () => {
    checkLicenseStatus();
    refreshDevices();
});

// 每 3 秒背景自動檢查一次裝置連線 (僅在未連線時輪詢)
setInterval(() => {
    const statusText = document.getElementById('status-text');
    if (statusText && statusText.innerText !== "已連線") {
        refreshDevices();
    }
}, 3000);

function initMap() {
    // 初始化地圖 (預設台北)
    map = L.map('map', {
        zoomControl: false,
        attributionControl: false
    }).setView([curLat, curLon], 16);
    window.map = map;

    // 縮放按鈕放置在右上角
    L.control.zoom({ position: 'topright' }).addTo(map);

    // 標準 OpenStreetMap 圖資 (無 API Key 限制)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // 當前假位置標記 (藍色圖示)
    const curIcon = L.divIcon({
        className: 'custom-cur-marker',
        html: `<div style="width: 16px; height: 16px; background: #3b82f6; border: 3px solid #ffffff; border-radius: 50%; box-shadow: 0 0 12px #3b82f6;"></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
    });

    currentMarker = L.marker([curLat, curLon], { icon: curIcon }).addTo(map);

    // 地圖點擊事件
    map.on('click', onMapClick);
}

function onMapClick(e) {
    const { lat, lng } = e.latlng;

    if (currentMode === "teleport") {
        setTargetLocation(lat, lng);
    } else if (currentMode === "route") {
        addWaypoint(lat, lng);
    }
}

function setTargetLocation(lat, lng) {
    if (!targetMarker) {
        const targetIcon = L.divIcon({
            className: 'custom-target-marker',
            html: `<div style="width: 20px; height: 20px; background: #ef4444; border: 3px solid #ffffff; border-radius: 50%; box-shadow: 0 0 14px #ef4444;"></div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
        targetMarker = L.marker([lat, lng], { icon: targetIcon }).addTo(map);
    } else {
        targetMarker.setLatLng([lat, lng]);
    }

    document.getElementById('target-lat').innerText = lat.toFixed(6);
    document.getElementById('target-lon').innerText = lng.toFixed(6);

    // 計算距離與建議冷卻時間
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.calculate_distance_and_cooldown(curLat, curLon, lat, lng).then(res => {
            document.getElementById('target-dist').innerText = (res.distance_km).toFixed(2) + " km";
            document.getElementById('cooldown-estimate').innerText = formatCooldownText(res.cooldown_sec);
        });
    }
}

function addWaypoint(lat, lng) {
    waypoints.push({ lat, lng });
    renderWaypoints();
    drawRouteLine();
}

function renderWaypoints() {
    const listEl = document.getElementById('waypoint-list');
    listEl.innerHTML = '';
    waypoints.forEach((wp, idx) => {
        const item = document.createElement('div');
        item.className = 'waypoint-item';
        item.innerHTML = `
            <span>#${idx + 1} (${wp.lat.toFixed(5)}, ${wp.lng.toFixed(5)})</span>
            <span class="waypoint-remove" onclick="removeWaypoint(${idx})">&times;</span>
        `;
        listEl.appendChild(item);
    });
}

function removeWaypoint(idx) {
    waypoints.splice(idx, 1);
    renderWaypoints();
    drawRouteLine();
}

function clearWaypoints() {
    waypoints = [];
    renderWaypoints();
    if (routePolyline) {
        map.removeLayer(routePolyline);
        routePolyline = null;
    }
}

function drawRouteLine() {
    if (routePolyline) {
        map.removeLayer(routePolyline);
    }
    const latlngs = waypoints.map(p => [p.lat, p.lng]);
    if (latlngs.length > 0) {
        // 連接起點
        latlngs.unshift([curLat, curLon]);
        routePolyline = L.polyline(latlngs, { color: '#3b82f6', weight: 4, dashArray: '6, 8' }).addTo(map);
    }
}

// 供 Python 端即時回呼更新座標
window.updateCurrentLocation = function(lat, lon) {
    curLat = lat;
    curLon = lon;
    if (currentMarker) {
        currentMarker.setLatLng([lat, lon]);
    }
    document.getElementById('cur-lat').innerText = lat.toFixed(6);
    document.getElementById('cur-lon').innerText = lon.toFixed(6);
};

function formatCooldownText(sec) {
    if (sec <= 0) return "無冷卻";
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m} 分 ${s} 秒`;
}

function startCooldownTimer(sec) {
    if (cooldownInterval) clearInterval(cooldownInterval);
    cooldownRemainingSec = sec;

    const timerEl = document.getElementById('active-cooldown');
    const updateDisplay = () => {
        if (cooldownRemainingSec <= 0) {
            clearInterval(cooldownInterval);
            timerEl.innerText = "00:00 (安全)";
            timerEl.style.color = "#10b981";
            return;
        }
        const m = String(Math.floor(cooldownRemainingSec / 60)).padStart(2, '0');
        const s = String(cooldownRemainingSec % 60).padStart(2, '0');
        timerEl.innerText = `${m}:${s}`;
        timerEl.style.color = "#fbbf24";
        cooldownRemainingSec--;
    };

    updateDisplay();
    cooldownInterval = setInterval(updateDisplay, 1000);
}

// UI 事件綁定
function openManual() {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_manual) {
        window.pywebview.api.open_manual();
    } else {
        window.open('manual.html', '_blank');
    }
}

function initUIEvents() {
    // 模式切換
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentMode = tab.dataset.mode;

            document.querySelectorAll('.mode-panel').forEach(p => p.style.display = 'none');
            document.getElementById(`panel-${currentMode}`).style.display = 'block';

            // 搖桿面板顯示控制
            const joystickBox = document.getElementById('joystick-container');
            if (currentMode === 'joystick') {
                joystickBox.style.display = 'flex';
            } else {
                joystickBox.style.display = 'none';
            }
        });
    });

    // 速度調整
    const speedSlider = document.getElementById('speed-slider');
    const speedDisplay = document.getElementById('speed-display');
    speedSlider.addEventListener('input', (e) => {
        setSpeed(parseFloat(e.target.value));
    });

    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setSpeed(parseFloat(btn.dataset.speed));
        });
    });

    // 瞬移按鈕
    document.getElementById('btn-teleport').addEventListener('click', () => {
        if (!targetMarker) {
            alert("請先在地圖上點擊或搜尋目標位置！");
            return;
        }
        const pos = targetMarker.getLatLng();
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.teleport(pos.lat, pos.lng).then(res => {
                if (res.success) {
                    window.updateCurrentLocation(pos.lat, pos.lng);
                    map.panTo([pos.lat, pos.lng]);
                    if (res.cooldown_sec > 0) {
                        startCooldownTimer(res.cooldown_sec);
                    }
                } else {
                    alert("瞬移失敗: " + res.message);
                }
            });
        }
    });

    // 搜尋
    document.getElementById('btn-search').addEventListener('click', handleSearch);
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // 連線按鈕
    document.getElementById('btn-connect').addEventListener('click', () => {
        const select = document.getElementById('device-select');
        const serial = select.value;
        if (!serial) {
            alert("請先選擇或插入 iOS 裝置！");
            return;
        }
        const btn = document.getElementById('btn-connect');
        btn.innerText = "連線中...";
        btn.disabled = true;

        window.pywebview.api.connect_device(serial).then(res => {
            btn.disabled = false;
            if (res.success) {
                btn.innerText = "已連線";
                btn.className = "btn btn-secondary";
                document.getElementById('status-badge').className = "status-badge connected";
                document.getElementById('status-text').innerText = `${res.device.name} (iOS ${res.device.version})`;
            } else {
                btn.innerText = "連線裝置";
                btn.className = "btn btn-primary";
                alert(res.message);
            }
        }).catch(err => {
            btn.disabled = false;
            btn.innerText = "連線裝置";
            btn.className = "btn btn-primary";
            alert("連線發生錯誤: " + err);
        });
    });

    // 一鍵喚醒/啟用開發者模式
    const btnDevMode = document.getElementById('btn-dev-mode');
    if (btnDevMode) {
        btnDevMode.addEventListener('click', () => {
            const select = document.getElementById('device-select');
            const serial = select ? select.value : null;
            if (!serial) {
                alert("請先將 iPhone 插上 USB 並解鎖螢幕！");
                return;
            }
            btnDevMode.innerText = "喚醒中...";
            btnDevMode.disabled = true;
            window.pywebview.api.enable_developer_mode(serial).then(res => {
                btnDevMode.innerText = "🛠️ 喚醒開發者模式";
                btnDevMode.disabled = false;
                alert(res.message);
            }).catch(err => {
                btnDevMode.innerText = "🛠️ 喚醒開發者模式";
                btnDevMode.disabled = false;
                alert("執行失敗: " + err);
            });
        });
    }

    // 還原真實 GPS
    document.getElementById('btn-reset-gps').addEventListener('click', () => {
        if (confirm("確定要清除模擬定位，恢復手機真實 GPS 嗎？")) {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.reset_gps().then(res => {
                    alert(res.message);
                });
            }
        }
    });

    // 路線導航按鈕
    document.getElementById('btn-start-route').addEventListener('click', () => {
        if (waypoints.length < 1) {
            alert("請在地圖上點擊加入至少一個路徑點！");
            return;
        }
        const fullPoints = [[curLat, curLon], ...waypoints.map(p => [p.lat, p.lng])];
        const loop = document.getElementById('route-loop').checked;

        window.pywebview.api.start_route(fullPoints, currentSpeedKmh, loop).then(res => {
            if (res.success) {
                document.getElementById('btn-start-route').style.display = 'none';
                document.getElementById('btn-stop-route').style.display = 'block';
            }
        });
    });

    document.getElementById('btn-stop-route').addEventListener('click', () => {
        window.pywebview.api.stop_route().then(() => {
            document.getElementById('btn-start-route').style.display = 'block';
            document.getElementById('btn-stop-route').style.display = 'none';
        });
    });

    // 重新整理裝置按鈕
    const refreshBtn = document.getElementById('btn-refresh-devices');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => refreshDevices(true));
    }
}

function setSpeed(speed) {
    currentSpeedKmh = speed;
    document.getElementById('speed-slider').value = speed;
    document.getElementById('speed-display').innerText = `${speed} km/h`;
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.set_speed(speed);
    }
}

function handleSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;

    // 判斷是否為經緯度格式 (例如: 25.033964, 121.564468)
    const coordMatch = query.match(/^([-+]?[0-9]*\.?[0-9]+)\s*,\s*([-+]?[0-9]*\.?[0-9]+)$/);
    if (coordMatch) {
        const lat = parseFloat(coordMatch[1]);
        const lon = parseFloat(coordMatch[2]);
        map.setView([lat, lon], 16);
        setTargetLocation(lat, lon);
        return;
    }

    // 地名搜尋
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.search_place(query).then(res => {
            if (res.success && res.results.length > 0) {
                const first = res.results[0];
                map.setView([first.lat, first.lon], 16);
                setTargetLocation(first.lat, first.lon);
            } else {
                alert("查無此地名，請嘗試輸入詳細地址或經緯度。");
            }
        });
    }
}

function refreshDevices(isManual = false) {
    const select = document.getElementById('device-select');
    const refreshBtn = document.getElementById('btn-refresh-devices');

    if (isManual && refreshBtn) {
        refreshBtn.innerText = '掃描中...';
    }

    if (!window.pywebview || !window.pywebview.api) {
        setTimeout(() => refreshDevices(isManual), 200);
        return;
    }

    window.pywebview.api.get_devices().then(devices => {
        if (refreshBtn) refreshBtn.innerText = '🔄 重新整理';
        const currentSelected = select.value;

        // 比對裝置清單是否改變
        const currentOptions = Array.from(select.options).map(o => o.value).filter(v => v !== "");
        const newOptions = (devices || []).map(d => d.serial);

        if (JSON.stringify(currentOptions) === JSON.stringify(newOptions) && currentOptions.length > 0 && !isManual) {
            return;
        }

        select.innerHTML = '';
        if (!devices || devices.length === 0) {
            select.innerHTML = '<option value="">未檢測到 iOS 裝置 (請插上 USB 並信任)</option>';
        } else {
            devices.forEach((d, idx) => {
                const opt = document.createElement('option');
                opt.value = d.serial;
                opt.innerText = `${d.name} (${d.serial.substring(0, 10)}...)`;
                if (d.serial === currentSelected || (!currentSelected && idx === 0)) {
                    opt.selected = true;
                }
                select.appendChild(opt);
            });
        }
    }).catch(err => {
        if (refreshBtn) refreshBtn.innerText = '🔄 重新整理';
        console.error("取得裝置失敗:", err);
    });
}

// ==================== 雲端授權與啟用邏輯 ====================
let isAppActivated = false;

function checkLicenseStatus() {
    if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.check_license) return;

    window.pywebview.api.check_license().then(res => {
        const overlay = document.getElementById('license-overlay');
        const midDisplay = document.getElementById('display-machine-id');
        if (midDisplay && res.machine_id) {
            midDisplay.innerText = res.machine_id;
        }

        if (res.is_activated) {
            isAppActivated = true;
            if (overlay) overlay.style.display = 'none';
        } else {
            isAppActivated = false;
            if (overlay) overlay.style.display = 'flex';
        }
    }).catch(err => {
        console.error("授權狀態檢查失敗:", err);
    });
}

function initLicenseEvents() {
    const btnActivate = document.getElementById('btn-activate-license');
    const inputKey = document.getElementById('license-input-key');
    const msgBox = document.getElementById('license-status-msg');
    const btnCopyMid = document.getElementById('btn-copy-mid');
    const midDisplay = document.getElementById('display-machine-id');

    if (btnCopyMid) {
        btnCopyMid.addEventListener('click', () => {
            const mid = midDisplay.innerText;
            if (mid && mid !== "正在取得中...") {
                navigator.clipboard.writeText(mid).then(() => {
                    btnCopyMid.innerText = '✅ 已複製';
                    setTimeout(() => { btnCopyMid.innerText = '📋 複製'; }, 2000);
                });
            }
        });
    }

    if (btnActivate) {
        btnActivate.addEventListener('click', () => {
            const key = (inputKey.value || "").trim();
            if (!key) {
                showLicenseMsg("請輸入啟用序號！", "error");
                return;
            }

            btnActivate.disabled = true;
            btnActivate.innerText = "⏳ 正在連線雲端驗證中...";
            showLicenseMsg("正在連線 Google 雲端伺服器驗證中（初次喚醒需約 3~8 秒，請稍候）...", "info");

            if (window.pywebview && window.pywebview.api && window.pywebview.api.activate_license) {
                window.pywebview.api.activate_license(key).then(res => {
                    btnActivate.disabled = false;
                    btnActivate.innerText = "🚀 立即線上驗證並啟用";

                    if (res.success) {
                        showLicenseMsg("🎉 " + res.message, "success");
                        isAppActivated = true;
                        setTimeout(() => {
                            const overlay = document.getElementById('license-overlay');
                            if (overlay) overlay.style.display = 'none';
                        }, 1200);
                    } else {
                        showLicenseMsg(res.message, "error");
                    }
                }).catch(err => {
                    btnActivate.disabled = false;
                    btnActivate.innerText = "🚀 立即線上驗證並啟用";
                    showLicenseMsg("驗證失敗: " + err, "error");
                });
            } else {
                btnActivate.disabled = false;
                btnActivate.innerText = "🚀 立即線上驗證並啟用";
                showLicenseMsg("API 尚未就緒，請重試", "error");
            }
        });
    }

    // 支援按下 Enter 直接提交
    if (inputKey) {
        inputKey.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                btnActivate.click();
            }
        });
    }
}

function showLicenseMsg(text, type) {
    const msgBox = document.getElementById('license-status-msg');
    if (!msgBox) return;
    msgBox.style.display = 'block';
    msgBox.className = 'license-status-msg ' + (type || '');
    msgBox.innerText = text;
}

