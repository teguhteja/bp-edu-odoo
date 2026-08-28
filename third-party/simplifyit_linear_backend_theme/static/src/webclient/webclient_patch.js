// Copyright 2026. Developed and maintained by Simplify It S.R.L. (https://simplifyit.com.bo)

import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";
import { session } from "@web/session";
import { LinearSidebar } from "@simplifyit_linear_backend_theme/webclient/sidebar/sidebar";
import { applyPalette } from "@simplifyit_linear_backend_theme/webclient/palette/palette";

/**
 * Register the Linear sidebar on the web client, and apply the current
 * company's accent palette (see models/ir_http.py session_info()) before the
 * first render, to avoid a flash of the default indigo accent.
 *
 * web_enterprise's WebClientEnterprise snapshots `...WebClient.components`
 * at module-load time, so patching the static object only works if this
 * module happens to execute first — the bundle order is not guaranteed.
 * Injecting at setup() time instead is order-independent and lands on the
 * actual class in use (WebClient on Community, WebClientEnterprise on
 * Enterprise), since both share this prototype method.
 */
patch(WebClient.prototype, {
    setup() {
        applyPalette(session.slt_palette);
        const cls = this.constructor;
        if (!cls.components.LinearSidebar) {
            cls.components = { ...cls.components, LinearSidebar };
        }
        super.setup();
    },
});
