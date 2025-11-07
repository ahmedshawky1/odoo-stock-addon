// Small fallback to show login form when Owl user switch doesn't mount
(function () {
    try {
        document.addEventListener('DOMContentLoaded', function () {
            // If the owl-component didn't render the login widget, reveal the classic form
            var loginForm = document.querySelector('form.oe_login_form');
            if (loginForm && loginForm.classList.contains('d-none')) {
                // Also ensure we don't reveal it if the page intends to show quick-login or SSO
                loginForm.classList.remove('d-none');
            }
        });
    } catch (e) {
        // silent fallback
        console.error('login_fallback error', e);
    }
})();
