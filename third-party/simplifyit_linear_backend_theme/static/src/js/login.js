// Copyright 2026. Developed and maintained by Simplify It S.R.L. (https://simplifyit.com.bo)

/*
 * Login page enhancement (vanilla JS, no OWL — the login page is public).
 * The show/hide behaviour itself is native (web/static/src/public/
 * show_password.js); this only keeps an accessible, localized aria-label in
 * sync with the current state. Tolerant to pages without the elements.
 *
 * The label text itself comes from the text content of two hidden
 * data-sit-password-label divs set in login_templates.xml (next to the
 * button), so it goes through Odoo's normal view translation mechanism
 * (i18n/*.po) instead of being hardcoded here.
 */
(function () {
    "use strict";

    function syncLabel(button, input, labels) {
        var hidden = input.type === "password";
        var label = labels[hidden ? "show" : "hide"];
        if (label) {
            button.setAttribute("aria-label", label.textContent);
        }
        button.setAttribute("aria-pressed", hidden ? "false" : "true");
    }

    document.addEventListener("DOMContentLoaded", function () {
        document
            .querySelectorAll(".oe_login_form .o_show_password, .oe_signup_form .o_show_password")
            .forEach(function (button) {
                var group = button.closest(".input-group");
                var input = group && group.querySelector("input");
                var labels = {
                    show: group && group.querySelector('[data-sit-password-label="show"]'),
                    hide: group && group.querySelector('[data-sit-password-label="hide"]'),
                };
                if (!input) {
                    return;
                }
                syncLabel(button, input, labels);
                button.addEventListener("click", function () {
                    // The native handler flips input.type; sync afterwards.
                    window.setTimeout(function () {
                        syncLabel(button, input, labels);
                    }, 0);
                });
            });
    });
})();
