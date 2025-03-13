# -*- coding: utf-8 -*-
from . import subscription_request
from . import swagger_extension
from . import field_extension

# Hack para forzar registro del extensor
from odoo.addons.funding_campaign_cooperator.controllers.field_extension import extend_cooperator_fields
import logging
_logger = logging.getLogger(__name__)
_logger.info(f"Cooperative extender loaded: {extend_cooperator_fields.__name__}")
