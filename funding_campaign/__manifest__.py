# -*- coding: utf-8 -*-
{
    'name': 'Funding Campaign Base',
    'version': '17.0.1.0.1',
    'summary': 'Manage and track funding campaigns with multiple sources',
    'description': """
        This module allows you to create and manage funding campaigns
        with multiple funding sources, track progress, and manage
        campaign states.
    """,
    'author': 'Som IT Cooperatiu SCCL ',
    'website': 'https://somit.coop',
    'category': 'Marketing/Fundraising',
    'depends': ['base', 'mass_mailing', 'swagger_docs'],
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
    'maintainers': ['nicolasramos'],
    'icon': 'funding_campaign/static/description/icon.png',
}
