# -*- coding: utf-8 -*-
{
    'name': 'Funding Campaign Base',
    'version': '1.0',
    'summary': """ Funding campaign Summary """,
    'author': '',
    'website': '',
    'category': '',
    'depends': ['base', 'mass_mailing'],
    'data': [
        'security/ir.model.access.csv',
        'views/funding_campaign_views.xml',
        'views/funding_source_views.xml',
        'views/funding_campaign_menus.xml',
    ],

    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
