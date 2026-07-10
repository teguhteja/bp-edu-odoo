/** @odoo-module **/
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

// "Ask AI" entry in the command palette (Ctrl/Cmd-K and the search dropdown).
registry.category("command_provider").add("eh_ai", {
    provide: (env) => [
        {
            name: _t("Ask AI"),
            action() {
                env.services["eh_ai.chat"].open({});
            },
        },
    ],
});
