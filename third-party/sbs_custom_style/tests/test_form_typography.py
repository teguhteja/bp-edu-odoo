from odoo.tests.common import TransactionCase, tagged
from odoo.tools import misc


@tagged("post_install", "-at_install")
class TestFormTypography(TransactionCase):

    stylesheet = (
        "sbs_custom_style/static/src/theme/views/form/form.scss"
    )

    def test_typography_is_screen_only(self):
        with misc.file_open(self.stylesheet, mode="r") as stylesheet:
            content = stylesheet.read()

        self.assertIn("@media screen", content)
        self.assertIn("--body-font-weight: 600", content)
        self.assertIn("--btn-font-weight: 600", content)
        self.assertIn(".o_web_client .o_form_view", content)
        self.assertIn(
            ".o_group .o_wrap_label .o_form_label",
            content,
        )
        self.assertIn(
            ".o-autocomplete--dropdown-menu .dropdown-item",
            content,
        )
        self.assertIn(".o-dropdown--menu .dropdown-item", content)
        self.assertIn(".o_web_client .o_dropdown_title", content)
        self.assertIn(
            ".o_list_renderer .o_list_table",
            content,
        )

    def test_typography_is_not_in_report_assets(self):
        asset_model = self.env["ir.asset"]
        asset_params = asset_model._get_asset_params()

        backend_paths = {
            path.lstrip("/")
            for path, _full_path, _bundle, _modified in
            asset_model._get_asset_paths("web.assets_backend", asset_params)
        }
        self.assertIn(self.stylesheet, backend_paths)

        for report_bundle in (
            "web.report_assets_common",
            "web.report_assets_pdf",
        ):
            report_paths = {
                path.lstrip("/")
                for path, _full_path, _bundle, _modified in
                asset_model._get_asset_paths(report_bundle, asset_params)
            }
            self.assertNotIn(self.stylesheet, report_paths)

    def test_backend_styles_compile(self):
        bundle = self.env["ir.qweb"]._get_asset_bundle(
            "web.assets_backend",
            css=True,
            js=False,
        )
        self.assertTrue(bundle.css())
