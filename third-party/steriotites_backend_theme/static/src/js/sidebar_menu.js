/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";
import { useState } from "@odoo/owl";
// import { registry } from "@web/core/registry";
// import { router, routerBus } from "@web/core/browser/router";



patch(WebClient.prototype, {
    async setup() {
        super.setup();

        this.menuService = this.env.services.menu;

        this.user = user;


        this.state.sidebarOpen = false;
        this.state.sidebarMini = false;

        this.state.allAppsOpen = true;

        this.state.currentAppSections = [];
        this._updateCurrentAppSections();

        this.state.currentAppId = this.menuService.getCurrentApp()?.id;
        this.env.bus.addEventListener(
            "MENUS:APP-CHANGED",
            this._onMenuChanged.bind(this)
        );



        this.env.bus.addEventListener(
            "MENUS:APP-CHANGED",
            this._onMenuChanged.bind(this)
        );


    },


    toggleSidebar() {
        this.state.sidebarOpen = !this.state.sidebarOpen;
    },

    toggleMiniSidebar() {
        this.state.sidebarMini = !this.state.sidebarMini;
    },
    toggleAllAppsOpen() {
        this.state.allAppsOpen = !this.state.allAppsOpen;
    },
    _updateCurrentAppSections() {
        const currentApp = this.menuService.getCurrentApp();
        if (!currentApp) {
            this.state.currentAppSections = [];
            return;
        }

        const tree = this.menuService.getMenuAsTree(currentApp.id);
        this.state.currentAppSections = tree?.childrenTree || [];
    },




    _onMenuChanged() {
        const currentApp = this.menuService.getCurrentApp();
        this.state.currentAppId = currentApp?.id || null;

        this._updateCurrentAppSections();
    },


    onSidebarMenuSelection(menu, close=false) {
        if (!menu) return;

        const actionableMenu = this._findFirstActionMenu(menu);
        if (actionableMenu) {
            this.menuService.selectMenu(actionableMenu);

            if (actionableMenu.appID) {
                this.menuService.setCurrentMenu(actionableMenu.appID);
                if (close) {
                    this.state.sidebarOpen = false;
                }
            }
            this.env.bus.trigger("MENU:CHANGED");
        }
    },

    _findFirstActionMenu(menu) {
        if (menu.actionID) {
            return menu;
        }
        if (!menu.childrenTree) {
            return null;
        }
        for (const child of menu.childrenTree) {
            const found = this._findFirstActionMenu(child);
            if (found) return found;
        }
        return null;
    },

    _getMenuIcon(menu) {
        if (menu.webIconData) {
            return menu.webIconData;
        }
        if (menu.webIcon) {
            return `/web/image/${menu.webIcon}`;
        }
        return "/web/static/img/menu_icon.svg";
    },

});
