from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    funding_campaign_auto_pay_invoice = fields.Boolean(
        string="Auto Pay Invoice on Subscription Validation",
        help="If checked, the invoice generated from a subscription request "
             "will be automatically marked as paid upon validation.",
    )
