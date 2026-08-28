/** @odoo-module **/

import { registry } from "@web/core/registry";

const CHATTER_SELECTOR = ".o-mail-Chatter";
const FORM_RENDERER_SELECTOR = ".o_form_renderer";
const CHATTER_ROW_CLASS = "o_chatter_toggle_row";
const READY_CLASS = "my_hide_chatter_ready";
const STORAGE_PREFIX = "my_hide_chatter_hidden";
const BTN_ID = "my_hide_chatter_global_btn";

const ANCHOR_SELECTORS = [
    ".o_control_panel .o_pager",
    ".o_control_panel .o_cp_pager",
    ".o_control_panel_actions",
    ".o_control_panel",
];

function getScopeKey() {
    try {
        const hashMatch = (window.location.hash || "").match(/[#&]model=([^&]+)/);
        if (hashMatch) {
            return decodeURIComponent(hashMatch[1]);
        }
        const path = window.location.pathname.replace(/\/+$/, "");
        const parts = path.split("/").filter(Boolean);
        if (parts.length && /^\d+$/.test(parts[parts.length - 1])) {
            parts.pop(); 
        }
        return parts.join("/") || "default";
    } catch (e) {
        return "default";
    }
}

function getStoredPref() {
    try {
        return window.localStorage.getItem(`${STORAGE_PREFIX}:${getScopeKey()}`) === "1";
    } catch (e) {
        return false;
    }
}

function setStoredPref(hidden) {
    try {
        window.localStorage.setItem(`${STORAGE_PREFIX}:${getScopeKey()}`, hidden ? "1" : "0");
    } catch (e) {
    }
}

function getVisibleFormRenderer() {
    const roots = document.querySelectorAll(FORM_RENDERER_SELECTOR);
    for (const el of roots) {
        if (el.offsetParent !== null) {
            return el;
        }
    }
    return null;
}

function getAnchor() {
    for (const sel of ANCHOR_SELECTORS) {
        const el = document.querySelector(sel);
        if (el) {
            return el;
        }
    }
    return null;
}

function setButtonState(btn, hidden) {
    const icon = btn.querySelector("i");
    if (icon) {
        icon.className = hidden ? "fa fa-eye-slash" : "fa fa-eye";
    }
    btn.classList.toggle("my_hide_chatter_btn_active", hidden);
    btn.title = hidden ? "Show chatter" : "Hide chatter";
}

function createGlobalButton() {
    let btn = document.getElementById(BTN_ID);
    if (btn) {
        return btn;
    }

    btn = document.createElement("button");
    btn.id = BTN_ID;
    btn.type = "button";
    btn.className = "my_hide_chatter_btn";

    const icon = document.createElement("i");
    btn.appendChild(icon);
    setButtonState(btn, getStoredPref());

    btn.addEventListener("click", (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        const root = getVisibleFormRenderer();
        if (!root) {
            return;
        }
        const hidden = root.classList.toggle("o_chatter_hidden");
        root.classList.add(READY_CLASS);
        setButtonState(btn, hidden);
        setStoredPref(hidden);
    });

    return btn;
}

function dockButton(btn) {
    const root = getVisibleFormRenderer();
    const anchor = getAnchor();

    if (!root || !anchor) {
        btn.style.display = "none";
        return;
    }

    if (btn.parentElement !== anchor) {
        anchor.appendChild(btn);
    }
    btn.style.display = "inline-flex";
    setButtonState(btn, root.classList.contains("o_chatter_hidden"));
}

function applyStoredPref(root) {
    root.classList.toggle("o_chatter_hidden", getStoredPref());
    root.classList.add(READY_CLASS);
}

function tagChatterRow(chatterEl) {
    const root = chatterEl.closest(FORM_RENDERER_SELECTOR);
    if (!root) {
        return;
    }
    const container = chatterEl.parentElement;
    if (container) {
        container.classList.add(CHATTER_ROW_CLASS);
    }
    applyStoredPref(root);
}

function scan(node) {
    if (!node || node.nodeType !== 1) {
        return;
    }
    if (node.matches && node.matches(FORM_RENDERER_SELECTOR)) {
        applyStoredPref(node);
    }
    if (node.querySelectorAll) {
        node.querySelectorAll(FORM_RENDERER_SELECTOR).forEach(applyStoredPref);
    }

    if (node.matches && node.matches(CHATTER_SELECTOR)) {
        tagChatterRow(node);
    }
    if (node.querySelectorAll) {
        node.querySelectorAll(CHATTER_SELECTOR).forEach(tagChatterRow);
    }
}

export const chatterToggleService = {
    start() {
        const btn = createGlobalButton();

        scan(document.body);
        dockButton(btn);

        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                mutation.addedNodes.forEach((node) => scan(node));
            }
            dockButton(btn);
        });
        observer.observe(document.documentElement, { childList: true, subtree: true });

        window.addEventListener("popstate", () => scan(document.body));

        return { observer };
    },
};

registry.category("services").add("my_hide_chatter_service", chatterToggleService);
