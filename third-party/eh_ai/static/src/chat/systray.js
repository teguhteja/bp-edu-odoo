/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// "Ask AI" button in the top systray, available on every backend screen.
export class EhAiSystray extends Component {
    static template = "eh_ai.Systray";
    static props = {};

    setup() {
        this.chat = useService("eh_ai.chat");
    }

    onClick() {
        this.chat.open({});
    }
}

registry.category("systray").add(
    "eh_ai.systray", { Component: EhAiSystray }, { sequence: 30 });
