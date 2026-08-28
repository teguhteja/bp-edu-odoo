// Copyright 2026. Developed and maintained by Simplify It S.R.L. (https://simplifyit.com.bo)

import { Component, onWillUnmount, useRef, useState } from "@odoo/owl";
import { user } from "@web/core/user";
import { url } from "@web/core/utils/urls";
import { useService } from "@web/core/utils/hooks";
import { useHotkey } from "@web/core/hotkeys/hotkey_hook";
import { useSortable } from "@web/core/utils/sortable_owl";
import { computeAppsAndMenuItems, reorderApps } from "@web/webclient/menus/menu_helpers";

const COLLAPSED_KEY = "slt_sidebar_collapsed";

/**
 * Linear style sidebar: brand header, command palette trigger, app list
 * with the active app expanded to its full menu tree (collapsible groups),
 * and a user footer. Collapsible to an icon rail (Ctrl+B).
 *
 * The sidebar fully replaces the navbar app/section menus on desktop, so
 * it must expose every menu item that has an action somewhere below it.
 */
export class LinearSidebar extends Component {
    static template = "simplifyit_linear_backend_theme.LinearSidebar";
    static props = {};

    setup() {
        this.menuService = useService("menu");
        this.commandService = useService("command");
        this.state = useState({
            collapsed: window.localStorage.getItem(COLLAPSED_KEY) === "1",
            expandedAppId: this.menuService.getCurrentApp()?.id || null,
            openGroups: {},
            activeMenuId: null,
            flyoutAppId: null,
            flyoutTop: 0,
            reordering: false,
            // Local copy of the persisted order, kept in reactive state so a
            // drop is reflected immediately instead of waiting for whatever
            // next triggers a render (`user.settings` itself isn't reactive).
            menuOrder: JSON.parse(user.settings?.homemenu_config || "null"),
        });
        this.navRef = useRef("navRef");
        this.flyoutCloseTimer = null;
        this.userName = user.name;
        this.userLogin = user.login;
        this.companyName = user.activeCompany?.name || "";
        this.avatarUrl = url("/web/image", {
            model: "res.users",
            field: "avatar_128",
            id: user.userId,
        });
        useHotkey("control+b", () => this.toggleCollapsed(), { global: true });
        useSortable({
            enable: () => this.state.reordering,
            ref: this.navRef,
            elements: ".slt_app",
            cursor: "move",
            delay: 100,
            tolerance: 10,
            onWillStartDrag: (params) => this._sortStart(params),
            onDrop: (params) => this._sortAppDrop(params),
        });
        const onAppChanged = () => {
            this.state.expandedAppId = this.menuService.getCurrentApp()?.id || null;
            this.state.openGroups = {};
            this.state.activeMenuId = null;
            this.state.flyoutAppId = null;
        };
        this.env.bus.addEventListener("MENUS:APP-CHANGED", onAppChanged);
        onWillUnmount(() => {
            this.env.bus.removeEventListener("MENUS:APP-CHANGED", onAppChanged);
            clearTimeout(this.flyoutCloseTimer);
        });
    }

    get apps() {
        const menuItems = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        const apps = menuItems.apps;
        if (this.state.menuOrder) {
            reorderApps(apps, this.state.menuOrder);
        }
        return apps;
    }

    get currentAppId() {
        return this.menuService.getCurrentApp()?.id;
    }

    /**
     * Full menu tree of the given app as view-model nodes, pruned to the
     * branches that lead to at least one actionable menu.
     */
    getMenuNodes(appId) {
        const tree = this.menuService.getMenuAsTree(appId);
        return this._buildNodes(tree.childrenTree || []);
    }

    _buildNodes(menus) {
        const nodes = [];
        for (const menu of menus) {
            const children = this._buildNodes(menu.childrenTree || []);
            if (!menu.actionID && !children.length) {
                continue;
            }
            nodes.push({
                id: menu.id,
                name: menu.name,
                actionID: menu.actionID,
                menu,
                children,
            });
        }
        return nodes;
    }

    onAppClick(app) {
        if (this.state.reordering) {
            return;
        }
        if (app.id === this.state.expandedAppId && app.id === this.currentAppId) {
            this.state.expandedAppId = null;
            return;
        }
        this.state.expandedAppId = app.id;
        this.menuService.selectMenu(app);
    }

    onNodeClick(node) {
        if (node.children.length) {
            this.state.openGroups = {
                ...this.state.openGroups,
                [node.id]: !this.state.openGroups[node.id],
            };
        }
        if (node.actionID) {
            this.state.activeMenuId = node.id;
            this.menuService.selectMenu(node.menu);
            this.state.flyoutAppId = null;
        }
    }

    /**
     * Collapsed rail: hovering an app icon opens a flyout with its full
     * menu tree, Windows-taskbar style, so apps stay navigable without
     * expanding the whole sidebar.
     */
    onAppMouseEnter(app, ev) {
        if (!this.state.collapsed || this.state.reordering) {
            return;
        }
        clearTimeout(this.flyoutCloseTimer);
        const rect = ev.currentTarget.getBoundingClientRect();
        // Pop the flyout out to the side of the icon, aligned with its top.
        // Keep its header on-screen even for apps near the bottom of a long
        // list; the body scrolls if it's taller than that.
        this.state.flyoutTop = Math.min(rect.top, window.innerHeight - 60);
        this.state.flyoutAppId = app.id;
    }

    onAppMouseLeave() {
        if (!this.state.collapsed) {
            return;
        }
        this._scheduleFlyoutClose();
    }

    onFlyoutMouseEnter() {
        clearTimeout(this.flyoutCloseTimer);
    }

    onFlyoutMouseLeave() {
        this._scheduleFlyoutClose();
    }

    _scheduleFlyoutClose() {
        clearTimeout(this.flyoutCloseTimer);
        this.flyoutCloseTimer = setTimeout(() => {
            this.state.flyoutAppId = null;
        }, 150);
    }

    openCommandPalette() {
        this.commandService.openMainPalette({});
    }

    toggleCollapsed() {
        this.state.collapsed = !this.state.collapsed;
        this.state.flyoutAppId = null;
        window.localStorage.setItem(COLLAPSED_KEY, this.state.collapsed ? "1" : "0");
    }

    /**
     * Per-user app order, editable via drag and drop (like Odoo Enterprise's
     * Home Menu). Persisted through the same `homemenu_config` user setting
     * Enterprise uses, so an order set there or here shows up in both.
     */
    toggleReordering() {
        this.state.reordering = !this.state.reordering;
        if (this.state.reordering) {
            this.state.expandedAppId = null;
            this.state.flyoutAppId = null;
        }
    }

    _sortStart({ element, addClass }) {
        addClass(element.children[0], "slt_dragged_app");
    }

    _sortAppDrop({ element, previous }) {
        const order = this.apps.map((app) => app.xmlid);
        const elementId = element.children[0].dataset.menuXmlid;
        const elementIndex = order.indexOf(elementId);
        order.splice(elementIndex, 1);
        if (previous) {
            const prevIndex = order.indexOf(previous.children[0].dataset.menuXmlid);
            order.splice(prevIndex + 1, 0, elementId);
        } else {
            order.splice(0, 0, elementId);
        }
        this.state.menuOrder = order;
        user.setUserSettings("homemenu_config", JSON.stringify(order));
    }
}
