# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    # Campo para vincular con subscription.request
    subscription_request_id = fields.Many2one(
        comodel_name="subscription.request",
        compute="_compute_subscription_request_id",
        string="Subscription Request",
        readonly=True,
        store=True,
    )

    @api.depends("record_ref")
    def _compute_subscription_request_id(self):
        for item in self.filtered(
            lambda x: x.record_ref and x.record_ref._name == "subscription.request"
        ):
            item.subscription_request_id = item.record_ref.id

    def action_send_signed_request(self):
        """Override to update subscription request after signing"""
        res = super().action_send_signed_request()
        
        customer_role = self.env.ref(
            "sign_oca.sign_role_customer", raise_if_not_found=False
        )
        company_signer_role = self.env.ref(
            "funding_campaign_cooperator.role_subscription_signer", raise_if_not_found=False
        )

        for request in self:
            if request.state == "2_signed" and request.subscription_request_id and request.data:
                signed_partner_on = False
                signer_partner_contact_id = False
                signed_company_on = False
                signer_company_contact_id = False
                
                # Obtener información de los firmantes
                for signer in request.signer_ids:
                    if signer.role_id == customer_role:
                        signer_partner_contact_id = signer.partner_id.id
                        signed_partner_on = signer.signed_on
                    elif signer.role_id == company_signer_role:
                        if signer.partner_id.user_ids:
                            signer_company_contact_id = signer.partner_id.user_ids[0].id
                        signed_company_on = signer.signed_on

                # Actualizar subscription.request con la información de firma
                vals = {
                    "partner_signed_date": signed_partner_on,
                    "partner_signed_user_id": signer_partner_contact_id,
                    "company_signed_date": signed_partner_on,
                    "company_signed_user_id": signer_company_contact_id,
                    "signed_contract": request.data,
                    "signed_contract_filename": request.name,
                }
                vals = {k: v for k, v in vals.items() if v}
                if vals:
                    request.subscription_request_id.sudo().write(vals)
        
        return res