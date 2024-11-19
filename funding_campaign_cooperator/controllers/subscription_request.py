# controllers/cooperator_voluntary_api.py

from odoo import http
from odoo.http import request
import json

class CooperatorVoluntaryApi(http.Controller):
    @http.route(
        "/api/subscription/campaign/create",
        type="json",
        auth="none",
        csrf=False,
    )
    def create_subscription(self, **kw):
        try:
            db = request.httprequest.headers.get('X-Odoo-Db')
            username = request.httprequest.headers.get('X-Odoo-Username')
            api_key = request.httprequest.headers.get('X-Odoo-Api-Key')

            if not all([db, username, api_key]):
                return {'error': 'Missing authentication parameters', 'status': 'error'}

            uid = request.session.authenticate(db, username, api_key)
            if not uid:
                return {'error': 'Authentication failed', 'status': 'error'}

            # Validar y crear subscription
            required_fields = [
                "partner_id",
                "ordered_parts",
                "share_product_id",
                "source",
                "type",
                "campaign_id",
            ]

            for field in required_fields:
                if field not in kw:
                    return {
                        "error": f"Missing required field: {field}",
                        "status": "error"
                    }

            subscription = request.env['subscription.request'].create(kw)

            return {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "status": "success",
                    "data": {
                        "id": subscription.id,
                        "state": subscription.state
                    }
                }
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": 200,
                    "message": str(e),
                    "data": {"status": "error"}
                }
            }
