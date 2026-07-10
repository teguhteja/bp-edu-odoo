/** @odoo-module **/
import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class EhAiPromptDialog extends Component {
    static template = "eh_ai.EditorPromptDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        confirm: { type: Function },
        title: { type: String, optional: true },
        placeholder: { type: String, optional: true },
    };

    setup() {
        this.state = useState({ value: "" });
        this.inputRef = useRef("input");
        onMounted(() => this.inputRef.el && this.inputRef.el.focus());
    }

    onConfirm() {
        const value = this.state.value.trim();
        this.props.close();
        this.props.confirm(value);
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && (ev.ctrlKey || ev.metaKey)) {
            ev.preventDefault();
            this.onConfirm();
        }
    }
}
