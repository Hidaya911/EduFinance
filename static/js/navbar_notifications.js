(() => {
    const toggle = document.getElementById("eduNotificationToggle");
    const panel = document.getElementById("eduNotificationPanel");
    if (!toggle || !panel) return;

    // A body-level panel avoids clipping by the shared workspace's overflow.
    document.body.appendChild(panel);

    function positionPanel() {
        const anchor = toggle.getBoundingClientRect();
        const margin = 12;
        const top = Math.max(margin, Math.min(anchor.bottom + 10, window.innerHeight - 100));
        panel.style.left = `${Math.max(margin, Math.min(anchor.right - panel.offsetWidth, window.innerWidth - panel.offsetWidth - margin))}px`;
        panel.style.top = `${top}px`;
        panel.style.maxHeight = `${Math.max(0, window.innerHeight - top - margin)}px`;
    }

    function closePanel(restoreFocus = false) {
        panel.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
        if (restoreFocus) toggle.focus();
    }

    toggle.addEventListener("click", () => {
        if (!panel.hidden) return closePanel();
        panel.hidden = false;
        toggle.setAttribute("aria-expanded", "true");
        positionPanel();
        panel.querySelector("a")?.focus({ preventScroll: true });
    });
    document.addEventListener("click", event => {
        if (!panel.hidden && !panel.contains(event.target) && !toggle.contains(event.target)) closePanel();
    });
    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && !panel.hidden) {
            event.preventDefault();
            closePanel(true);
        }
    });
    document.addEventListener("focusin", event => {
        if (!panel.hidden && !panel.contains(event.target) && !toggle.contains(event.target)) closePanel();
    });
    window.addEventListener("resize", () => { if (!panel.hidden) positionPanel(); });
    window.addEventListener("scroll", event => {
        if (!panel.hidden && !panel.contains(event.target)) closePanel();
    }, true);
    window.addEventListener("pageshow", () => closePanel());
})();
