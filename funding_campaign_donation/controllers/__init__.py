# -*- coding: utf-8 -*-
from . import donation_request
from . import field_extension
from . import swagger_extension

# Hack para forzar registro del extensor
from odoo.addons.funding_campaign_donation.controllers.field_extension import extend_donation_fields
import logging
_logger = logging.getLogger(__name__)
_logger.info(f"Donation extender loaded: {extend_donation_fields.__name__}")