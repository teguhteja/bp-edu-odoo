import { expect, test } from "@odoo/hoot";

import { browser } from "@web/core/browser/browser";
import { Chatter } from "@mail/chatter/web_portal/chatter";

import "@sbs_custom_style/chatter/chatter/chatter";

test.tags("sbs_custom_style_chatter");
test("notifications toggle updates localStorage and state", async () => {
    browser.localStorage.removeItem("sbs_custom_style.notifications");
    browser.localStorage.setItem(
        "sbs_custom_style.notifications", JSON.stringify(false)
    );
    const chatter = {
        state: {
            sbsShowNotificationMessages: false,
        },
    };
    Chatter.prototype.onClickSbsNotificationsToggle.call(chatter);
    expect(chatter.state.sbsShowNotificationMessages).toBe(true);
    expect(
        JSON.parse(browser.localStorage.getItem(
            "sbs_custom_style.notifications"
        ))
    ).toBe(true);
    Chatter.prototype.onClickSbsNotificationsToggle.call(chatter);
    expect(chatter.state.sbsShowNotificationMessages).toBe(false);
    expect(
        JSON.parse(browser.localStorage.getItem(
            "sbs_custom_style.notifications"
        ))
    ).toBe(false);
});
