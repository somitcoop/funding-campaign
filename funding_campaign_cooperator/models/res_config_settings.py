from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    funding_campaign_auto_pay_invoice = fields.Boolean(
        related="company_id.funding_campaign_auto_pay_invoice",
        readonly=False,
    )
