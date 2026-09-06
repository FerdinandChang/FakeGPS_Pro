// FakeGPS Pro - 巨大蘑菇即時雷達前端控制模組
(function() {
    'use strict';

    let radarTimer = null;
    let autoRefreshSec = 30; // 預設 30 秒
    let isSoundEnabled = true;
    let isNotifyEnabled = true;
    let currentMushrooms = [];
    let isQuerying = false;
    let radarMarkersLayer = null;

    // Web Audio API 清脆雙音階提示音 (D5 -> A5)
    function playChime() {
        if (!isSoundEnabled) return;
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            const ctx = new AudioContext();
            const now = ctx.currentTime;
            
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            
            osc.type = 'sine';
            osc.frequency.setValueAtTime(587.33, now); // D5
            osc.frequency.setValueAtTime(880.00, now + 0.12); // A5
            
            gain.gain.setValueAtTime(0.25, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
            
            osc.start(now);
            osc.stop(now + 0.6);
        } catch (e) {
            console.warn('播放提示音失敗:', e);
        }
    }

    // 初始化縣市選單
    function initCityOptions() {
        const citySel = document.getElementById('radar-filter-city');
        const areaSel = document.getElementById('radar-filter-area');
        if (!citySel || typeof TAIWAN_DISTRICTS === 'undefined') return;

        citySel.innerHTML = '<option value="">全台灣 (不限縣市)</option>';
        Object.keys(TAIWAN_DISTRICTS).forEach(city => {
            const opt = document.createElement('option');
            opt.value = city;
            opt.textContent = city;
            citySel.appendChild(opt);
        });

        citySel.addEventListener('change', () => {
            const selectedCity = citySel.value;
            areaSel.innerHTML = '<option value="">全區</option>';
            if (selectedCity && TAIWAN_DISTRICTS[selectedCity]) {
                areaSel.disabled = false;
                TAIWAN_DISTRICTS[selectedCity].forEach(area => {
                    const opt = document.createElement('option');
                    opt.value = area;
                    opt.textContent = area;
                    areaSel.appendChild(opt);
                });
            } else {
                areaSel.disabled = true;
            }
            refreshRadarData();
        });

        areaSel.addEventListener('change', () => {
            refreshRadarData();
        });
    }

    // 格式化數字
    function formatNum(n) {
        return Number(n || 0).toLocaleString('zh-TW');
    }

    // 格式化血量百分比
    function formatHpPercent(remaining, total) {
        if (!total || total <= 0) return 0;
        return Math.max(0, Math.min(100, (remaining / total * 100))).toFixed(1);
    }

    // 地圖標記繪製
    function updateMapMarkers(items) {
        if (!window.map || typeof L === 'undefined') return;

        if (!radarMarkersLayer) {
            radarMarkersLayer = L.layerGroup().addTo(window.map);
        } else {
            radarMarkersLayer.clearLayers();
        }

        if (!items || items.length === 0) return;

        items.forEach(m => {
            const lat = parseFloat(m.lat);
            const lng = parseFloat(m.lng);
            if (isNaN(lat) || isNaN(lng)) return;

            const isZero = m.challengerCount === 0;
            const badgeClass = isZero ? 'badge-zero' : '';
            const countText = isZero ? '0人空場' : `${m.challengerCount}/5人`;
            const hpPct = formatHpPercent(m.remainingHp, m.totalHp);

            const iconHtml = `<div class="mushroom-marker-bubble ${badgeClass}" title="${m.place || '巨大蘑菇'}">🍄 ${countText}</div>`;
            const customIcon = L.divIcon({
                className: 'mushroom-map-marker',
                html: iconHtml,
                iconSize: [72, 26],
                iconAnchor: [36, 13]
            });

            const marker = L.marker([lat, lng], { icon: customIcon });
            
            const popupHtml = `
                <div class="radar-popup-card">
                    <div class="radar-popup-title">📍 ${m.place || '未知地標'}</div>
                    <div class="radar-popup-row">🍄 類型：${m.typeName || '巨大蘑菇'}</div>
                    <div class="radar-popup-row">🏙️ 地區：${m.city || ''} ${m.area || ''}</div>
                    <div class="radar-popup-row">⚔️ 參戰：<strong>${countText}</strong></div>
                    <div class="radar-popup-row">❤️ 剩餘血量：${hpPct}% (${formatNum(m.remainingHp)})</div>
                    <button class="radar-popup-btn" onclick="MushroomRadar.teleport(${lat}, ${lng}, '${encodeURIComponent(m.place || '')}')">🚀 立即一鍵秒飛開打</button>
                </div>
            `;
            marker.bindPopup(popupHtml);
            radarMarkersLayer.addLayer(marker);
        });
    }

    // 統一秒飛定位
    function teleportToMushroom(lat, lng, name, triggerBtn) {
        if (isNaN(lat) || isNaN(lng)) return;

        // 呼叫底層瞬移
        if (typeof window.teleportTo === 'function') {
            window.teleportTo(lat, lng);
        } else if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.set_location(lat, lng);
            if (typeof window.updateCurrentLocation === 'function') {
                window.updateCurrentLocation(lat, lng);
            }
        }

        // 地圖平移並放大聚焦
        if (window.map) {
            window.map.setView([lat, lng], 17);
        }

        // 播放提示音
        playChime();

        // 視覺回饋
        if (triggerBtn) {
            const originText = triggerBtn.textContent;
            triggerBtn.textContent = '✅ 已瞬移！';
            triggerBtn.style.backgroundColor = '#10b981';
            triggerBtn.style.borderColor = '#10b981';
            setTimeout(() => {
                triggerBtn.textContent = originText;
                triggerBtn.style.backgroundColor = '';
                triggerBtn.style.borderColor = '';
            }, 1800);
        }
    }

    // 刷新蘑菇雷達資料
    async function refreshRadarData() {
        if (isQuerying || !window.pywebview || !window.pywebview.api) return;
        isQuerying = true;
        
        const refreshBtn = document.getElementById('radar-btn-refresh');
        const listContainer = document.getElementById('radar-mushroom-list');
        const sideListContainer = document.getElementById('side-radar-list');
        const countBadge = document.getElementById('radar-count-badge');
        const navBadge = document.getElementById('nav-radar-badge');
        const sideBadge = document.getElementById('side-radar-badge');
        
        if (refreshBtn) refreshBtn.classList.add('rotating');
        
        const city = document.getElementById('radar-filter-city')?.value || '';
        const area = document.getElementById('radar-filter-area')?.value || '';
        const engagement = document.getElementById('radar-filter-engagement')?.value || 'under_five';

        try {
            const res = await window.pywebview.api.query_giant_mushrooms(city, area, engagement);
            if (res && res.success) {
                currentMushrooms = res.items || [];
                const newItems = res.new_items || [];
                
                // 更新數量標籤
                const countText = `${currentMushrooms.length} 顆`;
                if (countBadge) countBadge.textContent = countText;
                if (sideBadge) sideBadge.textContent = `${currentMushrooms.length} 顆可打`;
                if (navBadge) {
                    navBadge.textContent = currentMushrooms.length;
                    navBadge.style.display = currentMushrooms.length > 0 ? 'inline-block' : 'none';
                }

                // 若有新目標，播放音效與系統通知
                if (newItems.length > 0) {
                    playChime();
                    if (isNotifyEnabled) {
                        const first = newItems[0];
                        const title = `🍄 發現 ${newItems.length} 顆未滿 5 人巨大蘑菇！`;
                        const msg = `[${first.city} ${first.area}] ${first.typeName} (${first.place}) 目前 ${first.challengerCount}/5 人`;
                        window.pywebview.api.notify_desktop(title, msg);
                    }
                }

                // 渲染右側抽屜清單
                renderMushroomList(currentMushrooms);
                // 渲染左側快捷清單
                renderSideQuickList(currentMushrooms);
                // 更新地圖標記
                updateMapMarkers(currentMushrooms);
            } else {
                const errMsg = `<div class="radar-empty-msg">查詢失敗: ${res?.error || '請確認網路連線'}</div>`;
                if (listContainer) listContainer.innerHTML = errMsg;
                if (sideListContainer) sideListContainer.innerHTML = errMsg;
            }
        } catch (err) {
            console.error('雷達更新錯誤:', err);
            const errMsg = `<div class="radar-empty-msg">連線異常，將於下週期重試</div>`;
            if (listContainer) listContainer.innerHTML = errMsg;
            if (sideListContainer) sideListContainer.innerHTML = errMsg;
        } finally {
            isQuerying = false;
            if (refreshBtn) refreshBtn.classList.remove('rotating');
        }
    }

    // 渲染右側抽屜卡片清單
    function renderMushroomList(items) {
        const listContainer = document.getElementById('radar-mushroom-list');
        if (!listContainer) return;

        if (!items || items.length === 0) {
            listContainer.innerHTML = `
                <div class="radar-empty-msg">
                    <div style="font-size: 36px; margin-bottom: 8px;">🍄</div>
                    <strong>目前沒有符合條件的巨大蘑菇</strong>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">雷達將在背景持續監控，一有新目標立刻通知！</div>
                </div>`;
            return;
        }

        listContainer.innerHTML = items.map(m => {
            const hpPct = formatHpPercent(m.remainingHp, m.totalHp);
            const countClass = m.challengerCount === 0 ? 'badge-zero' : 'badge-open';
            const countText = m.challengerCount === 0 ? '0 / 5 (空場速來!)' : `${m.challengerCount} / 5 人`;
            
            return `
                <div class="radar-card">
                    <div class="radar-card-header">
                        <span class="radar-type-tag">${m.typeName || '巨大蘑菇'}</span>
                        <span class="radar-count-tag ${countClass}">${countText}</span>
                    </div>
                    <div class="radar-card-title" title="${m.place || '未知地標'}">
                        📍 ${m.place || '未知地標'}
                    </div>
                    <div class="radar-card-meta">
                        <span>🏙️ ${m.city || ''} ${m.area || ''}</span>
                        <span>⚔️ 戰力: ${formatNum(m.totalPower)}</span>
                    </div>
                    <div class="radar-hp-wrap">
                        <div class="radar-hp-label">
                            <span>剩餘血量</span>
                            <span>${hpPct}% (${formatNum(m.remainingHp)})</span>
                        </div>
                        <div class="radar-hp-bar-bg">
                            <div class="radar-hp-bar-fill" style="width: ${hpPct}%;"></div>
                        </div>
                    </div>
                    <div class="radar-card-actions">
                        <button class="btn-radar-teleport" data-lat="${m.lat}" data-lng="${m.lng}" data-name="${encodeURIComponent(m.place || '')}">
                            🚀 一鍵秒飛
                        </button>
                        <button class="btn-radar-map" data-lat="${m.lat}" data-lng="${m.lng}" data-name="${encodeURIComponent(m.place || '')}">
                            🗺️ 定位至此
                        </button>
                    </div>
                </div>`;
        }).join('');

        // 綁定事件
        listContainer.querySelectorAll('.btn-radar-teleport').forEach(btn => {
            btn.addEventListener('click', () => {
                const lat = parseFloat(btn.dataset.lat);
                const lng = parseFloat(btn.dataset.lng);
                const name = decodeURIComponent(btn.dataset.name || '');
                teleportToMushroom(lat, lng, name, btn);
            });
        });

        listContainer.querySelectorAll('.btn-radar-map').forEach(btn => {
            btn.addEventListener('click', () => {
                const lat = parseFloat(btn.dataset.lat);
                const lng = parseFloat(btn.dataset.lng);
                if (window.map) {
                    window.map.setView([lat, lng], 17);
                }
            });
        });
    }

    // 渲染左側面板緊湊型清單
    function renderSideQuickList(items) {
        const sideListContainer = document.getElementById('side-radar-list');
        if (!sideListContainer) return;

        if (!items || items.length === 0) {
            sideListContainer.innerHTML = `
                <div style="text-align: center; padding: 1.5rem 0.5rem; color: var(--text-muted); font-size: 0.8rem;">
                    目前無符合條件巨大菇，持續監控中...
                </div>`;
            return;
        }

        sideListContainer.innerHTML = items.map(m => {
            const countClass = m.challengerCount === 0 ? 'badge-zero' : 'badge-open';
            const countText = m.challengerCount === 0 ? '0/5 (空場)' : `${m.challengerCount}/5 人`;
            const hpPct = formatHpPercent(m.remainingHp, m.totalHp);

            return `
                <div class="coord-card" style="padding: 0.6rem; border-color: rgba(236, 72, 153, 0.25);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
                        <span style="font-size: 0.78rem; font-weight: 700; color: #f8fafc; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 170px;" title="${m.place}">
                            📍 ${m.place || '未知地標'}
                        </span>
                        <span class="radar-count-tag ${countClass}" style="font-size: 0.68rem; padding: 1px 5px;">${countText}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted); margin-bottom: 0.35rem;">
                        <span>${m.city} ${m.area}</span>
                        <span>血量: ${hpPct}%</span>
                    </div>
                    <button class="btn btn-primary btn-sm side-btn-teleport" data-lat="${m.lat}" data-lng="${m.lng}" data-name="${encodeURIComponent(m.place || '')}" style="width: 100%; justify-content: center; font-size: 0.75rem; padding: 0.25rem;">
                        🚀 秒飛開打
                    </button>
                </div>
            `;
        }).join('');

        sideListContainer.querySelectorAll('.side-btn-teleport').forEach(btn => {
            btn.addEventListener('click', () => {
                const lat = parseFloat(btn.dataset.lat);
                const lng = parseFloat(btn.dataset.lng);
                const name = decodeURIComponent(btn.dataset.name || '');
                teleportToMushroom(lat, lng, name, btn);
            });
        });
    }

    // 重設輪詢計時器
    function setupPolling() {
        if (radarTimer) {
            clearInterval(radarTimer);
            radarTimer = null;
        }
        if (autoRefreshSec > 0) {
            radarTimer = setInterval(() => {
                refreshRadarData();
            }, autoRefreshSec * 1000);
        }
    }

    // 初始化事件監聽
    function initEvents() {
        const panel = document.getElementById('mushroom-radar-panel');
        const openBtn = document.getElementById('btn-open-radar');
        const closeBtn = document.getElementById('btn-close-radar');
        const sideOpenBtn = document.getElementById('btn-side-open-drawer');
        const tabRadar = document.getElementById('tab-radar');
        const refreshBtn = document.getElementById('radar-btn-refresh');
        const intervalSel = document.getElementById('radar-interval-select');
        const soundToggle = document.getElementById('radar-sound-toggle');
        const notifyToggle = document.getElementById('radar-notify-toggle');
        const engFilter = document.getElementById('radar-filter-engagement');

        function toggleRadarDrawer(forceState) {
            if (!panel) return;
            const willOpen = typeof forceState === 'boolean' ? forceState : !panel.classList.contains('active');
            if (willOpen) {
                panel.classList.add('active');
                if (openBtn) openBtn.classList.add('active');
                refreshRadarData();
            } else {
                panel.classList.remove('active');
                if (openBtn) openBtn.classList.remove('active');
            }
        }

        if (openBtn) {
            openBtn.addEventListener('click', () => {
                toggleRadarDrawer();
            });
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                toggleRadarDrawer(false);
            });
        }

        if (sideOpenBtn) {
            sideOpenBtn.addEventListener('click', () => {
                toggleRadarDrawer(true);
            });
        }

        if (tabRadar) {
            tabRadar.addEventListener('click', () => {
                toggleRadarDrawer(true);
            });
        }

        // ESC 鍵關閉雷達抽屜
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && panel && panel.classList.contains('active')) {
                toggleRadarDrawer(false);
            }
        });

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                refreshRadarData();
            });
        }

        if (intervalSel) {
            intervalSel.addEventListener('change', () => {
                autoRefreshSec = parseInt(intervalSel.value, 10);
                setupPolling();
            });
        }

        if (soundToggle) {
            soundToggle.addEventListener('change', () => {
                isSoundEnabled = soundToggle.checked;
                if (isSoundEnabled) playChime(); // 播放試聽
            });
        }

        if (notifyToggle) {
            notifyToggle.addEventListener('change', () => {
                isNotifyEnabled = notifyToggle.checked;
            });
        }

        if (engFilter) {
            engFilter.addEventListener('change', () => {
                refreshRadarData();
            });
        }

        // 首次啟動輪詢
        setupPolling();
        
        // 延遲 1 秒執行首次資料查詢
        setTimeout(() => {
            refreshRadarData();
        }, 1000);
    }

    // DOM Ready
    window.addEventListener('DOMContentLoaded', () => {
        initCityOptions();
        initEvents();
    });

    window.MushroomRadar = {
        refresh: refreshRadarData,
        playChime: playChime,
        teleport: function(lat, lng, encodedName) {
            const name = decodeURIComponent(encodedName || '');
            teleportToMushroom(lat, lng, name);
        }
    };
})();
