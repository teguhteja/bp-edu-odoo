/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, useRef } from "@odoo/owl";

/**
 * Parses a stored shortcut string (e.g. "ctrl+l") into a display label.
 * @param {string} shortcut
 * @returns {string}
 */
export function shortcutToLabel(shortcut) {
    if (!shortcut) return "";
    return shortcut
        .split("+")
        .map((part) => {
            const lower = part.toLowerCase().trim();
            if (lower === "ctrl") return "Ctrl";
            if (lower === "alt") return "Alt";
            if (lower === "shift") return "Shift";
            if (lower === "meta") return "Meta";
            return part.toUpperCase();
        })
        .join(" + ");
}

/**
 * Converts a KeyboardEvent into a normalised shortcut string like "ctrl+shift+l".
 * @param {KeyboardEvent} ev
 * @returns {string|null}  null if the event is a lone modifier key with no main key
 */
export function eventToShortcut(ev) {
    const parts = [];
    if (ev.ctrlKey) parts.push("ctrl");
    if (ev.altKey) parts.push("alt");
    if (ev.shiftKey) parts.push("shift");
    if (ev.metaKey) parts.push("meta");

    const key = ev.key.toLowerCase();
    // Ignore if the only key pressed is a modifier itself
    const MODIFIERS = ["control", "alt", "shift", "meta"];
    if (MODIFIERS.includes(key)) return null;

    parts.push(key);
    // Require at least one modifier for safety
    if (parts.length < 2) return null;
    return parts.join("+");
}

export class ShortcutInputField extends Component {
    static template = "fast_language_switcher.ShortcutInputField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.inputRef = useRef("input");
        this.state = useState({
            recording: false,
            displayValue: shortcutToLabel(
                this.props.record.data[this.props.name] || ""
            ),
        });
    }

    get currentShortcut() {
        return this.props.record.data[this.props.name] || "";
    }

    get isReadonly() {
        return this.props.readonly;
    }

    startRecording() {
        if (this.isReadonly) return;
        this.state.recording = true;
        this.state.displayValue = "Press a key combination...";
        // Focus the hidden input so we catch keydown
        this.inputRef.el && this.inputRef.el.focus();
    }

    onKeyDown(ev) {
        if (!this.state.recording) return;
        ev.preventDefault();
        ev.stopPropagation();

        if (ev.key === "Escape") {
            this.cancelRecording();
            return;
        }

        const shortcut = eventToShortcut(ev);
        if (!shortcut) return; // lone modifier, wait

        this.state.recording = false;
        this.state.displayValue = shortcutToLabel(shortcut);
        this.props.record.update({ [this.props.name]: shortcut });
    }

    onBlur() {
        if (this.state.recording) {
            this.cancelRecording();
        }
    }

    cancelRecording() {
        this.state.recording = false;
        this.state.displayValue = shortcutToLabel(this.currentShortcut);
    }

    resetToDefault() {
        const defaultVal = "ctrl+l";
        this.state.displayValue = shortcutToLabel(defaultVal);
        this.props.record.update({ [this.props.name]: defaultVal });
    }
}

export const shortcutInputField = {
    component: ShortcutInputField,
    displayName: "Shortcut Input",
    supportedTypes: ["char"],
    extractProps: ({ attrs }) => ({}),
};

registry.category("fields").add("shortcut_input", shortcutInputField);
