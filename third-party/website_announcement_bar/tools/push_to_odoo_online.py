"""
Install the Announcement Bar on an Odoo Online (SaaS) website, where custom
modules cannot be installed. Pushes the module's two QWeb views as ir.ui.view
records and injects compiled CSS / vanilla JS into the website's custom code.

Keep the ARCH/CSS/JS constants in sync with the module source:
  views/templates.xml, views/snippets/options.xml,
  static/src/scss/announcement_bar.scss, static/src/js/announcement_bar.js

The font picker option is intentionally omitted on SaaS: it requires an SCSS
alias-map merge in web._assets_primary_variables, which custom code cannot
reach on Odoo Online. Inline text styling via the editor toolbar still works.

Usage:
    python3 tools/push_to_odoo_online.py --url https://x.dev.odoo.com --db DB \
        --user USER --password PASS [--dry-run]

Idempotent: views are matched by key and updated in place; custom-code blocks
are marker-fenced and replaced.
"""

import argparse
import re
import sys
import xmlrpc.client

BAR_KEY = "website_announcement_bar.announcement_bar"
OPTIONS_KEY = "website_announcement_bar.snippet_options"
MARKER = "announcement-bar"

BAR_ARCH = """<data inherit_id="website.layout" name="Announcement Bar">
    <xpath expr="//header" position="before">
        <div class="o_announcement_bar o_announcement_bar_dismissable text-center o_cc o_cc3"
             data-name="Announcement Bar">
            <div id="announcementBarCarousel" class="carousel slide"
                 data-bs-ride="carousel" data-bs-interval="7000">
                <div class="carousel-indicators d-none">
                    <button type="button" data-bs-target="#announcementBarCarousel"
                            data-bs-slide-to="0" class="active" aria-label="Message 1"/>
                </div>
                <div class="carousel-inner">
                    <div class="carousel-item active">
                        <p class="mb-0 py-2 px-5">Write your announcement here — <a href="#">add a link if you like</a>.</p>
                    </div>
                </div>
            </div>
            <button type="button" class="o_announcement_bar_close btn-close"
                    title="Close" aria-label="Close"/>
        </div>
    </xpath>
</data>"""

OPTIONS_ARCH = """<data inherit_id="website.snippet_options" name="Announcement Bar Options">
    <xpath expr="." position="inside">
        <div data-selector="#wrapwrap > header" data-no-check="true"
             groups="website.group_website_designer">
            <we-checkbox string="Announcement Bar"
                         data-customize-website-views="website_announcement_bar.announcement_bar"
                         data-no-preview="true"
                         data-reload="/"/>
        </div>
        <div data-selector=".o_announcement_bar" data-no-check="true"
             groups="website.group_website_designer">
            <we-colorpicker string="Background Color"
                            data-select-style="true"
                            data-css-property="background-color"
                            data-color-prefix="bg-"/>
            <we-checkbox string="Visitors Can Close"
                         data-select-class="o_announcement_bar_dismissable"/>
            <we-datetimepicker string="Show From"
                               data-select-data-attribute="0"
                               data-attribute-name="startTime"/>
            <we-datetimepicker string="Show Until"
                               data-select-data-attribute="0"
                               data-attribute-name="endTime"/>
        </div>
        <div data-js="Carousel" data-selector=".o_announcement_bar"
             data-target="&gt; .carousel"
             groups="website.group_website_designer">
            <we-row string="Message">
                <we-button data-add-slide="true" data-no-preview="true"
                           class="o_we_bg_brand_primary">Add Message</we-button>
            </we-row>
            <we-select string="Transition">
                <we-button data-select-class="slide">Slide</we-button>
                <we-button data-select-class="carousel-fade slide">Fade</we-button>
            </we-select>
            <we-input string="Delay"
                      data-select-data-attribute="0s" data-attribute-name="bsInterval"
                      data-unit="s" data-save-unit="ms" data-step="0.1"/>
        </div>
    </xpath>
</data>"""

CSS = """body:not(.editor_enable) .o_announcement_bar:not(.o_announcement_bar_visible) { display: none; }
.o_announcement_bar { position: relative; }
.o_announcement_bar.o_announcement_bar_fixed { position: fixed; top: 0; left: 0; right: 0; z-index: 1030; }
.o_announcement_bar .carousel-indicators { display: none; }
.o_announcement_bar .o_announcement_bar_close { display: none; position: absolute; top: 50%; right: 0.75rem; transform: translateY(-50%); z-index: 2; }
.o_announcement_bar.o_announcement_bar_dismissable .o_announcement_bar_close { display: block; }
.o_announcement_bar a { color: inherit; text-decoration: underline; }"""

