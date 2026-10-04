import { registry } from "@web/core/registry";

// Mahasiswa: presensi dengan token, lalu mengerjakan pretest (survey) sampai selesai.
registry.category("web_tour.tours").add("bp_edu_lab_portal_tour", {
    url: "/my/praktikum",
    steps: () => [
        {
            content: "Isi token presensi",
            trigger: ".o_lab_form_presensi input[name='token']",
            run: "edit abc123",
        },
        {
            content: "Kirim presensi",
            trigger: ".o_lab_form_presensi button[type='submit']",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Presensi berhasil",
            trigger: ".o_lab_pesan:contains('Berhasil Presensi')",
        },
        {
            trigger: ".o_lab_hadir",
        },
        {
            content: "Buka pretest",
            trigger: "a.o_lab_ujian_pra",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Mulai survey",
            trigger: "button.btn-primary:contains('Start Survey')",
            run: "click",
        },
        {
            content: "Jawab soal",
            trigger: "div.js_question-wrapper:contains('Apa itu HTML?') textarea",
            run: "edit Bahasa markup untuk web",
        },
        {
            content: "Kirim jawaban",
            // tombol baru aktif setelah interaksi survey selesai memuat halaman
            trigger: "button[value='finish']:not(.disabled)",
            run: "click",
        },
        {
            content: "Konfirmasi kirim di dialog",
            trigger: ".modal button.btn-primary:contains('Submit')",
            run: "click",
        },
        {
            content: "Survey selesai",
            trigger: ".o_survey_finished",
        },
    ],
});

// Laboran: generate token pada praktikum lalu mengisi nilai di grid Penilaian.
registry.category("web_tour.tours").add("bp_edu_lab_admin_tour", {
    steps: () => [
        {
            content: "Buka praktikum",
            trigger: ".o_data_row td.o_data_cell:contains('Pertemuan Tes')",
            run: "click",
        },
        {
            content: "Generate token",
            trigger: ".o_form_view button[name='action_generate_token']",
            run: "click",
        },
        {
            content: "Token terisi",
            trigger: ".o_form_view .o_field_widget[name='token'] span:not(:empty)",
        },
        {
            content: "Buka penilaian",
            trigger: ".o_form_view .o_form_statusbar button[name='action_buka_penilaian']",
            run: "click",
        },
        {
            content: "Pilih sel nilai",
            trigger: ".o_list_view .o_data_row td[name='nilai']",
            run: "click",
        },
        {
            content: "Isi nilai",
            trigger: ".o_list_view .o_data_row .o_field_widget[name='nilai'] input",
            run: "edit 87",
        },
        {
            content: "Simpan",
            trigger: ".o_list_button_save",
            run: "click",
        },
        {
            content: "Nilai tersimpan",
            trigger: ".o_list_view .o_data_row td[name='nilai']:contains('87')",
        },
    ],
});
