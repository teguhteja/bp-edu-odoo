/** @odoo-module **/
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

// "Ask AI" button in the chatter, opening the agent conversation in Discuss.
patch(Chatter.prototype, {
    setup() {
        super.setup();
        this.ehAiChat = useService("eh_ai.chat");
    },
    onClickAskAi() {
        this.ehAiChat.open();
    },
});
