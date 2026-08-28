/** @odoo-module **/

import { Component, onMounted, onWillUnmount, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { browser } from "@web/core/browser/browser";
import { shortcutToLabel } from "../shortcut_input_field/shortcut_input_field";

const APPLY_DELAY = 1500; // ms to wait before applying after last shortcut key press
const CONFIG_KEY = "fast_language_switcher.shortcut";
const DEFAULT_SHORTCUT = "ctrl+l";

/**
 * Parses a stored shortcut string (e.g. "ctrl+shift+l") into a normalised object
 * for matching against a KeyboardEvent.
 * @param {string} shortcut
 * @returns {{ ctrl: boolean, alt: boolean, shift: boolean, meta: boolean, key: string }}
 */
function parseShortcut(shortcut) {
    const parts = (shortcut || DEFAULT_SHORTCUT).toLowerCase().split("+");
    const key = parts[parts.length - 1];
    return {
        ctrl: parts.includes("ctrl"),
        alt: parts.includes("alt"),
        shift: parts.includes("shift"),
        meta: parts.includes("meta"),
        key,
    };
}

/**
 * Returns true when a KeyboardEvent matches the parsed shortcut.
 */
function matchesShortcut(ev, parsed) {
    return (
        ev.ctrlKey === parsed.ctrl &&
        ev.altKey === parsed.alt &&
        ev.shiftKey === parsed.shift &&
        ev.metaKey === parsed.meta &&
        ev.key.toLowerCase() === parsed.key
    );
}

/**
 * macOS-style language switcher overlay.
 * Triggered by the user-configured keyboard shortcut (default Ctrl+L).
 * Each press cycles to the next language; after APPLY_DELAY ms without a
 * key press the selection is applied automatically.
 */
export class LanguageSwitcherDialog extends Component {
    setup() {
        this.orm = useService("orm");
        this.user = useService("user");

        this.state = useState({
            visible: false,
            languages: [],
            selectedIndex: 0,
            applying: false,
            shortcutLabel: shortcutToLabel(DEFAULT_SHORTCUT),
        });

        this._applyTimer = null;
        this._parsedShortcut = parseShortcut(DEFAULT_SHORTCUT);
        this._boundKeyDown = this._onKeyDown.bind(this);

        onWillStart(async () => {
            const [langs, savedShortcut] = await Promise.all([
                this.orm.searchRead(
                    "res.lang",
                    [["active", "=", true]],
                    ["code", "name", "flag_image_url"],
                    { order: "name asc" }
                ),
                this.orm.call(
                    "ir.config_parameter",
                    "get_param",
                    [CONFIG_KEY, DEFAULT_SHORTCUT]
                ),
            ]);

            this.state.languages = langs;

            const shortcut = savedShortcut || DEFAULT_SHORTCUT;
            this._parsedShortcut = parseShortcut(shortcut);
            this.state.shortcutLabel = shortcutToLabel(shortcut);
        });

        onMounted(() => {
            // capture: true — intercept before browser acts on Ctrl+L (address bar focus)
            document.addEventListener("keydown", this._boundKeyDown, true);
        });

        onWillUnmount(() => {
            document.removeEventListener("keydown", this._boundKeyDown, true);
            this._clearTimer();
        });
    }

    _onKeyDown(ev) {
        if (matchesShortcut(ev, this._parsedShortcut)) {
            ev.preventDefault();
            ev.stopPropagation();
            this._onShortcutPressed();
            return;
        }
        if (ev.key === "Escape" && this.state.visible) {
            ev.preventDefault();
            this._close();
        }
    }

    _onShortcutPressed() {
        if (!this.state.languages.length) return;

        if (!this.state.visible) {
            const currentCode = this.user.lang;
            const currentIdx = this.state.languages.findIndex((l) => l.code === currentCode);
            const nextIdx = (currentIdx + 1) % this.state.languages.length;

            this.state.selectedIndex = nextIdx;
            this.state.visible = true;
            this.state.applying = false;
        } else {
            this.state.selectedIndex =
                (this.state.selectedIndex + 1) % this.state.languages.length;
        }

        this._resetApplyTimer();
    }

    _resetApplyTimer() {
        this._clearTimer();
        this._applyTimer = setTimeout(() => {
            this._applySelectedLanguage();
        }, APPLY_DELAY);
    }

    _clearTimer() {
        if (this._applyTimer) {
            clearTimeout(this._applyTimer);
            this._applyTimer = null;
        }
    }

    async _applySelectedLanguage() {
        const lang = this.state.languages[this.state.selectedIndex];
        if (!lang || lang.code === this.user.lang) {
            this._close();
            return;
        }
        this.state.applying = true;
        await this.orm.write("res.users", [this.user.userId], { lang: lang.code });
        browser.location.reload();
    }

    async selectLanguage(index) {
        this._clearTimer();
        this.state.selectedIndex = index;
        await this._applySelectedLanguage();
    }

    _close() {
        this._clearTimer();
        this.state.visible = false;
        this.state.applying = false;
    }
}

LanguageSwitcherDialog.template = "fast_language_switcher.LanguageSwitcherDialog";
LanguageSwitcherDialog.props = {};

registry.category("systray").add(
    "fast_language_switcher.language_switcher_dialog",
    { Component: LanguageSwitcherDialog },
    { sequence: 2 }
);
