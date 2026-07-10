# Part of the EH AI Suite by ERP Heritage.
import json
import logging
import re
import time

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)
_CITATION = re.compile(r"\[SOURCE:(\d+)\]")

# Maps the friendly response-style choice to a sampling temperature. Models that
# reject sampling parameters simply ignore this (see supports_temperature).
RESPONSE_STYLE_TEMPERATURE = {
    "precise": 0.0,
    "balanced": 0.4,
    "creative": 0.8,
}


class EhAiAgent(models.Model):
    _name = "eh.ai.agent"
    _description = "AI Agent"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    subtitle = fields.Char(help="Short tagline shown in agent pickers.")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    partner_id = fields.Many2one(
        "res.partner", string="Agent Identity", ondelete="restrict", copy=False,
        help="Partner the agent posts as in Discuss conversations.",
    )

    chat_model_id = fields.Many2one(
        "eh.ai.model",
        string="Chat Model",
        required=True,
        domain=[("kind", "=", "chat")],
    )
    provider_id = fields.Many2one(related="chat_model_id.provider_id", store=True)

    system_prompt_id = fields.Many2one(
        "eh.ai.prompt",
        string="System Prompt Template",
        domain=[("kind", "=", "system")],
        help="A versioned prompt template. Overrides the inline system prompt when set.",
    )
    system_prompt = fields.Text(
        help="The agent's persistent instructions. Used when no template is selected.",
    )
    response_style = fields.Selection(
        selection=[
            ("precise", "Precise"),
            ("balanced", "Balanced"),
            ("creative", "Creative"),
        ],
        default="balanced",
        required=True,
    )
    max_output_tokens = fields.Integer(
        default=4096,
        help="Upper bound on tokens generated per response.",
    )
    topic_ids = fields.Many2many(
        "eh.ai.topic",
        "eh_ai_agent_topic_rel",
        "agent_id",
        "topic_id",
        string="Topics",
        help="Instruction and tool bundles available to this agent.",
    )

    # Retrieval-augmented generation (RAG).
    embedding_model_id = fields.Many2one(
        "eh.ai.model",
        string="Embedding Model",
        domain=[("kind", "=", "embedding")],
        help="Model used to embed knowledge sources and queries. Required for sources.",
    )
    source_ids = fields.One2many("eh.ai.source", "agent_id", string="Sources")
    source_count = fields.Integer(compute="_compute_source_count")
    use_sources = fields.Boolean(
        string="Use Knowledge Sources",
        default=True,
        help="Retrieve relevant chunks from this agent's sources and add them to the prompt.",
    )
    restrict_to_sources = fields.Boolean(
        string="Answer Only From Sources",
        help="Instruct the agent to answer only from retrieved sources.",
    )
    rag_top_n = fields.Integer(string="Retrieved Chunks", default=5)
    rag_hybrid = fields.Boolean(
        string="Hybrid Search",
        help="Combine vector similarity with keyword (full-text) search. Better for "
             "queries containing exact terms, codes or ids.",
    )
    rag_over_fetch = fields.Integer(
        string="Hybrid Candidates", default=20,
        help="How many candidates each search method contributes before fusion.",
    )

    def _compute_source_count(self):
        # Sources are manager-only; read the count with elevated rights so the
        # agent form stays viewable by regular users (who never see sources).
        data = self.env["eh.ai.source"].sudo()._read_group(
            [("agent_id", "in", self.ids)], ["agent_id"], ["__count"],
        )
        counts = {agent.id: count for agent, count in data}
        for agent in self:
            agent.source_count = counts.get(agent.id, 0)

    # -- public API ----------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        agents = super().create(vals_list)
        for agent in agents:
            agent._get_partner()
        return agents

    def _get_partner(self):
        self.ensure_one()
        if not self.partner_id:
            # Created inactive, like OdooBot (base.partner_root): the agent can
            # still author Discuss messages and be a chat member, but it stays
            # out of the Contacts address book.
            self.partner_id = self.env["res.partner"].sudo().create({
                "name": self.name,
                "type": "contact",
                "active": False,
            })
        elif self.partner_id.active:
            # Self-heal agents created before this behaviour existed.
            self.partner_id.sudo().write({"active": False})
        return self.partner_id

    def eh_ai_channel_id(self):
        """Return the id of this agent's one-to-one channel (opened as a chat window).

        Public so the web client can call it over RPC, so it must enforce its
        own access control: a caller may only open a channel with an agent it is
        allowed to read.
        """
        self.ensure_one()
        self.check_access("read")
        self._get_partner()
        return self.env["discuss.channel"]._eh_ai_get_or_create(self).id

    _NL_FIELD_TYPES = ("char", "text", "selection", "boolean", "integer",
                       "float", "monetary", "date", "datetime", "many2one")
    _NL_FIELD_CAP = 60

    def _nl_search(self, model_name, query, field_names=None):
        """Turn a natural-language query into a validated Odoo search domain."""
        self.ensure_one()
        if not query or not model_name:
            return []
        # Only introspect a model the caller is actually allowed to read: this
        # endpoint is reachable over RPC with a user-supplied model name, so an
        # unguarded fields_get() would leak the schema of any installed model.
        try:
            target = self.env[model_name]
            target.check_access("read")
        except (KeyError, AccessError):
            return []

        # Build a useful field set from the model itself, with the search-view
        # fields first, so the model can use real fields like country_id / city
        # rather than being limited to the few search-view fields.
        names = []
        for name in (field_names or []):
            field = target._fields.get(name)
            if field and field.store and field.type in self._NL_FIELD_TYPES and name not in names:
                names.append(name)
        for name, field in target._fields.items():
            if len(names) >= self._NL_FIELD_CAP:
                break
            if (field.store and field.type in self._NL_FIELD_TYPES
                    and name not in names and not name.startswith("message_")):
                names.append(name)

        meta = target.fields_get(names, ["type", "string", "selection", "relation"])
        lines = []
        for name in names:
            info = meta.get(name) or {}
            line = "- %s (%s): %s" % (name, info.get("type"), info.get("string"))
            if info.get("type") == "selection" and info.get("selection"):
                line += " | values: " + ", ".join(str(k) for k, __ in info["selection"][:20])
            elif info.get("type") == "many2one":
                line += " | use ilike with the related record's name"
            lines.append(line)

        prompt = (
            "Convert the user's request into an Odoo search domain for the model "
            "'%s'.\nFields you may use:\n%s\n\n"
            "Return ONLY a JSON array of [field, operator, value] triplets, for "
            'example [["country_id", "ilike", "United States"], ["is_company", "=", true]].\n'
            "Allowed operators: =, !=, ilike, in, >, <, >=, <=. Use ilike for free "
            "text and for many2one fields (it matches the related record name). For "
            "selection fields use '=' with the technical value. Use only the field "
            "names listed above. If you cannot build a useful filter, return [].\n\n"
            "Request: %s" % (model_name, "\n".join(lines), query)
        )
        result = self.generate_response(prompt)
        return self._eh_ai_parse_domain(result.get("text", ""), set(names))

    @api.model
    def _eh_ai_parse_domain(self, text, allowed_fields):
        match = re.search(r"\[.*\]", text or "", re.DOTALL)
        if not match:
            return []
        try:
            raw = json.loads(match.group(0))
        except ValueError:
            return []
        allowed_ops = {"=", "!=", "ilike", "like", "not ilike", "in", "not in",
                       ">", "<", ">=", "<="}
        domain = []
        for clause in raw if isinstance(raw, list) else []:
            if not (isinstance(clause, (list, tuple)) and len(clause) == 3):
                continue
            field, operator, value = clause
            if field not in allowed_fields or operator not in allowed_ops:
                continue
            if not isinstance(value, (str, int, float, bool, list)):
                continue
            domain.append([field, operator, value])
        return domain

    def generate_response(self, prompt, history=None, extra_context=None):
        """Run the agent against ``prompt`` and return the answer text.

        :param prompt: the user's message.
        :param history: optional list of prior neutral messages
            (``{"role": "user"|"assistant", "content": str}``).
        :param extra_context: optional context note (e.g. the record the user is
            viewing) appended to the system prompt for this call.
        :return: dict ``{"text", "usage", "calls"}``.
        """
        self.ensure_one()
        if not self.chat_model_id:
            raise UserError(_("Agent '%s' has no chat model configured.", self.name))

        adapter = self.chat_model_id.provider_id.get_adapter()
        tool_map = self._build_tool_map()
        system = self._build_system_prompt()
        temperature = self._resolve_temperature()
        messages = list(history or []) + [{"role": "user", "content": prompt}]

        if extra_context:
            system = (system + "\n\n" + extra_context) if system else extra_context

        rag_context, sources_map = self._build_rag_context(prompt)
        if rag_context:
            system = (system + "\n\n" + rag_context) if system else rag_context

        # Budget gate: a hard-stop budget raises before any spend.
        self.env["eh.ai.budget"]._enforce(self)

        from odoo.addons.eh_ai.utils.orchestrator import Orchestrator
        orchestrator = Orchestrator(
            self.env,
            adapter,
            self.chat_model_id.technical_name,
            tool_map=tool_map,
        )
        started = time.monotonic()
        try:
            result = orchestrator.run(
                system,
                messages,
                max_tokens=self.max_output_tokens or self.chat_model_id.max_output_tokens or 4096,
                temperature=temperature,
            )
        except Exception:
            # Usage is logged only for calls that complete. A row written here
            # would be rolled back with the request when the exception
            # propagates anyway, so just record the failure in the server log.
            _logger.warning("EH AI: agent '%s' generation failed", self.name, exc_info=True)
            raise

        latency_ms = int((time.monotonic() - started) * 1000)
        self.env["eh.ai.usage.log"]._record(
            self, self.chat_model_id, result["usage"],
            latency_ms=latency_ms, outcome="ok",
        )

        if sources_map:
            result["text"] = self._apply_citations(result["text"], sources_map)
        return result

    # -- internals -----------------------------------------------------------

    def _resolve_temperature(self):
        self.ensure_one()
        if not self.chat_model_id.supports_temperature:
            return None
        return RESPONSE_STYLE_TEMPERATURE.get(self.response_style, 0.4)

    def _build_system_prompt(self):
        self.ensure_one()
        parts = [self._eh_ai_base_grounding()]
        base = self.system_prompt_id.body if self.system_prompt_id else self.system_prompt
        if base:
            parts.append(base.strip())
        topic_instructions = [
            topic.instructions.strip()
            for topic in self.topic_ids
            if topic.instructions
        ]
        if topic_instructions:
            parts.append("\n\n".join(topic_instructions))
        return "\n\n".join(part for part in parts if part)

    def _eh_ai_base_grounding(self):
        """Always-on preamble that grounds the agent inside the live Odoo DB.

        Without this an agent behaves like a generic chatbot (asking the user to
        upload files); with it, the agent knows it runs inside Odoo and should
        answer data questions through its tools.
        """
        self.ensure_one()
        company = self.company_id or self.env.company
        return (
            "You are an AI assistant built into this Odoo ERP system, working on "
            "the live database of %s. You are not a generic chatbot: when the "
            "user asks about their data (records, documents, contacts, orders, "
            "invoices and so on), use the tools available to you to query Odoo, "
            "and never ask the user to upload or paste files. You only ever see "
            "data the current user is allowed to access." % company.name
        )

    def _build_tool_map(self):
        self.ensure_one()
        if not self.chat_model_id.supports_tools:
            return {}
        actions = self.topic_ids.tool_ids
        if not actions:
            return {}
        return self.env["ir.actions.server"]._eh_ai_build_tool_map(actions)

    # -- retrieval -----------------------------------------------------------

    def _build_rag_context(self, prompt):
        """Return ``(context_text, {source_id: source})`` for the prompt.

        Knowledge sources and their embeddings are not readable by the regular
        AI user group, so the reads here run with elevated rights but stay
        strictly scoped to *this* agent's own sources: the agent is trusted to
        surface its own knowledge to a user who already has access to it.
        """
        self.ensure_one()
        agent = self.sudo()
        model = agent.embedding_model_id
        active = agent.source_ids.filtered(
            lambda source: source.is_active and source.status == "indexed")
        if not (self.use_sources and model and active):
            return None, {}

        adapter = model.provider_id.get_adapter()
        query_vectors = adapter.embed(
            model.technical_name, [prompt],
            dimensions=model.embedding_dimensions or None)
        if not query_vectors:
            return None, {}

        Embedding = self.env["eh.ai.embedding"].sudo()
        top_n = self.rag_top_n or 5
        if self.rag_hybrid:
            hits = Embedding._search_hybrid(
                prompt, query_vectors[0], model.id, active.ids,
                top_n=top_n, over_fetch=self.rag_over_fetch or 20)
        else:
            hits = Embedding._search_similar(query_vectors[0], model.id, active.ids, top_n=top_n)
        if not hits:
            return None, {}

        lines = [
            "Use the following retrieved context to answer. When you rely on a "
            "chunk, cite it inline as [SOURCE:<id>] using the id shown.",
            "",
        ]
        sources_map = {}
        for embedding, __ in hits:
            source = embedding.source_id
            sources_map[source.id] = source
            lines.append("[SOURCE:%s] (%s)" % (source.id, source.name))
            lines.append(embedding.content)
            lines.append("")
        if self.restrict_to_sources:
            lines.append("Answer only using the context above. If the answer is not "
                         "present in it, say that you do not have that information.")
        return "\n".join(lines), sources_map

    def _apply_citations(self, text, sources_map):
        """Rewrite [SOURCE:id] markers into numbered references plus a list."""
        if not text:
            return text
        used = []

        def replace(match):
            source_id = int(match.group(1))
            if source_id not in sources_map:
                return ""
            if source_id not in used:
                used.append(source_id)
            return "[%d]" % (used.index(source_id) + 1)

        text = _CITATION.sub(replace, text).strip()
        if used:
            references = []
            for index, source_id in enumerate(used, start=1):
                source = sources_map[source_id]
                suffix = " (%s)" % source.url if source.url else ""
                references.append("[%d] %s%s" % (index, source.name, suffix))
            text = text + "\n\nSources:\n" + "\n".join(references)
        return text
