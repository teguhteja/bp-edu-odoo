// Copyright 2026. Developed and maintained by Simplify It S.R.L. (https://simplifyit.com.bo)

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { cookie } from "@web/core/browser/cookie";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";

function systemColorScheme() {
    return browser.matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light";
}

/**
 * Light/dark toggle placed just before the Discuss systray icon.
 *
 * The dark tokens live in the separate `web.assets_web_dark` bundle
 * (server-selected via `ir.http.color_scheme()`, see models/ir_http.py),
 * so switching theme requires a reload — there is no live CSS swap.
 *
 * If `web_enterprise`'s own `color_scheme` service is present, it recomputes
 * the cookie from `res.users.settings.color_scheme` on every boot and would
 * otherwise silently revert this toggle on the next navigation; persisting
 * through `user.setUserSettings` keeps both mechanisms in sync.
 */
export class DarkModeToggle extends Component {
    static template = "simplifyit_linear_backend_theme.DarkModeToggle";
    static props = {};

    get isDark() {
        return (cookie.get("color_scheme") || systemColorScheme()) === "dark";
    }

    /**
     * Built here rather than in the template: a `t-att-title` holding a JS
     * expression is not extracted for translation, so the label would be
     * frozen in English. `_t()` in the component is picked up by the export.
     */
    get label() {
        return this.isDark ? _t("Switch to light theme") : _t("Switch to dark theme");
    }

    async onClick() {
        const next = this.isDark ? "light" : "dark";
        cookie.set("color_scheme", next);
        if ("color_scheme" in this.env.services) {
            try {
                await user.setUserSettings("color_scheme", next);
            } catch {
                // web_enterprise present but settings write failed; the
                // cookie override in ir_http.py still makes the toggle work.
            }
        }
        browser.location.reload();
    }
}

registry.category("systray").add(
    "simplifyit_linear_backend_theme.DarkModeToggle",
    { Component: DarkModeToggle },
    { sequence: 26 }
);
