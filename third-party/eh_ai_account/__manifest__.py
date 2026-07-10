# Part of the EH AI Suite by ERP Heritage.
{
    'name': 'AI for Accounting',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Enable AI agents to query customer receivables directly, get_customer_balance lookup tool, accounting topic context, seamless integration with the EH AI Agents Engine, bring-your-own-key LLM provider support.',
    'description': 'AI for Accounting extends the EH AI Agents Engine with a purpose-built tool and topic for accounting workloads. When you install this module, agents gain access to a get_customer_balance tool that searches your customer database by name and returns their outstanding receivable balance. The module ships a pre-configured Accounting topic that primes the agent to handle financial queries professionally, using the balance tool appropriately and stating amounts with proper decimal precision. No bundled cloud service, no IAP charges, no LLM provider lock-in, you bring your own key to OpenAI, Google Gemini, Azure OpenAI, local Ollama, or any OpenAI-compatible endpoint.',
    'author': 'ERP Heritage',
    'website': 'https://erpheritage.com.au',
    'license': 'OPL-1',
    'depends': ['eh_ai', 'account'],
    'data': ['data/eh_ai_account_data.xml'],
    'application': False,
    'installable': True,
    'images': ['static/description/banner.gif'],
}
