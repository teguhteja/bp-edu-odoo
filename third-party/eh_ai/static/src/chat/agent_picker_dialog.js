/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class EhAiAgentPickerDialog extends Component {
    static template = "eh_ai.AgentPickerDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        agents: { type: Array },
        select: { type: Function },
    };

    setup() {
        this.state = useState({ agentId: this.props.agents[0] && this.props.agents[0].id });
    }

    onChange(ev) {
        this.state.agentId = parseInt(ev.target.value, 10);
    }

    onConfirm() {
        if (this.state.agentId) {
            this.props.select(this.state.agentId);
        }
        this.props.close();
    }
}
