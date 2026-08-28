/** @odoo-module **/
// Copyright 2014-2021 Tecnativa
// Migrated to the Odoo 19 Chatter (OWL, non-messaging) architecture.

import { Chatter } from "@mail/chatter/web_portal/chatter";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(Chatter.prototype, {
    setup() {
        super.setup(...arguments);
        this.documentUrlAction = useService("action");
    },

    onClickAddUrl() {
        this.documentUrlAction.doAction("document_url.action_ir_attachment_add_url", {
            additionalContext: {
                active_id: this.state.thread.id,
                active_ids: [this.state.thread.id],
                active_model: this.state.thread.model,
            },
            onClose: () => this.load(this.state.thread, ["attachments"]),
        });
    },
});
