document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("login-form");
    const password = document.getElementById("id_password");
    const toggle = document.getElementById("password-toggle");
    const submitButton = document.getElementById("sign-in-button");

    if (password && toggle) {
        toggle.addEventListener("click", () => {
            const isVisible = password.type === "text";
            password.type = isVisible ? "password" : "text";
            toggle.setAttribute("aria-pressed", String(!isVisible));
            toggle.setAttribute("aria-label", isVisible ? "Show password" : "Hide password");
            toggle.querySelector("i").className = isVisible ? "bi bi-eye" : "bi bi-eye-slash";
            password.focus();
        });
    }

    if (form && submitButton) {
        form.addEventListener("submit", () => {
            if (!form.checkValidity()) {
                return;
            }
            submitButton.disabled = true;
            submitButton.classList.add("is-loading");
            submitButton.setAttribute("aria-busy", "true");
        });
    }
});
