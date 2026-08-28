import { patch } from '@web/core/utils/patch';
import { browser } from '@web/core/browser/browser';

import { Chatter } from '@mail/chatter/web_portal/chatter';
import { RecipientsList } from '@sbs_custom_style/chatter/core/recipients_list/recipients_list';

patch(Chatter.prototype, {
    setup() {
        super.setup(...arguments);
        const sbsShowNotificationMessages = browser.localStorage.getItem(
            'sbs_custom_style.notifications'
        );
        this.state.sbsShowNotificationMessages = (
            sbsShowNotificationMessages != null ?
            JSON.parse(sbsShowNotificationMessages) : true
        );
        this.state.sbsNotifyInternalFollowers = false;
    },
    onClickSbsNotificationsToggle() {
        const sbsShowNotificationMessages = !this.state.sbsShowNotificationMessages;
        browser.localStorage.setItem(
            'sbs_custom_style.notifications', sbsShowNotificationMessages
        );
        this.state.sbsShowNotificationMessages = sbsShowNotificationMessages;
    },
});

Object.assign(Chatter.components, {
    RecipientsList,
});
