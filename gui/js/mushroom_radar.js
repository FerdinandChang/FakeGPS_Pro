// FakeGPS Pro - 蘑菇即時戰情雷達前端控制模組
(function() {
    'use strict';

    let radarTimer = null;
    let autoRefreshSec = 15; // 預設 15 秒快速監控
    let isSoundEnabled = true;
    let isNotifyEnabled = true;
    let isAutoTeleportEnabled = false;
    let currentMushrooms = [];
    let isQuerying = false;
    let radarMarkersLayer = null;

    // 自動秒飛防封鎖與冷卻機制
    let lastAutoTeleportTime = 0;
    const AUTO_TELEPORT_COOLDOWN_MS = 60000; // 60 秒安全防封保護冷卻
    const autoTeleportedIds = new Set();

    // 蘑菇等級名稱映射
    const LEVEL_NAMES = {
        'giant': '巨大菇',
        'large': '大菇',
        'normal': '普通菇',
        'small': '小菇',
        '巨大': '巨大菇',
        '大': '大菇',
        '一般': '普通菇',
        '普通': '普通菇',
        '小': '小菇'
    };

    // 蘑菇種類名稱映射 (100% 對齊皮皮蘑菇官方代碼)
    const TYPE_NAMES = {
        'elemental': '元素菇 ✨',
        'LunarNewYearMushroom': '華麗蘑菇 🏮',
        'RockCrystalMushroom': '水晶蘑菇 💎',
        'RedFireMushroom': '火蘑菇 🔥',
        'BlueWaterMushroom': '水蘑菇 💧',
        'YellowElectricMushroom': '電蘑菇 ⚡',
        'WhitePoisonousMushroom': '毒蘑菇 🟣',
        'Placeholder26Mushroom': '冰藍蘑菇 ❄️',
        'RockMushroom': '灰色蘑菇 🪨',
        'WhiteMushroom': '白色蘑菇 🤍',
        'RedMushroom': '紅色蘑菇 🔴',
        'BlueMushroom': '藍色蘑菇 🔵',
        'YellowMushroom': '黃色蘑菇 🟡',
        'WingedMushroom': '粉紅蘑菇 🪽',
        'PurpleMushroom': '紫色蘑菇 💜'
    };

    // 網頁內視覺浮動 Toast 提示 (100% 可視保證，免疫 Windows 勿擾模式)
    function showInAppToast(title, msg) {
        let container = document.getElementById('in-app-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'in-app-toast-container';
            container.style.cssText = 'position:fixed; top:70px; right:20px; z-index:99999; display:flex; flex-direction:column; gap:10px; pointer-events:none;';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.style.cssText = 'pointer-events:auto; background:linear-gradient(135deg, rgba(15,23,42,0.96), rgba(30,41,59,0.96)); border:1px solid #c084fc; box-shadow:0 10px 30px rgba(0,0,0,0.7), 0 0 16px rgba(192,132,252,0.5); border-radius:10px; padding:12px 18px; min-width:280px; max-width:380px; color:#f8fafc; font-size:13px; transform:translateX(100%); transition:all 0.35s cubic-bezier(0.16,1,0.3,1); opacity:0;';
        toast.innerHTML = `
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px; font-weight:700; color:#e879f9;">
                <span style="font-size:18px;">🍄</span>
                <span>${title}</span>
            </div>
            <div style="font-size:12px; color:#cbd5e1; line-height:1.4;">${msg}</div>
        `;

        container.appendChild(toast);
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
            toast.style.opacity = '1';
        });

        setTimeout(() => {
            toast.style.transform = 'translateX(120%)';
            toast.style.opacity = '0';
            setTimeout(() => {
                toast.remove();
            }, 350);
        }, 4500);
    }

    // 播放提示音 (雙保險機制：前端 Web Audio + 後端原生系統音效)
    function playChime(forceSystem = false) {
        if (!isSoundEnabled && !forceSystem) return;

        // 1. 前端 Web Audio API (D5 -> A5 雙音階清脆提示音)
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                const ctx = new AudioContext();
                if (ctx.state === 'suspended') {
                    ctx.resume();
                }
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(587.33, now); // D5
                osc.frequency.setValueAtTime(880.00, now + 0.12); // A5
                gain.gain.setValueAtTime(0.3, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
                osc.start(now);
                osc.stop(now + 0.6);
            }
        } catch (e) {
            console.warn('Web Audio 播放失敗:', e);
        }

        // 2. 後端 Python 原生系統警示音 (Windows winsound / macOS afplay 必響保險)
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.play_system_alert === 'function') {
            try {
                window.pywebview.api.play_system_alert();
            } catch (e) {
                console.warn('後端原生提示音播放失敗:', e);
            }
        }
    }

    // 發送系統通知 (網頁視覺 Toast + Windows 10/11 系統橫幅雙推播)
    function sendDesktopNotification(title, msg) {
        if (!isNotifyEnabled) return;
        
        // 視覺浮動 Toast (100% 免疫勿擾模式)
        showInAppToast(title, msg);

        // 系統原生 Toast 橫幅
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.notify_desktop === 'function') {
            try {
                window.pywebview.api.notify_desktop(title, msg);
            } catch (e) {
                console.warn('發送桌面通知失敗:', e);
            }
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

    // 取得蘑菇顯示等級名稱
    function getLevelDisplayName(level) {
        return LEVEL_NAMES[level] || (level ? level : '蘑菇');
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
            const levelLabel = getLevelDisplayName(m.level);

            const iconHtml = `<div class="mushroom-marker-bubble ${badgeClass}" title="${m.place || '蘑菇'}">🍄 ${countText}</div>`;
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
                    <div class="radar-popup-row">🍄 類型：${m.typeName || levelLabel}</div>
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

    // 統一秒飛定位 (修復：直接呼叫後端真實瞬移 API pywebview.api.teleport)
    function teleportToMushroom(lat, lng, name, triggerBtn) {
        if (isNaN(lat) || isNaN(lng)) return;

        // 1. 同步更新地圖目標紅點標記與經緯度顯示
        if (typeof window.setTargetLocation === 'function') {
            window.setTargetLocation(lat, lng);
        }

        // 2. 地圖平移並放大聚焦
        if (window.map) {
            window.map.setView([lat, lng], 17);
        }

        // 3. 呼叫後端瞬移 API
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.teleport === 'function') {
            window.pywebview.api.teleport(lat, lng).then(res => {
                if (res && res.success) {
                    if (typeof window.updateCurrentLocation === 'function') {
                        window.updateCurrentLocation(lat, lng);
                    }
                    if (res.cooldown_sec > 0 && typeof window.startCooldownTimer === 'function') {
                        window.startCooldownTimer(res.cooldown_sec);
                    }
                    playChime();
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
                } else {
                    alert("瞬移失敗: " + (res ? res.message : "裝置未連線或發送失敗"));
                }
            }).catch(err => {
                console.error("瞬移執行異常:", err);
                alert("瞬移執行異常: " + err);
            });
        } else {
            console.warn("未偵測到 pywebview.api.teleport 介面");
        }
    }

    // 執行「方案 A：發現目標自動秒飛 (含安全冷卻保護)」
    function handleAutoTeleport(newItems) {
        if (!isAutoTeleportEnabled || !newItems || newItems.length === 0) return;

        const now = Date.now();
        const elapsed = now - lastAutoTeleportTime;

        // 若距離上次自動秒飛小於安全冷卻時間 (60秒)，暫緩秒飛以保護帳號安全防封
        if (elapsed < AUTO_TELEPORT_COOLDOWN_MS) {
            const remainSec = Math.ceil((AUTO_TELEPORT_COOLDOWN_MS - elapsed) / 1000);
            console.log(`[自動秒飛防封閥] 冷卻中 (剩餘 ${remainSec} 秒)，略過本次自動瞬移`);
            return;
        }

        // 尋找尚未自動瞬移過的第一個合格新蘑菇
        const target = newItems.find(m => {
            const key = m.id || `${m.lat},${m.lng}`;
            return !autoTeleportedIds.has(key);
        });

        if (!target) return;

        const key = target.id || `${target.lat},${target.lng}`;
        autoTeleportedIds.add(key);
        lastAutoTeleportTime = now;

        const lat = parseFloat(target.lat);
        const lng = parseFloat(target.lng);
        const placeName = target.place || `${target.city} ${target.area}`;

        console.log(`⚡ [方案 A 自動秒飛] 命中目標: ${placeName} (${lat}, ${lng})，自動執行瞬移！`);
        teleportToMushroom(lat, lng, placeName);

        // 發送專屬桌面通知提示
        sendDesktopNotification(
            `⚡ 自動秒飛就位成功！`,
            `已為您瞬移至 [${target.city} ${target.area}] ${target.typeName || '蘑菇'} (${placeName})，進入 60s 安全防封保護！`
        );
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
        const level = document.getElementById('radar-filter-level')?.value || 'giant';
        const mushroomType = document.getElementById('radar-filter-type')?.value || 'all';
        const freshness = document.getElementById('radar-filter-freshness')?.value || '60';
        const sort = document.getElementById('radar-filter-sort')?.value || 'updated';

        try {
            const res = await window.pywebview.api.query_giant_mushrooms(city, area, engagement, level, mushroomType, sort, freshness);
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

                // 若有新目標，播放雙保險音效與系統通知
                if (newItems.length > 0) {
                    playChime();
                    if (isNotifyEnabled) {
                        const first = newItems[0];
                        const levelName = getLevelDisplayName(first.level || level);
                        const title = `🍄 發現 ${newItems.length} 顆符合條件 ${levelName}！`;
                        const msg = `[${first.city} ${first.area}] ${first.typeName || levelName} (${first.place}) 目前 ${first.challengerCount}/5 人`;
                        sendDesktopNotification(title, msg);
                    }

                    // 執行自動秒飛
                    handleAutoTeleport(newItems);
                }

                // 渲染右側抽屜清單
                renderMushroomList(currentMushrooms);
                // 渲染左側快捷清單
                renderSideQuickList(currentMushrooms);
                // 更新地圖標記
                updateMapMarkers(currentMushrooms);
            } else {
                if (res && res.need_login) {
                    updateLoginButtonState(false);
                    const authCard = `
                        <div class="radar-empty-msg" style="padding: 2rem 1rem; text-align: center;">
                            <div style="font-size: 40px; margin-bottom: 12px;">🔑</div>
                            <strong style="color: #60a5fa; font-size: 15px;">皮皮蘑菇官方已更新為需 Google 登入</strong>
                            <div style="font-size: 12px; color: #94a3b8; margin: 8px 0 16px; line-height: 1.5;">官網安全性改版，請透過內嵌視窗授權登入一次即可恢復即時戰情與一鍵秒飛！</div>
                            <button id="btn-login-prompt" class="btn btn-primary" style="margin: 0 auto; padding: 0.6rem 1.2rem; display: inline-flex; align-items: center; gap: 6px; background: #3b82f6; border: none; font-weight: bold; border-radius: 6px; cursor: pointer; color: white;">
                                🚀 點此一鍵 Google 登入授權
                            </button>
                            <div style="margin-top: 14px;">
                                <a href="javascript:void(0)" onclick="MushroomRadar.promptManualCookie()" style="font-size: 11px; color: #64748b; text-decoration: underline;">或手動貼入 Cookie</a>
                            </div>
                        </div>`;
                    if (listContainer) listContainer.innerHTML = authCard;
                    if (sideListContainer) sideListContainer.innerHTML = authCard;
                    document.getElementById('btn-login-prompt')?.addEventListener('click', () => {
                        triggerPipiLogin();
                    });
                } else {
                    const errMsg = `<div class="radar-empty-msg">查詢失敗: ${res?.error || '請確認網路連線'}</div>`;
                    if (listContainer) listContainer.innerHTML = errMsg;
                    if (sideListContainer) sideListContainer.innerHTML = errMsg;
                }
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
                    <strong>目前沒有符合條件的蘑菇</strong>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">雷達在背景持續全自動監控，發現目標將即時提醒！</div>
                </div>`;
            return;
        }

        listContainer.innerHTML = items.map(m => {
            const hpPct = formatHpPercent(m.remainingHp, m.totalHp);
            const countClass = m.challengerCount === 0 ? 'badge-zero' : 'badge-open';
            const countText = m.challengerCount === 0 ? '0 / 5 (空場速來!)' : `${m.challengerCount} / 5 人`;
            const levelName = getLevelDisplayName(m.level);
            
            return `
                <div class="radar-card">
                    <div class="radar-card-header">
                        <span class="radar-type-tag">${m.typeName || levelName}</span>
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
                    目前無符合條件蘑菇，持續監控中...
                </div>`;
            return;
        }

        sideListContainer.innerHTML = items.map(m => {
            const countClass = m.challengerCount === 0 ? 'badge-zero' : 'badge-open';
            const countText = m.challengerCount === 0 ? '0/5 (空場)' : `${m.challengerCount}/5 人`;
            const hpPct = formatHpPercent(m.remainingHp, m.totalHp);
            const levelName = getLevelDisplayName(m.level);

            return `
                <div class="coord-card" style="padding: 0.6rem; border-color: rgba(236, 72, 153, 0.25);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
                        <span style="font-size: 0.78rem; font-weight: 700; color: #f8fafc; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 170px;" title="${m.place}">
                            📍 ${m.place || '未知地標'}
                        </span>
                        <span class="radar-count-tag ${countClass}" style="font-size: 0.68rem; padding: 1px 5px;">${countText}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted); margin-bottom: 0.35rem;">
                        <span>${m.city} ${m.area} (${m.typeName || levelName})</span>
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
        const levelFilter = document.getElementById('radar-filter-level');
        const typeFilter = document.getElementById('radar-filter-type');
        const freshnessFilter = document.getElementById('radar-filter-freshness');
        const sortFilter = document.getElementById('radar-filter-sort');
        const autoTeleportToggle = document.getElementById('radar-auto-teleport');
        const testAlertBtn = document.getElementById('radar-btn-test-alert');

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
                // 開啟抽屜
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
            autoRefreshSec = parseInt(intervalSel.value, 10) || 15;
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

        if (levelFilter) {
            levelFilter.addEventListener('change', () => {
                refreshRadarData();
            });
        }

        if (typeFilter) {
            typeFilter.addEventListener('change', () => {
                refreshRadarData();
            });
        }

        if (freshnessFilter) {
            freshnessFilter.addEventListener('change', () => {
                refreshRadarData();
            });
        }

        if (sortFilter) {
            sortFilter.addEventListener('change', () => {
                refreshRadarData();
            });
        }

        if (autoTeleportToggle) {
            autoTeleportToggle.addEventListener('change', () => {
                isAutoTeleportEnabled = autoTeleportToggle.checked;
                if (isAutoTeleportEnabled) {
                    sendDesktopNotification(
                        '⚡ 自動秒飛已啟用',
                        '當雷達掃描到符合條件的新蘑菇時，系統將全自動順飛至該處！（具備 60 秒防封保護鎖）'
                    );
                }
            });
        }

        if (testAlertBtn) {
            testAlertBtn.addEventListener('click', () => {
                // 觸發音效雙保險與系統 Toast
                playChime(true);
                sendDesktopNotification(
                    '🍄 蘑菇戰情提醒測試',
                    '通知與警示音效 100% 正常運作中！發現目標將零延遲提醒您。'
                );
                testAlertBtn.textContent = '✅ 已發送測試';
                setTimeout(() => {
                    testAlertBtn.textContent = '🧪 測試通知';
                }, 2000);
            });
        }

        // 登入皮皮按鈕事件綁定
        const loginBtn = document.getElementById('radar-btn-login');
        if (loginBtn) {
            loginBtn.addEventListener('click', () => {
                triggerPipiLogin();
            });
        }
        checkPipiLoginStatus();

        // 首次啟動輪詢
        setupPolling();
        
        // 延遲 1 秒執行首次資料查詢
        setTimeout(() => {
            refreshRadarData();
        }, 1000);
    }

    // 更新登入按鈕外觀狀態
    function updateLoginButtonState(isLoggedIn) {
        const loginBtn = document.getElementById('radar-btn-login');
        const icon = document.getElementById('pipi-login-icon');
        const text = document.getElementById('pipi-login-text');
        if (!loginBtn) return;

        if (isLoggedIn) {
            loginBtn.style.background = '#10b981';
            loginBtn.title = '皮皮蘑菇帳號已授權登入（點擊可切換或手動更新 Cookie）';
            if (icon) icon.textContent = '✅';
            if (text) text.textContent = '已登入';
        } else {
            loginBtn.style.background = '#3b82f6';
            loginBtn.title = '使用 Google 帳號授權登入皮皮蘑菇';
            if (icon) icon.textContent = '🔑';
            if (text) text.textContent = '登入皮皮';
        }
    }

    // 檢查登入憑證狀態
    async function checkPipiLoginStatus() {
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_pipi_auth_status === 'function') {
            try {
                const res = await window.pywebview.api.get_pipi_auth_status();
                updateLoginButtonState(res && res.is_logged_in);
            } catch (e) {
                console.warn('檢查皮皮蘑菇登入狀態失敗:', e);
            }
        }
    }

    // 觸發皮皮蘑菇 Google 登入流程
    function triggerPipiLogin() {
        if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api.open_pipi_login !== 'function') {
            alert('系統未就緒，請稍候重試');
            return;
        }
        showInAppToast('🔑 開啟登入中', '請在彈出的視窗中完成 Google 帳號授權登入...');
        window.pywebview.api.open_pipi_login().then(res => {
            if (!res.success) {
                alert('開啟登入視窗失敗: ' + (res.message || '未知錯誤'));
            }
        });
    }

    // 手動貼入 Cookie 支援（備用）
    function promptManualCookie() {
        const val = prompt('請貼上從瀏覽器複製的皮皮蘑菇 Cookie 字串 (格式: ASP.NET_SessionId=...; pm_site_session=...):');
        if (!val) return;
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.set_pipi_cookie_manual === 'function') {
            window.pywebview.api.set_pipi_cookie_manual(val).then(res => {
                if (res.success) {
                    showInAppToast('✅ Cookie 儲存成功', '已套用皮皮蘑菇登入憑證！');
                    updateLoginButtonState(true);
                    refreshRadarData();
                } else {
                    alert('儲存失敗: ' + (res.message || '格式不正確'));
                }
            });
        }
    }

    // 全域回呼：當登入視窗成功捕獲 Cookie 時由後端自動調用
    window.onPipiLoginSuccess = function() {
        updateLoginButtonState(true);
        showInAppToast('🎉 登入授權成功', '已成功取得皮皮蘑菇認證憑證，正在載入最新戰況！');
        refreshRadarData();
    };

    // DOM Ready
    window.addEventListener('DOMContentLoaded', () => {
        initCityOptions();
        initEvents();
    });

    // 依據當前選取的條件動態開啟官方網頁
    window.openMushroomWebWithCurrentFilters = function() {
        const city = document.getElementById('radar-filter-city')?.value || '';
        const area = document.getElementById('radar-filter-area')?.value || '';
        const engagement = document.getElementById('radar-filter-engagement')?.value || 'under_five';
        const level = document.getElementById('radar-filter-level')?.value || 'giant';
        const mushroomType = document.getElementById('radar-filter-type')?.value || 'all';
        const freshness = document.getElementById('radar-filter-freshness')?.value || '60';
        const sort = document.getElementById('radar-filter-sort')?.value || 'updated';

        const levelMap = { 'giant': '巨大', 'large': '大', 'normal': '一般', 'small': '小', 'all': '' };
        const actualLevel = levelMap[level] !== undefined ? levelMap[level] : level;
        const actualType = mushroomType === 'all' ? '' : mushroomType;

        let url = 'https://pipimushroom.com/ppmushroom.aspx?regionCode=TW';
        if (city) url += `&city=${encodeURIComponent(city)}`;
        if (area) url += `&area=${encodeURIComponent(area)}`;
        if (actualType) url += `&type=${encodeURIComponent(actualType)}`;
        if (actualLevel) url += `&level=${encodeURIComponent(actualLevel)}`;
        if (engagement && engagement !== 'all') url += `&engagement=${encodeURIComponent(engagement)}`;
        if (freshness && freshness !== '60') url += `&freshness=${encodeURIComponent(freshness)}`;
        if (sort && sort !== 'power') url += `&sort=${encodeURIComponent(sort)}`;

        if (typeof window.openExternalUrl === 'function') {
            window.openExternalUrl(url);
        } else if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_url === 'function') {
            window.pywebview.api.open_url(url);
        } else {
            window.open(url, '_blank');
        }
    };

    window.MushroomRadar = {
        refresh: refreshRadarData,
        playChime: playChime,
        sendDesktopNotification: sendDesktopNotification,
        login: triggerPipiLogin,
        promptManualCookie: promptManualCookie,
        teleport: function(lat, lng, encodedName) {
            const name = decodeURIComponent(encodedName || '');
            teleportToMushroom(lat, lng, name);
        }
    };
})();
