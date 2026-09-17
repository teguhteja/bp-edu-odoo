import publicWidget from "@web/legacy/js/public/public_widget";

const STORAGE_KEY = "website_announcement_bar_closed";

publicWidget.registry.AnnouncementBar = publicWidget.Widget.extend({
    selector: ".o_announcement_bar",
    disabledInEditableMode: true,
    events: {
        "click .o_announcement_bar_close": "_onClose",
    },

    start() {
        this._normalizeCarousel();
        // toggle (not add): the reveal class may already be in the DOM —
        // even in the saved arch, if a previous editor session serialized
        // it — and a dismissed/out-of-schedule bar must actively lose it.
        const show = this._isWithinSchedule() && !window.sessionStorage.getItem(STORAGE_KEY);
        this.el.classList.toggle("o_announcement_bar_visible", show);
        if (show) {
            this._applyFixedHeaderOffset();
            this._onResize = () => this._applyFixedHeaderOffset();
            window.addEventListener("resize", this._onResize, { passive: true });
        }
        return this._super(...arguments);
    },

    destroy() {
        // Entering edit mode destroys public widgets, then the editor
        // serializes the DOM on save — a leftover runtime class would be
        // baked into the view arch.
        this.el.classList.remove("o_announcement_bar_visible");
        this._removeFixedHeaderOffset();
        if (this._onResize) {
            window.removeEventListener("resize", this._onResize);
        }
        this._super(...arguments);
    },

    // Editing (duplicating a message instead of using Add Message, undo,
    // partial saves) can leave the indicators out of sync with the
    // messages, which crashes Bootstrap's auto-cycle
    // (_setActiveIndicatorElement reads .active.classList). Rebuild them
    // to match reality before the carousel initializes. Frontend only —
    // the widget never runs in edit mode, so nothing gets serialized.
    _normalizeCarousel() {
        const carousel = this.el.querySelector(".carousel");
        if (!carousel) {
            return;
        }
        const items = carousel.querySelectorAll(".carousel-inner > .carousel-item");
        if (!items.length) {
            return;
        }
        let active = [...items].findIndex((i) => i.classList.contains("active"));
        if (active < 0) {
            active = 0;
            items[0].classList.add("active");
        }
        const indicators = carousel.querySelector(".carousel-indicators");
        if (!indicators) {
            return;
        }
        indicators.replaceChildren(...[...items].map((item, i) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.dataset.bsTarget = "#" + carousel.id;
            btn.dataset.bsSlideTo = String(i);
            btn.setAttribute("aria-label", "Message " + (i + 1));
            if (i === active) {
                btn.classList.add("active");
            }
            return btn;
        }));
    },

    // Themes with a fixed header paint the nav at the viewport top, which
    // would cover an in-flow bar. In that case the bar goes fixed too,
    // stacked above the nav, and the wrapper gets compensation padding.
    // No-op on themes whose header scrolls normally.
    _findFixedNav() {
        const header = document.querySelector("#wrapwrap > header");
        if (!header) {
            return null;
        }
        for (const el of [header, ...header.children]) {
            if (getComputedStyle(el).position === "fixed") {
                return el;
            }
        }
        return null;
    },

    _applyFixedHeaderOffset() {
        const nav = this._findFixedNav();
        if (!nav) {
            return;
        }
        // measure in flow before going fixed
        this.el.classList.remove("o_announcement_bar_fixed");
        const barHeight = this.el.offsetHeight;
        this.el.classList.add("o_announcement_bar_fixed");
        // inline-important: themes may pin the fixed nav with top:0 !important
        nav.style.setProperty("top", barHeight + "px", "important");
        this.el.closest("#wrapwrap").style.paddingTop = barHeight + "px";
        this._offsetNav = nav;
    },

    _removeFixedHeaderOffset() {
        if (!this._offsetNav) {
            return;
        }
        this._offsetNav.style.removeProperty("top");
        this.el.closest("#wrapwrap").style.paddingTop = "";
        this.el.classList.remove("o_announcement_bar_fixed");
        this._offsetNav = null;
    },

    // Schedule attrs are epoch seconds (same convention as s_countdown's
    // endTime); either bound may be absent.
    _isWithinSchedule() {
        const nowSec = Date.now() / 1000;
        const start = parseFloat(this.el.dataset.startTime);
        const end = parseFloat(this.el.dataset.endTime);
        if (!isNaN(start) && nowSec < start) {
            return false;
        }
        if (!isNaN(end) && nowSec > end) {
            return false;
        }
        return true;
    },

    _onClose() {
        window.sessionStorage.setItem(STORAGE_KEY, "1");
        this.el.classList.remove("o_announcement_bar_visible");
        this._removeFixedHeaderOffset();
    },
});
