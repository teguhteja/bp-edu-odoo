# Part of the EH AI Suite by ERP Heritage.
import ipaddress
import logging
import socket
from urllib.parse import urlparse

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.eh_ai.utils.chunking import chunk_text
from odoo.addons.eh_ai.utils.html_text import html_to_text

_logger = logging.getLogger(__name__)

URL_FETCH_TIMEOUT = 30
MIN_USEFUL_CHARS = 20


_NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")


def _effective_ip(address):
    """Unwrap IPv4-in-IPv6 forms to the real IPv4 they would reach.

    An IPv4-mapped (``::ffff:127.0.0.1``) or NAT64 (``64:ff9b::192.168.1.1``)
    IPv6 literal is classed as global by ``ipaddress`` even though it embeds a
    private IPv4, so check the embedded address instead.
    """
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped:
            return address.ipv4_mapped
        if address in _NAT64_PREFIX:
            return ipaddress.ip_address(int(address) & 0xFFFFFFFF)
    return address


def _assert_public_url(url):
    """Reject anything but an http(s) URL that resolves to a public address.

    Knowledge-source URLs are fetched server-side, so without this guard a user
    could point a source at an internal service or a cloud metadata endpoint
    (SSRF). Every address the host resolves to must be a global unicast IP.

    Note: this validates at resolve time and does not pin the IP, so a
    determined attacker controlling DNS could still rebind between this check
    and the fetch. Full DNS pinning is tracked as a later hardening item.
    """
    parsed = urlparse(url or "")
    if parsed.scheme not in ("http", "https"):
        raise UserError(_("Only http and https source URLs are allowed."))
    host = parsed.hostname
    if not host:
        raise UserError(_("The source URL has no host."))
    try:
        infos = socket.getaddrinfo(host, parsed.port or None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as error:
        raise UserError(_("The source URL host could not be resolved: %s", error))
    for info in infos:
        address = _effective_ip(ipaddress.ip_address(info[4][0]))
        if not address.is_global:
            raise UserError(_("The source URL resolves to a non-public address and was blocked."))


class EhAiSource(models.Model):
    _name = "eh.ai.source"
    _description = "AI Agent Knowledge Source"
    _order = "agent_id, sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    agent_id = fields.Many2one("eh.ai.agent", required=True, ondelete="cascade", index=True)
    type = fields.Selection(
        selection=[("binary", "File"), ("url", "Web Page")],
        required=True,
        default="binary",
    )
    attachment_id = fields.Many2one("ir.attachment", ondelete="cascade")
    upload_file = fields.Binary(string="Upload File")
    upload_filename = fields.Char(string="File Name")
    url = fields.Char()
    is_active = fields.Boolean(string="Active for Retrieval", default=True)
    status = fields.Selection(
        selection=[
            ("processing", "Processing"),
            ("indexed", "Indexed"),
            ("failed", "Failed"),
        ],
        default="processing",
        required=True,
    )
    error_details = fields.Text(readonly=True)
    embedding_ids = fields.One2many("eh.ai.embedding", "source_id")
    embedding_count = fields.Integer(compute="_compute_embedding_count")

    def _compute_embedding_count(self):
        data = self.env["eh.ai.embedding"]._read_group(
            [("source_id", "in", self.ids)], ["source_id"], ["__count"],
        )
        counts = {source.id: count for source, count in data}
        for source in self:
            source.embedding_count = counts.get(source.id, 0)

    # -- lifecycle -----------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._absorb_upload(vals)
            if not vals.get("name"):
                vals["name"] = self._default_name(vals)
        sources = super().create(vals_list)
        sources._trigger_indexing()
        return sources

    def _absorb_upload(self, vals):
        """Turn an uploaded binary into an ir.attachment source."""
        if vals.get("upload_file") and not vals.get("attachment_id"):
            attachment = self.env["ir.attachment"].create({
                "name": vals.get("upload_filename") or vals.get("name") or _("Source file"),
                "datas": vals["upload_file"],
            })
            vals["attachment_id"] = attachment.id
            vals["type"] = "binary"
        vals.pop("upload_file", None)
        vals.pop("upload_filename", None)

    def _default_name(self, vals):
        if vals.get("url"):
            return vals["url"]
        attachment_id = vals.get("attachment_id")
        if attachment_id:
            attachment = self.env["ir.attachment"].browse(attachment_id)
            if attachment.exists():
                return attachment.name
        return _("Source")

    def _trigger_indexing(self):
        if self:
            self.env.ref("eh_ai.ir_cron_generate_embeddings")._trigger()

    def action_reprocess(self):
        self.embedding_ids.unlink()
        self.write({"status": "processing", "error_details": False})
        self._trigger_indexing()

    # -- content extraction --------------------------------------------------

    def _extract_content(self):
        self.ensure_one()
        if self.type == "url":
            return self._extract_url_content()
        return self._extract_attachment_content()

    def _extract_attachment_content(self):
        attachment = self.attachment_id
        if not attachment:
            raise UserError(_("No file is attached to this source."))
        if attachment.mimetype and attachment.mimetype.startswith("text/"):
            return (attachment.raw or b"").decode("utf-8", errors="ignore")
        # attachment_indexation populates index_content with extracted text for
        # PDFs, office documents and similar at attachment-create time.
        return attachment.index_content or ""

    def _extract_url_content(self):
        if not self.url:
            raise UserError(_("No URL is set on this source."))
        _assert_public_url(self.url)
        response = requests.get(self.url, timeout=URL_FETCH_TIMEOUT, allow_redirects=False,
                                headers={"User-Agent": "Mozilla/5.0 (EH AI)"})
        response.raise_for_status()
        return html_to_text(response.text)

    # -- chunking ------------------------------------------------------------

    def _create_chunks(self):
        self.ensure_one()
        model = self.agent_id.embedding_model_id
        if not model:
            self._fail(_("The agent has no embedding model configured."))
            return
        try:
            text = self._extract_content()
        except Exception as error:  # noqa: BLE001 - surface as a failed source
            _logger.warning("EH AI: extraction failed for source %s: %s", self.id, error)
            self._fail(str(error))
            return

        if not text or len(text.strip()) < MIN_USEFUL_CHARS:
            self._fail(_("No usable text could be extracted."))
            return

        chunks = chunk_text(text)
        if not chunks:
            self._fail(_("The content produced no chunks."))
            return

        self.env["eh.ai.embedding"].create([
            {
                "source_id": self.id,
                "embedding_model_id": model.id,
                "sequence": index,
                "content": "%s\n\n%s" % (self.name, chunk),
            }
            for index, chunk in enumerate(chunks)
        ])

    def _update_status_after_embedding(self):
        self.ensure_one()
        if self.status != "processing":
            return
        if not self.embedding_ids:
            return
        # Stay in 'processing' while any chunk is still embeddable or awaiting a
        # retry, so a transient batch failure does not strand the rest of the
        # document as orphaned, never-processed chunks.
        pending = self.embedding_ids.filtered(
            lambda e: not e.embedding_json and not e.has_failed)
        if pending:
            return
        if self.embedding_ids.filtered(lambda e: e.has_failed):
            self._fail(_("One or more chunks could not be embedded."))
            return
        self.status = "indexed"

    def _fail(self, message):
        self.write({"status": "failed", "error_details": message})
