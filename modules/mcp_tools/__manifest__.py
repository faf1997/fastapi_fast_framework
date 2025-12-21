{
    "name": "Protocolo mcp",
    "author": "Francisco Fiorentino",
    "category": "tools",
    "summary": "Protocolo mcp para crear herramientas dinámicas desde odoo",
    "version": "17.0.1.0.5",
    "license": "AGPL-3",
    "depends": ['base', 'contacts'],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/mcp_tools_views.xml',
        'wizards/assist_ia_wizard_views.xml'
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}

