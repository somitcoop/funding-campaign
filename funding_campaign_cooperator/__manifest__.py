# -*- coding: utf-8 -*-
{
    'name': 'Funding Campaign Cooperator',
    'version': '17.0.1.0.0',
    'category': 'Cooperative',
    'summary': 'Link between Funding Campaigns and Cooperator modules',
    'description': """
        This module allows you to create and manage funding campaigns
        with multiple funding sources, track progress, and manage
        campaign states.
    """,
    'author': 'Som IT Cooperatiu SCCL ',
    'website': 'https://somit.coop',
    'category': 'Marketing/Fundraising',
    'depends': [
        'funding_campaign',
        'cooperator',
        'swagger_docs',
        'sign_oca',
    ],
    'data': [
        'data/mail_template_data.xml',
        'data/sign_roles_data.xml',
        'views/funding_campaign_view.xml',
        'views/funding_source_view.xml',
        'views/subscription_request.xml',
        'report/subscription_agreement_report.xml',
        'security/ir.model.access.csv',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'maintainers': ['nicolasramos'],
}
