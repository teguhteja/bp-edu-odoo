import re

from odoo import api, models


class SbsIrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @api.model
    def _sbs_get_login_background_style(self):
        parameters = self.env["ir.config_parameter"].sudo()
        background_type = parameters.get_param(
            "sbs_custom_style.login_background_type"
        )
        common_style = (
            "background-position: center; background-repeat: no-repeat; "
            "background-size: cover;"
        )
        if background_type == "color":
            color = parameters.get_param(
                "sbs_custom_style.login_background_color"
            )
            if color and re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                return f"background-color: {color}; {common_style}"
        elif background_type == "image" and parameters.get_param(
            "sbs_custom_style.login_background_image"
        ):
            return (
                "background-image: "
                "url('/sbs_custom_style/login/background'); "
                f"{common_style}"
            )
        return ""

    def session_info(self):
        result = super().session_info()
        result.update(
            {
                "sbs_chatter_position": self.env.user.sbs_chatter_position,
                "sbs_dialog_size": self.env.user.sbs_dialog_size,
                "sbs_pager_autoload_interval": int(
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param(
                        "sbs_custom_style.pager_autoload_interval",
                        default=30000,
                    )
                ),
            }
        )
        if self.env.user._is_internal():
            companies = result["user_companies"]["allowed_companies"]
            for company in self.env.user.company_ids.with_context(bin_size=True):
                companies[company.id].update(
                    {
                        "sbs_has_appsbar_image": bool(company.sbs_appbar_image),
                        "sbs_has_background_image": bool(
                            company.sbs_background_image
                        ),
                    }
                )
        return result
