import base64

from odoo.tools import file_open

from . import controllers
from . import models


def _setup_module(env):
    company = env.ref("base.main_company", raise_if_not_found=False)
    if not company:
        return

    values = {}
    with file_open("base/static/img/res_company_logo.png", "rb") as image_file:
        values["sbs_appbar_image"] = base64.b64encode(image_file.read())
    with file_open("web/static/img/favicon.ico", "rb") as favicon_file:
        values["sbs_favicon"] = base64.b64encode(favicon_file.read())
    with file_open(
        "sbs_custom_style/static/src/theme/img/background.webp", "rb"
    ) as background_file:
        encoded_background = base64.b64encode(background_file.read())
        values["sbs_background_image"] = encoded_background
    company.write(values)

    parameters = env["ir.config_parameter"].sudo()
    parameters.set_param("sbs_custom_style.login_background_type", "image")
    parameters.set_param(
        "sbs_custom_style.login_background_image",
        encoded_background.decode("ascii"),
    )


def _uninstall_cleanup(env):
    settings = env["res.config.settings"]
    settings._sbs_reset_light_color_assets()
    settings._sbs_reset_dark_color_assets()
    settings._sbs_reset_theme_color_assets()
