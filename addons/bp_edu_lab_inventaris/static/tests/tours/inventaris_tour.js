import { registry } from "@web/core/registry";

// Laboran: membuat perbaikan untuk barang rusak lalu memprosesnya.
registry.category("web_tour.tours").add("bp_edu_lab_inventaris_tour", {
    steps: () => [
        {
            content: "Buat perbaikan baru",
            trigger: ".o_list_button_add",
            run: "click",
        },
        {
            content: "Pilih barang",
            trigger: ".o_field_widget[name='product_id'] input",
            run: "edit Laptop Tes",
        },
        {
            trigger: ".o-autocomplete--dropdown-item:contains('Laptop Tes')",
            run: "click",
        },
        {
            content: "Jumlah rusak",
            trigger: ".o_field_widget[name='qty'] input",
            run: "edit 2",
        },
        {
            content: "Proses perbaikan",
            trigger: ".o_form_statusbar button[name='action_proses']",
            run: "click",
        },
        {
            content: "Status menjadi Proses",
            trigger: ".o_statusbar_status button.o_arrow_button_current:contains('Proses')",
        },
    ],
});
