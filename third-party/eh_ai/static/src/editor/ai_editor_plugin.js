/** @odoo-module **/
import { Plugin } from "@html_editor/plugin";
import { HtmlField } from "@html_editor/fields/html_field";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { withSequence } from "@html_editor/utils/resource";
import { rpc } from "@web/core/network/rpc";
import { EhAiPromptDialog } from "./ai_prompt_dialog";

// Adds "/AI" powerbox commands to backend HTML fields: write new text from an
// instruction, or rephrase the current selection. Generation goes through the
// engine controller, so it is governed by the usual budgets and usage logging.
export class EhAiEditorPlugin extends Plugin {
    static id = "eh_ai_editor";
    static dependencies = ["selection", "history", "dom", "delete"];

    resources = {
        user_commands: [
            {
                id: "ehAiWrite",
                title: _t("Write with AI"),
                description: _t("Generate text from an instruction"),
                icon: "fa-magic",
                run: this.writeWithAi.bind(this),
            },
            {
                id: "ehAiRephrase",
                title: _t("Rephrase with AI"),
                description: _t("Rewrite the selected text"),
                icon: "fa-magic",
                run: this.rephraseWithAi.bind(this),
            },
        ],
        powerbox_categories: withSequence(80, { id: "eh_ai", name: _t("AI") }),
        powerbox_items: [
            {
                categoryId: "eh_ai",
                commandId: "ehAiWrite",
                keywords: [_t("ai"), _t("write"), _t("draft")],
            },
            {
                categoryId: "eh_ai",
                commandId: "ehAiRephrase",
                keywords: [_t("ai"), _t("rephrase"), _t("improve")],
            },
        ],
    };

    async _defaultAgent() {
        const agents = await this.services.orm.searchRead(
            "eh.ai.agent", [["active", "=", true]], ["id", "name"], { limit: 1 });
        if (!agents.length) {
            this.services.notification.add(_t("No AI agents are configured yet."), { type: "warning" });
            return null;
        }
        return agents[0];
    }

    async _ask(agentId, message) {
        const result = await rpc("/eh_ai/agent/message", { agent_id: agentId, message });
        return result.text || "";
    }

    _notifyError(error) {
        const message = (error && error.data && error.data.message) || error.message || String(error);
        this.services.notification.add(_t("AI error: %s", message), { type: "danger" });
    }

    _restore(selection) {
        try {
            this.dependencies.selection.setSelection(selection);
        } catch {
            // selection may be stale; insertion falls back to the live cursor
        }
    }

    async writeWithAi() {
        const agent = await this._defaultAgent();
        if (!agent) {
            return;
        }
        const cursor = this.dependencies.selection.getEditableSelection();
        this.services.dialog.add(EhAiPromptDialog, {
            title: _t("Write with AI"),
            placeholder: _t("Describe what to write…"),
            confirm: async (instruction) => {
                if (!instruction) {
                    return;
                }
                let text;
                try {
                    text = await this._ask(agent.id, instruction);
                } catch (error) {
                    this._notifyError(error);
                    return;
                }
                if (!text) {
                    return;
                }
                this._restore(cursor);
                this.dependencies.dom.insert(text);
                this.dependencies.history.addStep();
            },
        });
    }

    async rephraseWithAi() {
        const agent = await this._defaultAgent();
        if (!agent) {
            return;
        }
        const selection = this.dependencies.selection.getEditableSelection();
        const selected = selection.textContent ? selection.textContent() : "";
        if (!selected || !selected.trim()) {
            this.services.notification.add(_t("Select some text to rephrase first."), { type: "warning" });
            return;
        }
        let text;
        try {
            text = await this._ask(
                agent.id,
                "Rephrase the following text to be clear and professional. " +
                    "Return only the rewritten text, with no preamble:\n\n" + selected);
        } catch (error) {
            this._notifyError(error);
            return;
        }
        if (!text) {
            return;
        }
        this._restore(selection);
        const current = this.dependencies.selection.getEditableSelection();
        if (!current.isCollapsed) {
            this.dependencies.delete.deleteSelection(current);
        }
        this.dependencies.dom.insert(text);
        this.dependencies.history.addStep();
    }
}

// Backend HTML fields build their editor from MAIN_PLUGINS plus this.props.
// editorConfig; there is no plugin registry, so append our plugin in getConfig.
patch(HtmlField.prototype, {
    getConfig() {
        const config = super.getConfig();
        config.Plugins = [...config.Plugins, EhAiEditorPlugin];
        return config;
    },
});
