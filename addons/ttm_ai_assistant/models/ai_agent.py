"""
AI Agent — core model untuk koneksi LLM dan agentic tool-calling loop.

Mendukung Groq (gratis), OpenRouter, dan OpenAI dengan format OpenAI-compatible.
Tool calling: search_records, read_record, update_field, create_record,
              get_current_record_info.
"""
import json
import logging
import re
import time

import requests

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────────

DEFAULT_SYSTEM_PROMPT = (
    "Kamu adalah asisten AI yang terintegrasi dalam Odoo ERP. "
    "Kamu dapat membantu pengguna dengan mencari data, membaca record, "
    "memperbarui field, dan membuat record baru menggunakan tools yang tersedia. "
    "Selalu jawab dalam bahasa yang sama dengan pertanyaan pengguna (Indonesia atau Inggris). "
    "Berikan jawaban yang jelas, singkat, dan akurat. "
    "Saat melakukan operasi yang mengubah data, konfirmasi apa yang telah dilakukan."
)

DEFAULT_MODELS = {
    'groq': 'llama-3.3-70b-versatile',
    'openrouter': 'deepseek/deepseek-chat',
    'openai': 'gpt-4o-mini',
}

PROVIDER_URLS = {
    'groq': 'https://api.groq.com/openai/v1/chat/completions',
    'openrouter': 'https://openrouter.ai/api/v1/chat/completions',
    'openai': 'https://api.openai.com/v1/chat/completions',
}

