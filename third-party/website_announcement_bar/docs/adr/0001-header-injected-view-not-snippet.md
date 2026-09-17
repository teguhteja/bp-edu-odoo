# Announcement Bar is a header-injected editable view, not a draggable snippet

Snippets live in page content, so a dragged snippet exists only on the page it was dropped on — wrong for a site-wide bar. Instead we inherit `website.layout` to render the bar above the header and store its content as an editable view. This makes multi-language (view translation), multi-website (copy-on-write), and any-theme compatibility native for free, at the cost of no per-page placement (page targeting deferred to v2).
