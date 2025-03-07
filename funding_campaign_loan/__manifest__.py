# -*- coding: utf-8 -*-
{
    "name": "Funding_campaign_loan",
    "version": "17.0.1.0.0",
    "summary": "Funding_campaign_loan Summary",
    "author": "Som IT Cooperatiu SCCL",
    "website": "https://somit.coop",
    "category": "Marketing/Fundraising",
    "depends": [
        "funding_campaign",
        "account_loan_permanent",
        "cooperator_share_increase_loan",
        "swagger_docs",
    ],
    "data": [
        "data/ir_sequence_data.xml",
        "security/ir.model.access.csv",
        "views/funding_campaign_view.xml",
        "views/funding_loan_request_views.xml",
        "views/funding_loan_template_views.xml",
        "views/menu_views.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
    "maintainers": ["nicolasramos"],
}
