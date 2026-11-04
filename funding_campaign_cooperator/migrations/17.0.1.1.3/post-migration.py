# Copyright 2026 Som IT Cooperatiu SCCL
# Nicolás Ramos https://github.com/nicolasramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from lxml import etree

from odoo import SUPERUSER_ID, api
from odoo.modules.module import get_resource_path

_logger = logging.getLogger(__name__)

FIELDS = ("body_html", "subject", "email_from", "email_to")


def _inner_xml(element):
    """Raw inner content of a data-file field (keeps QWeb tags as-is)."""
    parts = [element.text or ""]
    for child in element:
        parts.append(etree.tostring(child, encoding="unicode"))
        parts.append(child.tail or "")
    return "".join(parts)


def migrate(cr, version):
    """Force the confirmation mail templates from the data file (OP #4536).

    The templates live in a ``noupdate="1"`` block, so neither a regular
    update nor ``convert_xml_import(..., noupdate=False)`` (the file's own
    flag wins, see ``odoo/tools/convert.py``) overwrite them. Read the new
    bodies straight from the data file and write them: unrendered ``{{ }}``,
    missing logo and any stale content get replaced in existing databases.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    path = get_resource_path(
        "funding_campaign_cooperator", "data", "mail_template_data.xml"
    )
    doc = etree.parse(path)
    updated = 0
    for record in doc.xpath("//record[@model='mail.template']"):
        template = env.ref(
            "funding_campaign_cooperator.%s" % record.get("id"),
            raise_if_not_found=False,
        )
        if not template:
            continue
        vals = {}
        for node in record.xpath("field"):
            if node.get("name") in FIELDS:
                vals[node.get("name")] = _inner_xml(node)
        if vals:
            template.sudo().write(vals)
            updated += 1
    _logger.info(
        "funding_campaign_cooperator: %d confirmation mail templates "
        "force-updated from data file",
        updated,
    )
