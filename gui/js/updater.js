// FakeGPS Pro - 線上自動檢查與一鍵升級模組
(function() {
    'use strict';

    let latestUpdateInfo = null;

    // 格式化檔案大小
    function formatBytes(bytes) {
        if (!bytes || bytes <= 0) return '';
        const mb = bytes / (1024 * 1024);
        return `(${mb.toFixed(1)} MB)`;
    }

    // 檢查更新
    async function checkForUpdates(isManual = false) {
        if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.check_for_updates) {
            return;
        }

        const updateBtn = document.getElementById('btn-check-update');
        if (isManual && updateBtn) {
            updateBtn.textContent = '🔄 檢查中...';
            updateBtn.disabled = true;
        }

        try {
            const res = await window.pywebview.api.check_for_updates();
            if (res && res.success) {
                if (res.has_update) {
                    latestUpdateInfo = res;
                    showUpdateModal(res);
                } else if (isManual) {
                    alert(`目前已是最新版本 (v${res.current_version})！暫無更新。`);
                }
            } else if (isManual) {
                alert(`檢查更新失敗: ${res?.error || '連線逾時'}`);
            }
        } catch (e) {
            console.error('檢查更新異常:', e);
            if (isManual) alert('連線至更新伺服器發生異常。');
        } finally {
            if (isManual && updateBtn) {
                updateBtn.textContent = '🔄 檢查更新';
                updateBtn.disabled = false;
            }
        }
    }

    // 顯示更新彈窗
    function showUpdateModal(info) {
        const modal = document.getElementById('update-modal');
        if (!modal) return;

        const curVerEl = document.getElementById('update-cur-ver');
        const newVerEl = document.getElementById('update-new-ver');
        const sizeEl = document.getElementById('update-file-size');
        const changelogEl = document.getElementById('update-changelog');
        const progressBox = document.getElementById('update-progress-box');
        const actionBtns = document.getElementById('update-action-btns');
        const btnStart = document.getElementById('btn-start-upgrade');

        if (curVerEl) curVerEl.textContent = `v${info.current_version}`;
        if (newVerEl) newVerEl.textContent = `v${info.latest_version}`;
        if (sizeEl) sizeEl.textContent = formatBytes(info.file_size);
        if (changelogEl) {
            changelogEl.textContent = info.changelog || '本版本包含效能優化與問題修復。';
        }

        // 重置進度條顯示
        if (progressBox) progressBox.style.display = 'none';
        if (actionBtns) actionBtns.style.display = 'flex';
        if (btnStart) {
            btnStart.disabled = false;
            btnStart.textContent = '🚀 立即升級並重新啟動';
        }

        modal.style.display = 'flex';
    }

    // 關閉彈窗
    function closeUpdateModal() {
        const modal = document.getElementById('update-modal');
        if (modal) modal.style.display = 'none';
    }

    // 開始升級
    async function startUpgrade() {
        if (!latestUpdateInfo || !latestUpdateInfo.download_url) {
            alert('找不到下載連結，請稍後再試。');
            return;
        }

        const progressBox = document.getElementById('update-progress-box');
        const actionBtns = document.getElementById('update-action-btns');
        const progressBar = document.getElementById('update-progress-bar');
        const progressText = document.getElementById('update-progress-text');

        if (actionBtns) actionBtns.style.display = 'none';
        if (progressBox) progressBox.style.display = 'block';
        if (progressBar) progressBar.style.width = '5%';
        if (progressText) progressText.textContent = '正在連線下載更新檔...';

        try {
            const res = await window.pywebview.api.start_auto_update(latestUpdateInfo.download_url);
            if (!res || !res.success) {
                alert(`啟動更新失敗: ${res?.error || '未知錯誤'}`);
                if (actionBtns) actionBtns.style.display = 'flex';
                if (progressBox) progressBox.style.display = 'none';
            }
        } catch (e) {
            console.error('啟動升級錯誤:', e);
            alert('啟動更新失敗，請檢查網路連線。');
            if (actionBtns) actionBtns.style.display = 'flex';
            if (progressBox) progressBox.style.display = 'none';
        }
    }

    // Python 後端進度回報回呼
    window.onUpdateProgress = function(pct, message) {
        const progressBar = document.getElementById('update-progress-bar');
        const progressText = document.getElementById('update-progress-text');

        if (pct < 0) {
            // 錯誤
            if (progressText) progressText.textContent = `❌ ${message}`;
            if (progressBar) progressBar.style.backgroundColor = '#ef4444';
            setTimeout(() => {
                const actionBtns = document.getElementById('update-action-btns');
                const progressBox = document.getElementById('update-progress-box');
                if (actionBtns) actionBtns.style.display = 'flex';
                if (progressBox) progressBox.style.display = 'none';
            }, 3000);
            return;
        }

        if (progressBar) {
            progressBar.style.width = `${Math.min(100, Math.max(5, pct))}%`;
        }
        if (progressText) {
            progressText.textContent = message;
        }
    };

    // 初始化事件
    function initEvents() {
        const btnCheck = document.getElementById('btn-check-update');
        const btnClose = document.getElementById('btn-close-update');
        const btnLater = document.getElementById('btn-update-later');
        const btnStart = document.getElementById('btn-start-upgrade');

        if (btnCheck) {
            btnCheck.addEventListener('click', () => checkForUpdates(true));
        }
        if (btnClose) {
            btnClose.addEventListener('click', closeUpdateModal);
        }
        if (btnLater) {
            btnLater.addEventListener('click', closeUpdateModal);
        }
        if (btnStart) {
            btnStart.addEventListener('click', startUpgrade);
        }

        // 開啟 3 秒後靜默自動檢查一次
        setTimeout(() => {
            checkForUpdates(false);
        }, 3000);
    }

    window.addEventListener('DOMContentLoaded', initEvents);

    window.AutoUpdaterUI = {
        check: checkForUpdates,
        show: showUpdateModal
    };
})();