AI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_records",
            "description": (
                "Cari records dalam model Odoo berdasarkan filter (domain). "
                "Gunakan untuk mencari daftar data, contoh: invoice terbaru, "
                "customer dengan nama tertentu, produk dengan kategori tertentu."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Nama model Odoo, contoh: sale.order, res.partner, account.move, product.product"
                    },
                    "domain": {
                        "type": "array",
                        "description": 'Odoo domain filter. Contoh: [["state","=","sale"]] atau [["partner_id.name","ilike","budi"]]',
                        "items": {}
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Daftar field yang dikembalikan. Kosong = field utama saja."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maksimum record yang dikembalikan. Default 10, maksimum 50.",
                        "default": 10
                    }
                },
                "required": ["model", "domain"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_record",
            "description": "Baca detail lengkap satu record berdasarkan model dan ID-nya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Nama model Odoo"},
                    "record_id": {"type": "integer", "description": "ID record"},
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Field spesifik yang ingin dibaca. Kosong = semua field."
                    }
                },
                "required": ["model", "record_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_field",
            "description": "Perbarui nilai satu field pada sebuah record Odoo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Nama model Odoo"},
                    "record_id": {"type": "integer", "description": "ID record yang akan diperbarui"},
                    "field": {"type": "string", "description": "Nama field yang diperbarui, contoh: priority, date_deadline"},
                    "value": {"description": "Nilai baru untuk field tersebut"}
                },
                "required": ["model", "record_id", "field", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_record",
            "description": "Buat record baru dalam model Odoo, contoh: buat activity, buat sale order line.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Nama model Odoo"},
                    "values": {
                        "type": "object",
                        "description": "Nilai field untuk record baru, contoh: {\"summary\": \"Call\", \"user_id\": 1}"
                    }
                },
                "required": ["model", "values"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_record_info",
            "description": (
                "Ambil informasi lengkap tentang record aktif saat @ai dipanggil. "
                "Gunakan ini untuk menjawab pertanyaan tentang record yang sedang dibuka, "
                "contoh: 'siapa customer ini?', 'berapa total invoice ini?', 'apa status SO ini?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

MAX_AGENTIC_ITERATIONS = 6
MAX_SEARCH_LIMIT = 50


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _safe_serialize(val):
    """Konversi nilai field Odoo ke tipe JSON-serializable."""
    if isinstance(val, bytes):
        return '[binary data]'
    if isinstance(val, (list, tuple)):
        # Many2one returns (id, name) tuple
        if len(val) == 2 and isinstance(val[0], int) and isinstance(val[1], str):
            return {'id': val[0], 'name': val[1]}
        return [_safe_serialize(v) for v in val]
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return val


def _clean_record_data(data: dict) -> dict:
    """Filter field binary dan serialize nilai Odoo."""
    return {
        k: _safe_serialize(v)
        for k, v in data.items()
        if not k.startswith('_') and not isinstance(v, bytes)
    }


def _escape_html(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _apply_inline_markdown(text: str) -> str:
    """Konversi markdown ringan (bold/italic/code) dari respons LLM ke tag HTML."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!_)_([^_\n]+?)_(?!_)', r'<i>\1</i>', text)
    text = re.sub(r'`([^`\n]+?)`', r'<code>\1</code>', text)
    return text


def _format_ai_response(content: str) -> str:
    """
    Format teks respons AI menjadi HTML rapi untuk chatter/Discuss:
    markdown ringan (**bold**, *italic*, `code`) dikonversi ke tag HTML
    yang sesuai, bukan dibiarkan tampil sebagai teks mentah.
    """
    escaped = _escape_html((content or '').strip())
    formatted = _apply_inline_markdown(escaped)
    paragraphs = [p.strip() for p in formatted.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [formatted]
    body = ''.join(f'<p>{p.replace(chr(10), "<br/>")}</p>' for p in paragraphs)
    return f'<p><b>🤖 AI Assistant</b></p>{body}'


# ─── Model ───────────────────────────────────────────────────────────────────

class AiAgent(models.Model):
    _name = 'ai.agent'
    _description = 'AI Agent Configuration'
    _rec_name = 'name'
    _order = 'priority desc, name'

    name = fields.Char(string='Nama Agent', required=True)
    priority = fields.Integer(
        string='Prioritas',
        default=10,
        help='Semakin tinggi nilai = semakin diprioritaskan. Agent dengan prioritas tertinggi digunakan saat @ai dipanggil di Discuss.',
    )
    api_provider = fields.Selection([
        ('groq', 'Groq (Llama — Free Tier)'),
        ('openrouter', 'OpenRouter (Multi-model)'),
        ('openai', 'OpenAI (GPT)'),
    ], string='AI Provider', required=True, default='groq')
    api_key = fields.Char(string='API Key')
    model_name = fields.Char(
        string='Nama Model',
        help='Groq: llama-3.3-70b-versatile | OpenRouter: deepseek/deepseek-chat | OpenAI: gpt-4o-mini'
    )
    system_prompt = fields.Text(string='System Prompt', default=DEFAULT_SYSTEM_PROMPT)
    max_tokens = fields.Integer(string='Max Tokens', default=2048)
    temperature = fields.Float(string='Temperature', default=0.7)
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        label_map = dict(self._fields['api_provider'].selection)
        for rec in self:
            rec.display_name = f'[{label_map.get(rec.api_provider, "")}] {rec.name}'

    # ─── Public API ──────────────────────────────────────────────────────────

    @api.model
    def call_from_settings(self, command, res_model=None, res_id=None):
        """
        Gunakan ai.agent record dengan prioritas tertinggi.
        Fallback ke ir.config_parameter (Settings) jika tidak ada record aktif.
        """
        # Utamakan ai.agent record aktif dengan prioritas tertinggi
        agent = self.sudo().search([('active', '=', True)], limit=1)
        if agent:
            return agent.process_message(command, res_model, res_id)

        # Fallback: gunakan konfigurasi dari Settings
        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('ttm_ai.api_key', '')
        if not api_key:
            return (
                '<p><b>AI Assistant belum dikonfigurasi.</b><br/>'
                'Buat AI Agent di <b>Settings → Technical → AI Agents</b> '
                'atau isi API Key di <b>Settings → General Settings</b>.</p>'
            )

        provider = ICP.get_param('ttm_ai.api_provider', 'groq')
        model_name = (
            ICP.get_param('ttm_ai.model_name', '')
            or DEFAULT_MODELS.get(provider, 'llama-3.3-70b-versatile')
        )
        agent = self.new({
            'name': 'System Default',
            'api_provider': provider,
            'api_key': api_key,
            'model_name': model_name,
            'system_prompt': ICP.get_param('ttm_ai.system_prompt', DEFAULT_SYSTEM_PROMPT),
            'max_tokens': int(ICP.get_param('ttm_ai.max_tokens', '2048') or 2048),
            'temperature': float(ICP.get_param('ttm_ai.temperature', '0.7') or 0.7),
        })
        return agent.process_message(command, res_model, res_id)

    def process_message(self, command, res_model=None, res_id=None):
        """Jalankan agentic loop dan catat hasilnya ke ai.agent.log."""
        self.ensure_one()
        start = time.time()
        try:
            response = self._process_message_inner(command, res_model, res_id)
            is_error = ('❌' in response) or ('⚠️' in response)
            self._log_interaction(
                command, response, res_model, res_id,
                error=is_error, duration=time.time() - start,
            )
            return response
        except Exception as e:
            _logger.exception('AI Agent process_message error tak terduga')
            self._log_interaction(
                command, None, res_model, res_id,
                error=True, error_message=str(e), duration=time.time() - start,
            )
            return f'<p>❌ Terjadi error internal: {e}</p>'

    def _log_interaction(self, command, response, res_model, res_id,
                          error=False, error_message=None, duration=0.0):
        try:
            self.env['ai.agent.log'].sudo().create({
                'agent_id': self.id if isinstance(self.id, int) else False,
                'user_id': self.env.uid,
                'command': command,
                'response': response or False,
                'error_message': error_message or (response if error else False),
                'state': 'error' if error else 'success',
                'res_model': res_model or False,
                'res_id': res_id or False,
                'duration': duration,
            })
        except Exception:
            _logger.exception('Gagal menyimpan AI Agent Log')

    def _process_message_inner(self, command, res_model=None, res_id=None):
        """
        Jalankan agentic loop:
        1. Kirim pesan ke LLM dengan tools
        2. Jika LLM meminta tool call → eksekusi → kirim hasil balik
        3. Ulangi sampai LLM memberikan respons teks final
        """
        self.ensure_one()

        # Build system prompt + context record
        system_content = self.system_prompt or DEFAULT_SYSTEM_PROMPT
        if res_model and res_id:
            ctx = self._build_record_context(res_model, res_id)
            if ctx:
                system_content = f"{system_content}\n\n{ctx}"

        messages = [
            {'role': 'system', 'content': system_content},
            {'role': 'user', 'content': command},
        ]

        for iteration in range(MAX_AGENTIC_ITERATIONS):
            _logger.info(
                'AI Agent [%s] iteration %d — messages: %d',
                self.api_provider, iteration + 1, len(messages)
            )

            response, error_detail = self._call_api(messages)
            if response is None:
                if error_detail:
                    return f'<p>❌ AI gagal merespons: {_escape_html(error_detail)}</p>'
                return (
                    '<p>❌ Tidak dapat terhubung ke AI. '
                    'Periksa koneksi internet dan API key.</p>'
                )

            choices = response.get('choices', [])
            if not choices:
                _logger.error('AI API — no choices in response: %s', response)
                return '<p>❌ Respons AI tidak valid (tidak ada choices).</p>'

            msg = choices[0].get('message', {})
            tool_calls = msg.get('tool_calls') or []

            if not tool_calls:
                # Final response — format ringan (markdown -> HTML rapi)
                content = (msg.get('content') or '').strip()
                if not content:
                    return '<p>✅ Selesai.</p>'
                return _format_ai_response(content)

            # Append assistant message (with tool_calls) to history
            messages.append({
                'role': 'assistant',
                'content': msg.get('content'),
                'tool_calls': tool_calls,
            })

            # Execute each tool call and append results
            for tc in tool_calls:
                fn = tc.get('function', {})
                tool_name = fn.get('name', '')
                try:
                    tool_args = json.loads(fn.get('arguments') or '{}')
                except json.JSONDecodeError:
                    tool_args = {}

                _logger.info('AI tool call: %s(%s)', tool_name, str(tool_args)[:200])
                result = self._execute_tool(tool_name, tool_args, res_model, res_id)
                _logger.info('AI tool result: %s', str(result)[:300])

                messages.append({
                    'role': 'tool',
                    'tool_call_id': tc.get('id', ''),
                    'content': json.dumps(result, default=_safe_serialize, ensure_ascii=False),
                })

        return '<p>⚠️ AI melebihi batas iterasi. Proses dihentikan.</p>'

    def action_test_connection(self):
        """Test koneksi ke LLM API dan tampilkan hasilnya."""
        self.ensure_one()
        if not self.api_key:
            return self._notify('❌ API Key kosong', 'Isi API Key terlebih dahulu.', 'danger')

        response, error_detail = self._call_api([
            {'role': 'system', 'content': 'You are a test assistant.'},
            {'role': 'user', 'content': 'Reply exactly: "Connection OK"'},
        ])
        if response and response.get('choices'):
            content = response['choices'][0]['message'].get('content', '?')
            model_used = response.get('model', self.model_name)
            return self._notify(
                '✅ Koneksi Berhasil',
                f'Model: {model_used}\nRespons: {content}',
                'success',
            )
        return self._notify(
            '❌ Koneksi Gagal',
            error_detail or 'Tidak ada respons. Cek API key dan model name.',
            'danger',
        )

    # ─── Private: API call ────────────────────────────────────────────────────

    def _get_tools(self):
        """Return daftar tools yang tersedia. Override di subclass untuk menambah tools."""
        return AI_TOOLS

    def _call_api(self, messages, use_tools=True):
        """Kirim request ke LLM API. Return tuple (dict respons | None, pesan_error | None).

        use_tools=False untuk pemanggilan satu-arah (mis. ekstraksi teks -> JSON)
        yang tidak boleh dibelokkan LLM jadi tool call.
        """
        url = PROVIDER_URLS.get(self.api_provider, PROVIDER_URLS['groq'])
        model = self.model_name or DEFAULT_MODELS.get(self.api_provider, 'llama-3.3-70b-versatile')

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        if self.api_provider == 'openrouter':
            headers['HTTP-Referer'] = 'https://odoo.com'
            headers['X-Title'] = 'Odoo AI Assistant'

        payload = {
            'model': model,
            'messages': messages,
            'max_tokens': int(self.max_tokens or 2048),
            'temperature': float(self.temperature if self.temperature is not None else 0.7),
        }
        if use_tools:
            payload['tools'] = self._get_tools()
            payload['tool_choice'] = 'auto'

        _logger.debug('AI API → %s | model=%s | messages=%d', url, model, len(messages))

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            _logger.debug('AI API ← status=%s | choices=%d', resp.status_code, len(data.get('choices', [])))
            return data, None

        except requests.Timeout:
            _logger.error('AI API timeout setelah 60s (provider=%s, model=%s)', self.api_provider, model)
            return None, 'Timeout — server AI tidak merespons dalam 60 detik.'

        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else '?'
            try:
                err_msg = e.response.json().get('error', {}).get('message', '')
            except Exception:
                err_msg = getattr(e.response, 'text', '')[:300]
            _logger.error('AI API HTTP %s: %s', status, err_msg)
            return None, f'HTTP {status} dari provider {self.api_provider}: {err_msg}'

        except Exception as e:
            _logger.exception('AI API unexpected error')
            return None, str(e)

    # ─── Private: Tool execution ─────────────────────────────────────────────

    def _execute_tool(self, tool_name, args, res_model=None, res_id=None):
        """Eksekusi tool yang diminta LLM via Odoo ORM."""
        try:
            if tool_name == 'get_current_record_info':
                return self._tool_get_current_record(res_model, res_id)

            elif tool_name == 'search_records':
                return self._tool_search(args)

            elif tool_name == 'read_record':
                return self._tool_read(args)

            elif tool_name == 'update_field':
                return self._tool_update(args)

            elif tool_name == 'create_record':
                return self._tool_create(args)

            else:
                return {'error': f'Tool tidak dikenal: {tool_name!r}'}

        except Exception as e:
            _logger.exception('Tool execution error [%s]', tool_name)
            return {'error': str(e)}

    def _tool_get_current_record(self, res_model, res_id):
        if not res_model or not res_id:
            return {'error': 'Tidak ada context record aktif. @ai dipanggil di luar record?'}
        if res_model not in self.env:
            return {'error': f'Model {res_model!r} tidak ditemukan.'}
        record = self.env[res_model].browse(res_id)
        if not record.exists():
            return {'error': f'Record {res_model} #{res_id} tidak ditemukan.'}
        raw = record.read([])[0]
        return {
            'model': res_model,
            'model_description': self.env[res_model]._description or res_model,
            'id': res_id,
            'data': _clean_record_data(raw),
        }

    def _tool_search(self, args):
        model_name = args.get('model', '')
        if not model_name or model_name not in self.env:
            return {'error': f'Model {model_name!r} tidak ditemukan.'}
        domain = args.get('domain', [])
        field_list = args.get('fields') or []
        limit = min(int(args.get('limit', 10) or 10), MAX_SEARCH_LIMIT)
        records = self.env[model_name].search_read(domain, field_list or False, limit=limit)
        serialized = [_clean_record_data(r) for r in records]
        return {'count': len(serialized), 'records': serialized}

    def _tool_read(self, args):
        model_name = args.get('model', '')
        if not model_name or model_name not in self.env:
            return {'error': f'Model {model_name!r} tidak ditemukan.'}
        record_id = int(args.get('record_id', 0) or 0)
        field_list = args.get('fields') or []
        record = self.env[model_name].browse(record_id)
        if not record.exists():
            return {'error': f'Record {model_name} #{record_id} tidak ditemukan.'}
        raw = record.read(field_list or [])[0]
        return _clean_record_data(raw)

    def _tool_update(self, args):
        model_name = args.get('model', '')
        if not model_name or model_name not in self.env:
            return {'error': f'Model {model_name!r} tidak ditemukan.'}
        record_id = int(args.get('record_id', 0) or 0)
        field_name = args.get('field', '')
        value = args.get('value')
        if not field_name:
            return {'error': 'Nama field tidak boleh kosong.'}
        self.env[model_name].browse(record_id).write({field_name: value})
        return {
            'success': True,
            'model': model_name,
            'record_id': record_id,
            'updated': {field_name: value},
        }

    def _tool_create(self, args):
        model_name = args.get('model', '')
        if not model_name or model_name not in self.env:
            return {'error': f'Model {model_name!r} tidak ditemukan.'}
        values = args.get('values') or {}
        if not values:
            return {'error': 'Values tidak boleh kosong.'}
        new_rec = self.env[model_name].create(values)
        return {'success': True, 'model': model_name, 'id': new_rec.id}

    def _build_record_context(self, res_model, res_id):
        """Build string context tentang record aktif untuk system prompt."""
        try:
            if res_model not in self.env:
                return ''
            record = self.env[res_model].browse(res_id)
            if not record.exists():
                return ''
            raw = record.read([])[0]
            safe = _clean_record_data(raw)
            data_str = json.dumps(safe, ensure_ascii=False, default=str)
            # Truncate agar tidak melebihi context window
            if len(data_str) > 3000:
                data_str = data_str[:3000] + '...[terpotong]'
            model_desc = self.env[res_model]._description or res_model
            return (
                f"=== Context Record Aktif ===\n"
                f"Model: {res_model} ({model_desc})\n"
                f"ID: {res_id}\n"
                f"Data: {data_str}"
            )
        except Exception as e:
            _logger.warning('Gagal build context untuk %s #%s: %s', res_model, res_id, e)
            return ''

    @staticmethod
    def _notify(title, message, ntype='info'):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': ntype,
                'sticky': ntype == 'danger',
            },
        }
