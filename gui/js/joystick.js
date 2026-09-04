// 虛擬搖桿與鍵盤 WASD 控制器
let joystickActive = false;
let pressedKeys = new Set();
let joystickHeading = 0;

document.addEventListener("DOMContentLoaded", () => {
    initVirtualJoystick();
    initKeyboardControls();
});

function initVirtualJoystick() {
    const pad = document.getElementById('joystick-pad');
    const stick = document.getElementById('joystick-stick');
    if (!pad || !stick) return;

    let isDragging = false;
    const maxRadius = 45; // 搖桿最大移動半徑

    const startDrag = (e) => {
        isDragging = true;
        updateStick(e);
    };

    const doDrag = (e) => {
        if (!isDragging) return;
        updateStick(e);
    };

    const stopDrag = () => {
        if (!isDragging) return;
        isDragging = false;
        stick.style.transform = `translate(-50%, -50%)`;
        sendJoystickState(0, false);
    };

    const updateStick = (e) => {
        const rect = pad.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;

        const dx = clientX - centerX;
        const dy = clientY - centerY;
        const dist = Math.sqrt(dx * dx + dy * dy);

        let clampedDist = Math.min(dist, maxRadius);
        let angleRad = Math.atan2(dy, dx);

        const stickX = Math.cos(angleRad) * clampedDist;
        const stickY = Math.sin(angleRad) * clampedDist;

        stick.style.transform = `translate(calc(-50% + ${stickX}px), calc(-50% + ${stickY}px))`;

        // 計算地理方位角 (0度為北方/上方，90度為東方/右方)
        let headingDeg = (Math.atan2(dx, -dy) * 180 / Math.PI + 360) % 360;
        sendJoystickState(headingDeg, true);
    };

    pad.addEventListener('mousedown', startDrag);
    window.addEventListener('mousemove', doDrag);
    window.addEventListener('mouseup', stopDrag);

    pad.addEventListener('touchstart', startDrag);
    window.addEventListener('touchmove', doDrag);
    window.addEventListener('touchend', stopDrag);
}

function initKeyboardControls() {
    window.addEventListener('keydown', (e) => {
        const key = e.key.toUpperCase();
        if (['W', 'A', 'S', 'D', 'ARROWUP', 'ARROWDOWN', 'ARROWLEFT', 'ARROWRIGHT'].includes(key)) {
            // 避免在搜尋框輸入時觸發
            if (document.activeElement.tagName === 'INPUT') return;
            e.preventDefault();
            pressedKeys.add(key);
            processKeyboardMovement();
        }
    });

    window.addEventListener('keyup', (e) => {
        const key = e.key.toUpperCase();
        if (pressedKeys.has(key)) {
            pressedKeys.delete(key);
            processKeyboardMovement();
        }
    });
}

function processKeyboardMovement() {
    let up = pressedKeys.has('W') || pressedKeys.has('ARROWUP');
    let down = pressedKeys.has('S') || pressedKeys.has('ARROWDOWN');
    let left = pressedKeys.has('A') || pressedKeys.has('ARROWLEFT');
    let right = pressedKeys.has('D') || pressedKeys.has('ARROWRIGHT');

    if (!up && !down && !left && !right) {
        sendJoystickState(0, false);
        return;
    }

    let dx = 0;
    let dy = 0;
    if (up) dy -= 1;
    if (down) dy += 1;
    if (left) dx -= 1;
    if (right) dx += 1;

    let headingDeg = (Math.atan2(dx, -dy) * 180 / Math.PI + 360) % 360;
    sendJoystickState(headingDeg, true);
}

function sendJoystickState(heading, active) {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.update_joystick(heading, active);
    }
}
