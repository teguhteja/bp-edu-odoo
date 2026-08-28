import base64
import binascii
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.mimetypes import guess_mimetype


class SbsResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    SBS_COLOR_FIELDS = (
        "color_brand",
        "color_primary",
        "color_success",
        "color_info",
        "color_warning",
        "color_danger",
    )
    SBS_THEME_COLOR_FIELDS = (
        "color_appsmenu_text",
        "color_appbar_text",
        "color_appbar_active",
        "color_appbar_background",
    )
    SBS_COLOR_ASSET_LIGHT_URL = (
        "/sbs_custom_style/static/src/colors/scss/colors_light.scss"
    )
    SBS_COLOR_ASSET_DARK_URL = (
        "/sbs_custom_style/static/src/colors/scss/colors_dark.scss"
    )
    SBS_COLOR_ASSET_THEME_URL = (
        "/sbs_custom_style/static/src/theme/scss/colors.scss"
    )
    SBS_COLOR_BUNDLE_LIGHT = "web._assets_primary_variables"
    SBS_COLOR_BUNDLE_DARK = "web.assets_web_dark"
    SBS_COLOR_BUNDLE_THEME = "web._assets_primary_variables"

    sbs_appbar_image = fields.Binary(
        related="company_id.sbs_appbar_image",
        readonly=False,
    )
    sbs_theme_favicon = fields.Binary(
        related="company_id.sbs_favicon",
        readonly=False,
    )
    sbs_theme_background_image = fields.Binary(
        related="company_id.sbs_background_image",
        readonly=False,
    )

    sbs_color_brand_light = fields.Char(string="Brand Light Color")
    sbs_color_primary_light = fields.Char(string="Primary Light Color")
    sbs_color_success_light = fields.Char(string="Success Light Color")
    sbs_color_info_light = fields.Char(string="Info Light Color")
    sbs_color_warning_light = fields.Char(string="Warning Light Color")
    sbs_color_danger_light = fields.Char(string="Danger Light Color")

    sbs_color_brand_dark = fields.Char(string="Brand Dark Color")
    sbs_color_primary_dark = fields.Char(string="Primary Dark Color")
    sbs_color_success_dark = fields.Char(string="Success Dark Color")
    sbs_color_info_dark = fields.Char(string="Info Dark Color")
    sbs_color_warning_dark = fields.Char(string="Warning Dark Color")
    sbs_color_danger_dark = fields.Char(string="Danger Dark Color")

    sbs_theme_color_appsmenu_text = fields.Char(string="Apps Menu Text Color")
    sbs_theme_color_appbar_text = fields.Char(string="AppsBar Text Color")
    sbs_theme_color_appbar_active = fields.Char(string="AppsBar Active Color")
    sbs_theme_color_appbar_background = fields.Char(
        string="AppsBar Background Color"
    )
    sbs_login_background_type = fields.Selection(
        selection=[
            ("color", "Colour"),
            ("image", "Uploaded Image"),
        ],
        string="Login Background",
        config_parameter="sbs_custom_style.login_background_type",
    )
    sbs_login_background_color = fields.Char(
        string="Login Background Colour",
        config_parameter="sbs_custom_style.login_background_color",
    )
    sbs_login_background_image = fields.Binary(
        string="Login Background Image",
        help="Upload a JPG, PNG, GIF, or WEBP image up to 10 MB.",
    )

    @api.constrains("sbs_login_background_color")
    def _check_sbs_login_background_color(self):
        for settings in self:
            color = settings.sbs_login_background_color
            if color and not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                raise ValidationError(
                    "The login background colour must use the #RRGGBB format."
                )

    @api.constrains("sbs_login_background_image")
    def _check_sbs_login_background_image(self):
        for settings in self:
            encoded_image = settings.sbs_login_background_image
            if not encoded_image:
                continue
            try:
                image = base64.b64decode(encoded_image, validate=True)
            except (binascii.Error, ValueError, TypeError) as error:
                raise ValidationError(
                    "The uploaded login background is not a valid image."
                ) from error
            if len(image) > 10 * 1024 * 1024:
                raise ValidationError(
                    "The login background image cannot exceed 10 MB."
                )
            if guess_mimetype(image) not in {
                "image/gif",
                "image/jpeg",
                "image/png",
                "image/webp",
            }:
                raise ValidationError(
                    "The uploaded login background must be an image."
                )

    @property
    def _sbs_color_editor(self):
        return self.env["sbs.custom.style.color.assets.editor"]

    def _sbs_get_color_values(self, url, bundle, variables):
        return self._sbs_color_editor.get_color_variables_values(
            url,
            bundle,
            variables,
        )

    def _sbs_set_mode_color_values(self, values, mode):
        if mode == "light":
            url = self.SBS_COLOR_ASSET_LIGHT_URL
            bundle = self.SBS_COLOR_BUNDLE_LIGHT
        else:
            url = self.SBS_COLOR_ASSET_DARK_URL
            bundle = self.SBS_COLOR_BUNDLE_DARK
        colors = self._sbs_get_color_values(url, bundle, self.SBS_COLOR_FIELDS)
        for variable, value in colors.items():
            values[f"sbs_{variable}_{mode}"] = value
        return values

    def _sbs_set_theme_color_values(self, values):
        colors = self._sbs_get_color_values(
            self.SBS_COLOR_ASSET_THEME_URL,
            self.SBS_COLOR_BUNDLE_THEME,
            self.SBS_THEME_COLOR_FIELDS,
        )
        for variable, value in colors.items():
            values[f"sbs_theme_{variable}"] = value
        return values

    def _sbs_mode_colors_changed(self, mode):
        if mode == "light":
            url = self.SBS_COLOR_ASSET_LIGHT_URL
            bundle = self.SBS_COLOR_BUNDLE_LIGHT
        else:
            url = self.SBS_COLOR_ASSET_DARK_URL
            bundle = self.SBS_COLOR_BUNDLE_DARK
        colors = self._sbs_get_color_values(url, bundle, self.SBS_COLOR_FIELDS)
        return any(
            self[f"sbs_{variable}_{mode}"] != value
            for variable, value in colors.items()
        )

    def _sbs_theme_colors_changed(self):
        colors = self._sbs_get_color_values(
            self.SBS_COLOR_ASSET_THEME_URL,
            self.SBS_COLOR_BUNDLE_THEME,
            self.SBS_THEME_COLOR_FIELDS,
        )
        return any(
            self[f"sbs_theme_{variable}"] != value
            for variable, value in colors.items()
        )

    def _sbs_replace_mode_color_values(self, mode):
        if mode == "light":
            url = self.SBS_COLOR_ASSET_LIGHT_URL
            bundle = self.SBS_COLOR_BUNDLE_LIGHT
        else:
            url = self.SBS_COLOR_ASSET_DARK_URL
            bundle = self.SBS_COLOR_BUNDLE_DARK
        variables = [
            {
                "name": f"$sbs_{variable}",
                "value": self[f"sbs_{variable}_{mode}"],
            }
            for variable in self.SBS_COLOR_FIELDS
        ]
        self._sbs_color_editor.replace_color_variables_values(
            url,
            bundle,
            variables,
        )

    def _sbs_replace_theme_color_values(self):
        variables = [
            {
                "name": f"$sbs_{variable}",
                "value": self[f"sbs_theme_{variable}"],
            }
            for variable in self.SBS_THEME_COLOR_FIELDS
        ]
        self._sbs_color_editor.replace_color_variables_values(
            self.SBS_COLOR_ASSET_THEME_URL,
            self.SBS_COLOR_BUNDLE_THEME,
            variables,
        )

    def _sbs_reset_light_color_assets(self):
        self._sbs_color_editor.reset_color_asset(
            self.SBS_COLOR_ASSET_LIGHT_URL,
            self.SBS_COLOR_BUNDLE_LIGHT,
        )

    def _sbs_reset_dark_color_assets(self):
        self._sbs_color_editor.reset_color_asset(
            self.SBS_COLOR_ASSET_DARK_URL,
            self.SBS_COLOR_BUNDLE_DARK,
        )

    def _sbs_reset_theme_color_assets(self):
        self._sbs_color_editor.reset_color_asset(
            self.SBS_COLOR_ASSET_THEME_URL,
            self.SBS_COLOR_BUNDLE_THEME,
        )

    def action_sbs_reset_light_color_assets(self):
        self._sbs_reset_light_color_assets()
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_sbs_reset_dark_color_assets(self):
        self._sbs_reset_dark_color_assets()
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_sbs_reset_theme_color_assets(self):
        self._sbs_reset_light_color_assets()
        self._sbs_reset_dark_color_assets()
        self._sbs_reset_theme_color_assets()
        return {"type": "ir.actions.client", "tag": "reload"}

    def get_values(self):
        values = super().get_values()
        self._sbs_set_mode_color_values(values, "light")
        self._sbs_set_mode_color_values(values, "dark")
        self._sbs_set_theme_color_values(values)
        values["sbs_login_background_image"] = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sbs_custom_style.login_background_image")
        )
        return values

    def set_values(self):
        result = super().set_values()
        if self._sbs_mode_colors_changed("light"):
            self._sbs_replace_mode_color_values("light")
        if self._sbs_mode_colors_changed("dark"):
            self._sbs_replace_mode_color_values("dark")
        if self._sbs_theme_colors_changed():
            self._sbs_replace_theme_color_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "sbs_custom_style.login_background_image",
            self.sbs_login_background_image or False,
        )
        return result
