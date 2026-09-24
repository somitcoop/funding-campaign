# Copyright 2026 Som IT Cooperatiu SCCL
# Nicolás Ramos https://github.com/nicolasramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class CarsharingContribution(models.Model):
    _inherit = "carsharing.contribution"

    def _close_contribution(self, close_date=None, close_reason=False):
        """Propagate the cancellation to the linked subscription request.

        When a contribution is cancelled, the subscription request it comes
        from must leave the ``paid`` state and become ``cancelled`` so the
        funding side stays consistent with the contribution.
        """
        res = super()._close_contribution(
            close_date=close_date, close_reason=close_reason
        )
        if close_reason == "cancellation":
            for contribution in self:
                subscription = contribution.subscription_request_id
                if subscription and subscription.state == "paid":
                    subscription.cancel_subscription_request()
        return res
