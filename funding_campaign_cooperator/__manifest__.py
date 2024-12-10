# -*- coding: utf-8 -*-
{
    'name': 'Funding Campaign Cooperator',
    'version': '16.0.1.0.0',
    'category': 'Cooperative',
    'summary': 'Link between Funding Campaigns and Cooperator modules',
    'depends': [
        'funding_campaign',
        'cooperator',
        'swagger_docs'
    ],
    'data': [
        'views/funding_campaign_view.xml',
        'views/funding_source_view.xml',
        'views/subscription_request.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'AGPL-3',
    'installable': True,
}
