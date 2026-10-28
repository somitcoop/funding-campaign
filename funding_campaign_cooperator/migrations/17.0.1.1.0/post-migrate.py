# Copyright 2026 Som IT Cooperatiu SCCL
# Nicolás Ramos https://github.com/nicolasramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Normalize legacy 'increase_remunerated' type to the remunerated flag.

    From 17.0.1.1.0 remunerated increases are stored as
    ``type = 'increase'`` plus ``remunerated = True``. All legacy requests
    with the old ``increase_remunerated`` type are converted so the
    historical data stays coherent with the new creation flow.
    """
    if not version:
        return
    cr.execute(
        """
        UPDATE subscription_request
           SET type = 'increase', remunerated = TRUE
         WHERE type = 'increase_remunerated'
        """
    )
    _logger.info(
        "funding_campaign_cooperator: normalized %s legacy remunerated "
        "increases to type='increase' + remunerated",
        cr.rowcount,
    )
