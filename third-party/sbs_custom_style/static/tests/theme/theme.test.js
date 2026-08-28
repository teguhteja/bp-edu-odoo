import { expect, test } from "@odoo/hoot";

import "@sbs_custom_style/appsbar/webclient/menus/app_menu_service";
import "@sbs_custom_style/theme/webclient/navbar/navbar";

import { NavBar } from "@web/webclient/navbar/navbar";
import { AppsMenu } from "@sbs_custom_style/theme/webclient/appsmenu/appsmenu";

test.tags("sbs_custom_style_theme");
test("navbar uses AppsMenu component", async () => {
    expect(NavBar.components.AppsMenu).toBe(AppsMenu);
});

test("navbar identifies the active top-level section", () => {
    const context = {
        actionService: { currentController: { action: { id: 42 } } },
        _sbsMenuContainsAction: NavBar.prototype._sbsMenuContainsAction,
    };
    const section = {
        actionID: false,
        childrenTree: [{ actionID: 42, childrenTree: [] }],
    };

    expect(NavBar.prototype.isSbsSectionActive.call(context, section)).toBe(true);
});

test("navbar rejects a section unrelated to the current action", () => {
    const context = {
        actionService: { currentController: { action: { id: 42 } } },
        _sbsMenuContainsAction: NavBar.prototype._sbsMenuContainsAction,
    };
    const section = { actionID: 7, childrenTree: [] };

    expect(NavBar.prototype.isSbsSectionActive.call(context, section)).toBe(false);
});

test("navbar identifies the active submenu item", () => {
    const context = {
        actionService: { currentController: { action: { id: 42 } } },
    };

    expect(
        NavBar.prototype.isSbsMenuItemActive.call(context, { actionID: 42 })
    ).toBe(true);
    expect(
        NavBar.prototype.isSbsMenuItemActive.call(context, { actionID: 7 })
    ).toBe(false);
});
