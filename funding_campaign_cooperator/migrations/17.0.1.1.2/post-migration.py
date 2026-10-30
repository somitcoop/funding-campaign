# Copyright 2026 Som IT Cooperatiu SCCL
# Nicolás Ramos https://github.com/nicolasramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api
from odoo.modules.module import get_resource_path
from odoo.tools.convert import convert_xml_import

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Force the confirmation mail templates from the data file (OP #4536).

    The templates live in a ``noupdate="1"`` block, so a regular module
    update never overwrote the stale version stored in existing databases
    (mixed ``{{ }}``/``t-`` syntax shown unrendered, no logo). Re-import
    the data file in update mode to align staging and production with the
    repository version, including the company logo header.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    path = get_resource_path(
        "funding_campaign_cooperator", "data", "mail_template_data.xml"
    )
    convert_xml_import(
        env,
        "funding_campaign_cooperator",
        path,
        idref={},
        mode="update",
        noupdate=False,
    )
    _logger.info(
        "funding_campaign_cooperator: confirmation mail templates "
        "force-updated from data file"
    )
