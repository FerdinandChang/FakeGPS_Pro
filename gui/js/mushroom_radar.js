// FakeGPS Pro - 巨大蘑菇即時雷達前端控制模組
(function() {
    'use strict';

    let radarTimer = null;
    let autoRefreshSec = 30; // 預設 30 秒
    let isSoundEnabled = true;
    let isNotifyEnabled = true;
    let currentMushrooms = [];
    let isQuerying = false;

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

    // 刷新蘑菇雷達資料
    async function refreshRadarData() {
        if (isQuerying || !window.pywebview || !window.pywebview.api) return;
        isQuerying = true;
        
        const refreshBtn = document.getElementById('radar-btn-refresh');
        const listContainer = document.getElementById('radar-mushroom-list');
        const countBadge = document.getElementById('radar-count-badge');
        const navBadge = document.getElementById('nav-radar-badge');
        
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
                if (navBadge) {
                    navBadge.textContent = currentMushrooms.length;
                    navBadge.style.display = currentMushrooms.length > 0 ? 'inline-block' : 'none';
                }

                // 若有新偵測到的蘑菇，觸發音效與桌面通知
                if (newItems.length > 0) {
                    playChime();
                    if (isNotifyEnabled) {
                        const first = newItems[0];
                        const title = `🍄 發現 ${newItems.length} 顆未滿 5 人巨大蘑菇！`;
                        const msg = `[${first.city} ${first.area}] ${first.typeName} (${first.place}) 目前 ${first.challengerCount}/5 人`;
                        window.pywebview.api.notify_desktop(title, msg);
                    }
                }

                // 渲染清單
                renderMushroomList(currentMushrooms);
            } else {
                if (listContainer) {
                    listContainer.innerHTML = `<div class="radar-empty-msg">查詢失敗: ${res?.error || '請確認網路連線'}</div>`;
                }
            }
        } catch (err) {
            console.error('雷達更新錯誤:', err);
            if (listContainer) {
                listContainer.innerHTML = `<div class="radar-empty-msg">連線發生異常，將於下個週期重試</div>`;
            }
        } finally {
            isQuerying = false;
            if (refreshBtn) refreshBtn.classList.remove('rotating');
        }
    }

    // 渲染卡片清單
    function renderMushroomList(items) {
        const listContainer = document.getElementById('radar-mushroom-list');
        if (!listContainer) return;

        if (!items || items.length === 0) {
            listContainer.innerHTML = `
                <div class="radar-empty-msg">
                    <div style="font-size: 32px; margin-bottom: 8px;">🍄</div>
                    <strong>目前沒有符合條件的巨大蘑菇</strong>
                    <div style="font-size: 12px; color: #888; margin-top: 4px;">雷達將在背景持續監控，一有新目標立刻通知！</div>
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
                    <div class="radar-card-title" title="${m.place}">
                        📍 ${m.place || '未知地標'}
                    </div>
                    <div class="radar-card-meta">
                        <span>🏙️ ${m.city || ''} ${m.area || ''}</span>
                        <span>⚔️ 戰力: ${formatNum(m.totalPower)}</span>
                    </div>
                    <div class="radar-hp-wrap">
                        <div class="radar-hp-label">
                            <span>剩餘血量</span>
                            <span>${hpPct}%</span>
                        </div>
                        <div class="radar-hp-bar-bg">
                            <div class="radar-hp-bar-fill" style="width: ${hpPct}%;"></div>
                        </div>
                    </div>
                    <div class="radar-card-actions">
                        <button class="btn-radar-teleport" data-lat="${m.lat}" data-lng="${m.lng}" data-name="${m.place}">
                            🚀 一鍵秒飛
                        </button>
                        <button class="btn-radar-map" data-lat="${m.lat}" data-lng="${m.lng}">
                            🗺️ 開地圖
                        </button>
                    </div>
                </div>`;
        }).join('');

        // 綁定卡片按鈕事件
        listContainer.querySelectorAll('.btn-radar-teleport').forEach(btn => {
            btn.addEventListener('click', () => {
                const lat = parseFloat(btn.dataset.lat);
                const lng = parseFloat(btn.dataset.lng);
                const name = btn.dataset.name;
                if (isNaN(lat) || isNaN(lng)) return;

                // 呼叫地圖秒飛邏輯
                if (typeof window.teleportTo === 'function') {
                    window.teleportTo(lat, lng);
                } else if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.set_location(lat, lng);
                    if (window.updateCurrentLocation) {
                        window.updateCurrentLocation(lat, lng);
                    }
                }
                
                // 視覺回饋
                btn.textContent = '✅ 已瞬移！';
                btn.style.backgroundColor = '#10b981';
                setTimeout(() => {
                    btn.textContent = '🚀 一鍵秒飛';
                    btn.style.backgroundColor = '';
                }, 2000);
            });
        });

        listContainer.querySelectorAll('.btn-radar-map').forEach(btn => {
            btn.addEventListener('click', () => {
                const lat = btn.dataset.lat;
                const lng = btn.dataset.lng;
                const url = `https://pipimushroom.com/mfmap.aspx?lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}&zoom=19&regionCode=TW`;
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.open_url(url);
                } else {
                    window.open(url, '_blank');
                }
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
        const refreshBtn = document.getElementById('radar-btn-refresh');
        const intervalSel = document.getElementById('radar-interval-select');
        const soundToggle = document.getElementById('radar-sound-toggle');
        const notifyToggle = document.getElementById('radar-notify-toggle');
        const engFilter = document.getElementById('radar-filter-engagement');

        if (openBtn) {
            openBtn.addEventListener('click', () => {
                panel.classList.toggle('active');
                if (panel.classList.contains('active')) {
                    refreshRadarData();
                }
            });
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                panel.classList.remove('active');
            });
        }

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
                if (isSoundEnabled) playChime(); // 播放一下給使用者試聽
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
        
        // 延遲 1.5 秒執行首次資料查詢
        setTimeout(() => {
            refreshRadarData();
        }, 1500);
    }

    // DOM Ready
    window.addEventListener('DOMContentLoaded', () => {
        initCityOptions();
        initEvents();
    });

    window.MushroomRadar = {
        refresh: refreshRadarData,
        playChime: playChime
    };
})();
