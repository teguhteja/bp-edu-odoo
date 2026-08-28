import base64

from odoo.addons.sbs_custom_style import _setup_module
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSbsLoginBackground(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parameters = cls.env["ir.config_parameter"].sudo()
        cls.settings_model = cls.env["res.config.settings"]

    def test_color_background_style(self):
        self.parameters.set_param(
            "sbs_custom_style.login_background_type", "color"
        )
        self.parameters.set_param(
            "sbs_custom_style.login_background_color", "#0A2540"
        )
        style = self.env["ir.http"]._sbs_get_login_background_style()
        self.assertIn("background-color: #0A2540", style)
        self.assertNotIn("background-image", style)

    def test_image_background_style(self):
        self.parameters.set_param(
            "sbs_custom_style.login_background_type", "image"
        )
        self.parameters.set_param(
            "sbs_custom_style.login_background_image",
            base64.b64encode(b"image-data"),
        )
        style = self.env["ir.http"]._sbs_get_login_background_style()
        self.assertIn("/sbs_custom_style/login/background", style)

    def test_setup_module_uses_app_background_for_login(self):
        _setup_module(self.env)
        company = self.env.ref("base.main_company")

        self.assertEqual(
            self.parameters.get_param(
                "sbs_custom_style.login_background_type"
            ),
            "image",
        )
        self.assertEqual(
            self.parameters.get_param(
                "sbs_custom_style.login_background_image"
            ),
            company.sbs_background_image.decode("ascii"),
        )

    def test_invalid_color_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.settings_model.create(
                {"sbs_login_background_color": "not-a-colour"}
            )

    def test_non_image_upload_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.settings_model.create(
                {
                    "sbs_login_background_image": base64.b64encode(
                        b"plain text"
                    )
                }
            )
