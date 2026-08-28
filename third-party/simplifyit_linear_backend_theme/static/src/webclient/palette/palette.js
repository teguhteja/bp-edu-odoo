// Copyright 2026. Developed and maintained by Simplify It S.R.L. (https://simplifyit.com.bo)

import { browser } from "@web/core/browser/browser";
import { cookie } from "@web/core/browser/cookie";

/**
 * Curated accent palettes. Only the accent-family tokens vary per palette —
 * surfaces, borders and text keep the values from tokens.scss/tokens.dark.scss
 * regardless of the chosen palette. Keys must match res_company.py's
 * `slt_palette` selection.
 *
 * `indigo` mirrors the default values already baked into tokens.scss /
 * tokens.dark.scss, so picking it is a no-op override.
 */
export const PALETTES = {
    indigo: {
        light: {
            accent: "#5E6AD2", accentRgb: "94, 106, 210", accentStrong: "#4F5ABF", accentText: "#4C59BD",
            accentSoft: "rgba(94, 106, 210, 0.11)", accentSoft2: "rgba(94, 106, 210, 0.18)",
            ring: "rgba(94, 106, 210, 0.25)",
        },
        dark: {
            accent: "#5E6AD2", accentRgb: "94, 106, 210", accentStrong: "#6E79DB", accentText: "#858DF0",
            accentSoft: "rgba(94, 106, 210, 0.18)", accentSoft2: "rgba(94, 106, 210, 0.28)",
            ring: "rgba(110, 121, 219, 0.35)",
        },
    },
    blue: {
        light: {
            accent: "#2E6ADE", accentRgb: "46, 106, 222", accentStrong: "#2557C0", accentText: "#2A5FC7",
            accentSoft: "rgba(46, 106, 222, 0.11)", accentSoft2: "rgba(46, 106, 222, 0.18)",
            ring: "rgba(46, 106, 222, 0.25)",
        },
        dark: {
            accent: "#5B8DEF", accentRgb: "91, 141, 239", accentStrong: "#71A0F5", accentText: "#8CB2F7",
            accentSoft: "rgba(91, 141, 239, 0.18)", accentSoft2: "rgba(91, 141, 239, 0.28)",
            ring: "rgba(91, 141, 239, 0.35)",
        },
    },
    teal: {
        light: {
            accent: "#0E9488", accentRgb: "14, 148, 136", accentStrong: "#0B7A70", accentText: "#0C8579",
            accentSoft: "rgba(14, 148, 136, 0.11)", accentSoft2: "rgba(14, 148, 136, 0.18)",
            ring: "rgba(14, 148, 136, 0.25)",
        },
        dark: {
            accent: "#2DD4C4", accentRgb: "45, 212, 196", accentStrong: "#45DED0", accentText: "#6EE6DA",
            accentSoft: "rgba(45, 212, 196, 0.18)", accentSoft2: "rgba(45, 212, 196, 0.28)",
            ring: "rgba(45, 212, 196, 0.35)",
        },
    },
    green: {
        light: {
            accent: "#2F9E58", accentRgb: "47, 158, 88", accentStrong: "#24803F", accentText: "#278A46",
            accentSoft: "rgba(47, 158, 88, 0.11)", accentSoft2: "rgba(47, 158, 88, 0.18)",
            ring: "rgba(47, 158, 88, 0.25)",
        },
        dark: {
            accent: "#3FBE72", accentRgb: "63, 190, 114", accentStrong: "#52CB82", accentText: "#74D89B",
            accentSoft: "rgba(63, 190, 114, 0.18)", accentSoft2: "rgba(63, 190, 114, 0.28)",
            ring: "rgba(63, 190, 114, 0.35)",
        },
    },
    purple: {
        light: {
            accent: "#7C3AED", accentRgb: "124, 58, 237", accentStrong: "#6425D0", accentText: "#6E30DD",
            accentSoft: "rgba(124, 58, 237, 0.11)", accentSoft2: "rgba(124, 58, 237, 0.18)",
            ring: "rgba(124, 58, 237, 0.25)",
        },
        dark: {
            accent: "#9C6BFF", accentRgb: "156, 107, 255", accentStrong: "#AC82FF", accentText: "#BC9AFF",
            accentSoft: "rgba(156, 107, 255, 0.18)", accentSoft2: "rgba(156, 107, 255, 0.28)",
            ring: "rgba(156, 107, 255, 0.35)",
        },
    },
    pink: {
        light: {
            accent: "#DB2C6F", accentRgb: "219, 44, 111", accentStrong: "#B81F5C", accentText: "#C22567",
            accentSoft: "rgba(219, 44, 111, 0.11)", accentSoft2: "rgba(219, 44, 111, 0.18)",
            ring: "rgba(219, 44, 111, 0.25)",
        },
        dark: {
            accent: "#FF5C9A", accentRgb: "255, 92, 154", accentStrong: "#FF74AA", accentText: "#FF8FBB",
            accentSoft: "rgba(255, 92, 154, 0.18)", accentSoft2: "rgba(255, 92, 154, 0.28)",
            ring: "rgba(255, 92, 154, 0.35)",
        },
    },
    orange: {
        light: {
            accent: "#D96B1A", accentRgb: "217, 107, 26", accentStrong: "#B85A12", accentText: "#C4620F",
            accentSoft: "rgba(217, 107, 26, 0.11)", accentSoft2: "rgba(217, 107, 26, 0.18)",
            ring: "rgba(217, 107, 26, 0.25)",
        },
        dark: {
            accent: "#FF9A44", accentRgb: "255, 154, 68", accentStrong: "#FFAC63", accentText: "#FFBE85",
            accentSoft: "rgba(255, 154, 68, 0.18)", accentSoft2: "rgba(255, 154, 68, 0.28)",
            ring: "rgba(255, 154, 68, 0.35)",
        },
    },
    red: {
        light: {
            accent: "#DC3B3B", accentRgb: "220, 59, 59", accentStrong: "#BC2E2E", accentText: "#C63333",
            accentSoft: "rgba(220, 59, 59, 0.11)", accentSoft2: "rgba(220, 59, 59, 0.18)",
            ring: "rgba(220, 59, 59, 0.25)",
        },
        dark: {
            accent: "#FF6B6B", accentRgb: "255, 107, 107", accentStrong: "#FF8484", accentText: "#FF9D9D",
            accentSoft: "rgba(255, 107, 107, 0.18)", accentSoft2: "rgba(255, 107, 107, 0.28)",
            ring: "rgba(255, 107, 107, 0.35)",
        },
    },
};

const CSS_VARS = {
    accent: "--slt-accent",
    accentRgb: "--slt-accent-rgb",
    accentStrong: "--slt-accent-strong",
    accentText: "--slt-accent-text",
    accentSoft: "--slt-accent-soft",
    accentSoft2: "--slt-accent-soft-2",
};

/** Mirrors the cookie/media-query fallback used by the dark mode toggle. */
export function getColorScheme() {
    return (
        cookie.get("color_scheme") ||
        (browser.matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light")
    );
}

/**
 * Override the accent CSS custom properties on the document root for the
 * given palette + color scheme. Applied as inline styles, so they take
 * precedence over the `:root` declarations from tokens(.dark).scss without
 * needing a per-palette asset bundle.
 */
export function applyPalette(paletteId, colorScheme = getColorScheme()) {
    const palette = PALETTES[paletteId] || PALETTES.indigo;
    const values = palette[colorScheme] || palette.light;
    const root = document.documentElement.style;
    for (const [key, cssVar] of Object.entries(CSS_VARS)) {
        root.setProperty(cssVar, values[key]);
    }
    root.setProperty("--slt-ring", `0 0 0 3px ${values.ring}`);
}
