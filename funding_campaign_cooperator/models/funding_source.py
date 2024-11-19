from odoo import models, fields, api

class FundingSource(models.Model):
    _inherit = 'funding.source'

    source_type = fields.Selection(
        selection_add=[
            ('subscription', 'Subscription Requests')
        ],
        ondelete={'subscription': 'set default'}
    )

    @api.depends('campaign_ids', 'campaign_ids.subscription_request_ids.subscription_amount', 'campaign_ids.subscription_request_ids.state')
    def _compute_raised_amount(self):
        super()._compute_raised_amount()
        for source in self:
            if source.source_type == 'subscription':
                source.raised_amount = sum(
                    request.subscription_amount
                    for campaign in source.campaign_ids
                    for request in campaign.subscription_request_ids
                    if request.state in ['done', 'paid']
                )
