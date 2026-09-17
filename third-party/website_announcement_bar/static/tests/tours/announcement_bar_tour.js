import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("announcement_bar_dismiss", {
    url: "/",
    steps: () => [
        {
            content: "bar revealed by the widget",
            trigger: ".o_announcement_bar.o_announcement_bar_visible",
        },
        {
            content: "close it",
            trigger: ".o_announcement_bar_close",
            run: "click",
        },
        {
            content: "bar hidden and dismissal stored for the tab session",
            trigger: "body:not(:has(.o_announcement_bar_visible))",
            run: () => {
                if (sessionStorage.getItem("website_announcement_bar_closed") !== "1") {
                    throw new Error("dismissal was not stored in sessionStorage");
                }
            },
        },
    ],
});
