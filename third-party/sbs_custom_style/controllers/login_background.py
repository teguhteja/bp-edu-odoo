import base64
import binascii

from odoo import http
from odoo.http import request
from odoo.tools.mimetypes import guess_mimetype


class SbsLoginBackgroundController(http.Controller):

    @http.route(
        "/sbs_custom_style/login/background",
        type="http",
        auth="none",
        methods=["GET"],
        readonly=True,
        save_session=False,
    )
    def sbs_login_background(self):
        parameters = request.env["ir.config_parameter"].sudo()
        if (
            parameters.get_param("sbs_custom_style.login_background_type")
            != "image"
        ):
            return request.not_found()

        encoded_image = parameters.get_param(
            "sbs_custom_style.login_background_image"
        )
        if not encoded_image:
            return request.not_found()
        try:
            image = base64.b64decode(encoded_image, validate=True)
        except (binascii.Error, ValueError, TypeError):
            return request.not_found()

        mimetype = guess_mimetype(image)
        if mimetype not in {
            "image/gif",
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            return request.not_found()
        return request.make_response(
            image,
            headers=[
                ("Content-Type", mimetype),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )
