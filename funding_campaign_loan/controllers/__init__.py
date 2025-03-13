# -*- coding: utf-8 -*-
from . import loan_request
from . import swagger_extension
from . import field_extension

# Hack para forzar registro del extensor
from odoo.addons.funding_campaign_loan.controllers.field_extension import extend_loan_fields
import logging
_logger = logging.getLogger(__name__)
_logger.info(f"Loan extender loaded: {extend_loan_fields.__name__}")