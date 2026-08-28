import { patch } from '@web/core/utils/patch';
import { useBus, useService } from '@web/core/utils/hooks';

import { NavBar } from '@web/webclient/navbar/navbar';
import { AppsMenu } from "@sbs_custom_style/theme/webclient/appsmenu/appsmenu";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.appMenuService = useService('sbs_custom_style.app_menu');
        useBus(this.env.bus, 'ACTION_MANAGER:UI-UPDATED', () => this.render());
    },

    _sbsMenuContainsAction(menu, actionId) {
        if (!menu || !actionId) {
            return false;
        }
        if (Number(menu.actionID) === Number(actionId)) {
            return true;
        }
        return (menu.childrenTree || []).some((child) =>
            this._sbsMenuContainsAction(child, actionId)
        );
    },

    isSbsSectionActive(section) {
        const actionId = this.actionService.currentController?.action?.id;
        return this._sbsMenuContainsAction(section, actionId);
    },

    isSbsMenuItemActive(item) {
        const actionId = this.actionService.currentController?.action?.id;
        return Boolean(actionId) && Number(item?.actionID) === Number(actionId);
    },

    isSbsAnySectionActive(sections) {
        return sections.some((section) => this.isSbsSectionActive(section));
    },
});

patch(NavBar, {
    components: {
        ...NavBar.components,
        AppsMenu,
    },
});
