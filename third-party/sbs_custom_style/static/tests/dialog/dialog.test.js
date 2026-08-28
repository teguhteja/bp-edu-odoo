import { session } from "@web/session";
import { expect, test } from "@odoo/hoot";

import { Component, xml } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

import { defineMailModels } from "@mail/../tests/mail_test_helpers";

import {
    contains,
    makeDialogMockEnv,
    mountWithCleanup
} from "@web/../tests/web_test_helpers";

import "@sbs_custom_style/dialog/core/dialog/dialog";

defineMailModels();

test.tags("sbs_custom_style_dialog");
test("dialog size toggle switches between fullscreen and initial size", async () => {
    const realDialogSize = session.sbs_dialog_size;
    try {
        session.sbs_dialog_size = "maximize";

        class Parent extends Component {
            static components = { Dialog };
            static template = xml`
                <Dialog title="'Hello'">
                    Hello
                </Dialog>
            `;
            static props = ["*"];
        }

        await makeDialogMockEnv();
        await mountWithCleanup(Parent);
        expect(".o_dialog").toHaveCount(1);
        expect(".o_dialog .sbs_btn_dialog_size").toHaveCount(1);
        expect(".o_dialog .modal-fs").toHaveCount(1);
        expect(".o_dialog .sbs_btn_dialog_size i.fa-compress").toHaveCount(1);
        await contains(".o_dialog .sbs_btn_dialog_size").click();
        expect(".o_dialog .modal-lg").toHaveCount(1);
        expect(".o_dialog .sbs_btn_dialog_size i.fa-expand").toHaveCount(1);
        await contains(".o_dialog .sbs_btn_dialog_size").click();
        expect(".o_dialog .modal-fs").toHaveCount(1);
        expect(".o_dialog .sbs_btn_dialog_size i.fa-compress").toHaveCount(1);
    } finally {
        session.sbs_dialog_size = realDialogSize;
    }
});
