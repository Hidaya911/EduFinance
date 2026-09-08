(() => {
    const menu = document.querySelector('[data-receipt-menu]');
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.querySelector('.receipt-menu-backdrop');
    if (menu && sidebar && backdrop) {
        sidebar.id = 'receiptMobileNavigation';
        const closeMenu = () => {
            document.body.classList.remove('receipt-menu-open');
            menu.setAttribute('aria-expanded', 'false');
            backdrop.hidden = true;
        };
        menu.addEventListener('click', () => {
            const open = !document.body.classList.contains('receipt-menu-open');
            document.body.classList.toggle('receipt-menu-open', open);
            menu.setAttribute('aria-expanded', String(open));
            backdrop.hidden = !open;
            if (open) sidebar.querySelector('a')?.focus();
        });
        backdrop.addEventListener('click', () => { closeMenu(); menu.focus(); });
        document.addEventListener('keydown', event => {
            if (event.key === 'Escape' && document.body.classList.contains('receipt-menu-open')) {
                closeMenu(); menu.focus();
            }
        });
        window.addEventListener('resize', () => { if (window.innerWidth > 760) closeMenu(); });
    }
    const form = document.getElementById("receiptFilters");
    if (form) {
        let timer;
        const submit = () => { clearTimeout(timer); if (form.reportValidity()) form.requestSubmit(); };
        form.querySelector('input[name="q"]').addEventListener("input", event => {
            clearTimeout(timer);
            if (!event.isComposing) timer = setTimeout(submit, 350);
        });
        form.querySelectorAll('select, input[type="date"]').forEach(field => field.addEventListener("change", submit));
    }
    const buttons = document.querySelectorAll("[data-receipt-print]");
    const print = async () => {
        buttons.forEach(button => { button.disabled = true; });
        await document.fonts.ready;
        await Promise.all(Array.from(document.querySelectorAll('.receipt-paper img')).map(img => img.decode().catch(() => {})));
        window.print();
        buttons.forEach(button => { button.disabled = false; });
    };
    buttons.forEach(button => button.addEventListener("click", print));
    document.querySelectorAll('.receipt-school-logo').forEach(img => img.addEventListener('error', () => { img.hidden = true; }));
    if (document.body.hasAttribute("data-receipt-auto-print")) {
        if (document.readyState === "complete") print();
        else window.addEventListener("load", print, { once: true });
    }
})();