JS = """(function () {
    "use strict";
    // Builder/preview iframe: never touch runtime classes there, or the
    // editor could serialize them into the saved view arch.
    if (window.frameElement) { return; }
    var KEY = "website_announcement_bar_closed";
    function init() {
        var bar = document.querySelector(".o_announcement_bar");
        if (!bar) { return; }
        var now = Date.now() / 1000;
        var start = parseFloat(bar.dataset.startTime);
        var end = parseFloat(bar.dataset.endTime);
        var inWindow = (isNaN(start) || now >= start) && (isNaN(end) || now <= end);
        var show = inWindow && !window.sessionStorage.getItem(KEY);
        bar.classList.toggle("o_announcement_bar_visible", show);
        var offsetNav = null;
        function findFixedNav() {
            var header = document.querySelector("#wrapwrap > header");
            if (!header) { return null; }
            var els = [header].concat([].slice.call(header.children));
            for (var i = 0; i < els.length; i++) {
                if (getComputedStyle(els[i]).position === "fixed") { return els[i]; }
            }
            return null;
        }
        function applyOffset() {
            var nav = findFixedNav();
            if (!nav) { return; }
            bar.classList.remove("o_announcement_bar_fixed");
            var h = bar.offsetHeight;
            bar.classList.add("o_announcement_bar_fixed");
            nav.style.setProperty("top", h + "px", "important");
            document.getElementById("wrapwrap").style.paddingTop = h + "px";
            offsetNav = nav;
        }
        function removeOffset() {
            if (!offsetNav) { return; }
            offsetNav.style.removeProperty("top");
            document.getElementById("wrapwrap").style.paddingTop = "";
            bar.classList.remove("o_announcement_bar_fixed");
            offsetNav = null;
        }
        if (show) {
            applyOffset();
            window.addEventListener("resize", applyOffset, { passive: true });
        }
        var close = bar.querySelector(".o_announcement_bar_close");
        if (close) {
            close.addEventListener("click", function () {
                window.sessionStorage.setItem(KEY, "1");
                bar.classList.remove("o_announcement_bar_visible");
                removeOffset();
            });
        }
    }
    if (document.readyState !== "loading") { init(); }
    else { document.addEventListener("DOMContentLoaded", init); }
})();"""


class Client:
    def __init__(self, url, db, user, password):
        self.url, self.db, self.password = url.rstrip("/"), db, password
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = common.authenticate(db, user, password, {})
        if not self.uid:
            sys.exit("ERROR: authentication failed")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def kw(self, model, method, args, kwargs=None):
        return self.models.execute_kw(self.db, self.uid, self.password,
                                      model, method, args, kwargs or {})


def upsert_view(c, key, name, inherit_module, inherit_name, arch, active, dry):
    inherit_id = c.kw("ir.model.data", "check_object_reference",
                      [inherit_module, inherit_name])[1]
    existing = c.kw("ir.ui.view", "search_read",
                    [[["key", "=", key]], ["id", "active"]],
                    {"context": {"active_test": False}})
    vals = {"name": name, "type": "qweb", "key": key, "mode": "extension",
            "inherit_id": inherit_id, "arch_base": arch}
    if dry:
        print(f"DRY RUN: would {'update ' + str([v['id'] for v in existing]) if existing else 'create'} view {key}")
        return
    if existing:
        c.kw("ir.ui.view", "write", [[v["id"] for v in existing], vals])
        print(f"updated view {key} (ids {[v['id'] for v in existing]})")
    else:
        vals["active"] = active
        vid = c.kw("ir.ui.view", "create", [vals])
        print(f"created view {key} (id {vid}, active={active})")


def upsert_block(c, site_id, field, current, tag, body, dry):
    start = f"<!-- == {MARKER} start == -->"
    end = f"<!-- == {MARKER} end == -->"
    stripped = re.sub(re.escape(start) + r".*?" + re.escape(end), "",
                      current or "", flags=re.DOTALL).strip()
    block = f"{start}\n<{tag}>\n{body}\n</{tag}>\n{end}"
    new = (stripped + "\n" + block).strip() if stripped else block
    if dry:
        print(f"DRY RUN: would write {len(new)} chars to website.{field}")
        return
    c.kw("website", "write", [[site_id], {field: new}])
    print(f"wrote {field} ({len(new)} chars)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--db", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--website-id", type=int, default=1,
                   help="website record id to receive the custom-code blocks")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    print(f"target: {a.url} db={a.db}")
    c = Client(a.url, a.db, a.user, a.password)

    upsert_view(c, BAR_KEY, "Announcement Bar", "website", "layout",
                BAR_ARCH, False, a.dry_run)
    upsert_view(c, OPTIONS_KEY, "Announcement Bar Options", "website",
                "snippet_options", OPTIONS_ARCH, True, a.dry_run)

    wid = a.website_id
    site = c.kw("website", "read", [[wid], ["name", "custom_code_head", "custom_code_footer"]])[0]
    print(f"custom code target website: {wid} ({site['name']})")
    upsert_block(c, wid, "custom_code_head", site.get("custom_code_head"),
                 "style", CSS, a.dry_run)
    upsert_block(c, wid, "custom_code_footer", site.get("custom_code_footer"),
                 "script", JS, a.dry_run)
    print("done")


if __name__ == "__main__":
    main()
