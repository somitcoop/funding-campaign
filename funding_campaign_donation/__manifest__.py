# -*- coding: utf-8 -*-
{
    'name': 'Funding Campaign Donation',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Donations',
    'summary': 'Integration between Funding Campaigns and Donations',
    'author': 'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/donation',
    'license': 'AGPL-3',
    'depends': [
        'funding_campaign',
        'donation',
    ],
    "data": [
        "views/donation_campaign_views.xml",
        "views/funding_campaign_view.xml",
        "views/funding_source_view.xml"
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
