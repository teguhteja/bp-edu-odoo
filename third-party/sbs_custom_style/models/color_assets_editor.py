import base64
import re

from odoo import api, models
from odoo.addons.base.models.assetsbundle import EXTENSIONS
from odoo.tools import misc


class SbsColorAssetsEditor(models.AbstractModel):
    _name = "sbs.custom.style.color.assets.editor"
    _description = "SBS Custom Style Color Asset Utilities"

    @api.model
    def _get_custom_colors_url(self, url, bundle):
        return f"/_custom/{bundle}{url}"

    @api.model
    def _get_color_info_from_url(self, url):
        match = re.match(r"^(/_custom/([^/]+))?/(\w+)/([/\w]+\.\w+)$", url)
        if not match:
            return False
        return {
            "module": match.group(3),
            "resource_path": match.group(4),
            "customized": bool(match.group(1)),
            "bundle": match.group(2) or False,
        }

    @api.model
    def _get_colors_attachment(self, custom_url):
        return self.env["ir.attachment"].search([("url", "=", custom_url)])

    @api.model
    def _get_colors_asset(self, custom_url):
        return self.env["ir.asset"].search([("path", "like", custom_url)])

    @api.model
    def _get_colors_from_url(self, url, bundle):
        custom_url = self._get_custom_colors_url(url, bundle)
        url_info = self._get_color_info_from_url(custom_url)
        if url_info and url_info["customized"]:
            attachment = self._get_colors_attachment(custom_url)
            if attachment:
                return base64.b64decode(attachment.datas)
        with misc.file_open(url.strip("/"), "rb", filter_ext=EXTENSIONS) as asset_file:
            return asset_file.read()

    def _get_color_variable(self, content, variable):
        match = re.search(fr"{re.escape(variable)}:?\s(.*?);", content)
        return match and match.group(1)

    def _get_color_variables(self, content, variables):
        return {
            variable: self._get_color_variable(content, f"$sbs_{variable}")
            for variable in variables
        }

    def _replace_color_variables(self, content, variables):
        for variable in variables:
            name = re.escape(variable["name"])
            content = re.sub(
                fr"{name}:?\s(.*?);",
                f'{variable["name"]}: {variable["value"]};',
                content,
            )
        return content

    @api.model
    def _save_color_asset(self, url, bundle, content):
        custom_url = self._get_custom_colors_url(url, bundle)
        asset_url = url[1:] if url.startswith(("/", "\\")) else url
        datas = base64.b64encode((content or "\n").encode())
        attachment = self._get_colors_attachment(custom_url)
        if attachment:
            attachment.write({"datas": datas})
            self.env.registry.clear_cache("assets")
            return

        attachment_values = {
            "name": url.split("/")[-1],
            "type": "binary",
            "mimetype": "text/scss",
            "datas": datas,
            "url": custom_url,
        }
        asset_values = {
            "path": custom_url,
            "target": url,
            "directive": "replace",
        }
        target_asset = self._get_colors_asset(asset_url)
        if target_asset:
            asset_values.update(
                {
                    "name": f"{target_asset.name} override",
                    "bundle": target_asset.bundle,
                    "sequence": target_asset.sequence,
                }
            )
        else:
            asset_values.update(
                {
                    "name": f'{bundle}: replace {custom_url.split("/")[-1]}',
                    "bundle": self.env["ir.asset"]._get_related_bundle(url, bundle),
                }
            )
        self.env["ir.attachment"].create(attachment_values)
        self.env["ir.asset"].create(asset_values)

    def get_color_variables_values(self, url, bundle, variables):
        content = self._get_colors_from_url(url, bundle).decode()
        return self._get_color_variables(content, variables)

    def replace_color_variables_values(self, url, bundle, variables):
        original = self._get_colors_from_url(url, bundle).decode()
        content = self._replace_color_variables(original, variables)
        self._save_color_asset(url, bundle, content)

    def reset_color_asset(self, url, bundle):
        custom_url = self._get_custom_colors_url(url, bundle)
        self._get_colors_attachment(custom_url).unlink()
        self._get_colors_asset(custom_url).unlink()
