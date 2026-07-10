/** @odoo-module **/
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { EhAiAgentPickerDialog } from "./agent_picker_dialog";

// Opens an AI agent conversation as a floating Discuss chat window (over the
// current screen), used by the systray, command palette, chatter and search.
export const ehAiChatService = {
    dependencies: ["orm", "mail.store", "dialog", "notification"],
    start(env, deps) {
        const { orm, dialog, notification } = deps;
        const store = deps["mail.store"];

        async function openAgent(agentId) {
            const channelId = await orm.call("eh.ai.agent", "eh_ai_channel_id", [[agentId]]);
            const thread = await store.Thread.getOrFetch({ model: "discuss.channel", id: channelId });
            if (thread) {
                await thread.openChatWindow({ focus: true });
            }
        }

        return {
            openAgent,
            async open() {
                const agents = await orm.searchRead(
                    "eh.ai.agent", [["active", "=", true]], ["id", "name"]);
                if (!agents.length) {
                    notification.add(_t("No AI agents are configured yet."), { type: "warning" });
                    return;
                }
                if (agents.length === 1) {
                    await openAgent(agents[0].id);
                    return;
                }
                dialog.add(EhAiAgentPickerDialog, {
                    agents,
                    select: (id) => openAgent(id),
                });
            },
        };
    },
};

registry.category("services").add("eh_ai.chat", ehAiChatService);
