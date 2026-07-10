/** @odoo-module **/
import { Thread } from "@mail/core/common/thread_model";
import { fields } from "@mail/model/misc";
import { patch } from "@web/core/utils/patch";

// An AI agent cannot take an audio/video call, so hide the call buttons on its
// chat window (allowCalls already excludes OdooBot the same way).
patch(Thread.prototype, {
    setup() {
        super.setup();
        this.eh_ai_is_agent = fields.Attr(false);
    },
    get allowCalls() {
        return super.allowCalls && !this.eh_ai_is_agent;
    },
});
