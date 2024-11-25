from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
import logging
import traceback

_logger = logging.getLogger(__name__)

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
                _logger.warning("Missing authentication parameters.")
                return {'error': 'Missing authentication parameters', 'status': 'error'}

            request.session.db = db

            _logger.info(f"Searching user: {username}")
            user = request.env['res.users'].sudo().search([('login', '=', username)], limit=1)

            if not user:
                _logger.warning(f"User not found: {username}")
                return {'error': 'User not found', 'status': 'error'}

            try:
                user.ensure_one()
            except ValueError:
                _logger.error(f"Multiple users found with login: {username}")
                return {'error': 'Multiple users found with same login', 'status': 'error'}

            _logger.info(f"User found: {user.name}")

            try:
                temp_env = request.env(user=user.id)
                temp_env.user._check_credentials(api_key, {'interactive': False})
                _logger.info(f"Authentication successful for user: {user.name}")
            except AccessDenied:
                _logger.warning(f"Authentication failed for user: {username}")
                return {'error': 'Authentication failed', 'status': 'error'}

            request.env = temp_env

            required_fields = [
                "partner_id",
                "ordered_parts",
                "share_product_id",
                "source",
                "type",
                "campaign_id",
                "country_id",
                "firstname",
                "lastname",
                "email",
                "address",
                "city",
                "zip_code",
                "phone",
                "lang",
            ]

            for field in required_fields:
                if field not in kw:
                    _logger.warning(f"Missing required field: {field}")
                    return {'error': f'Missing required field: {field}', 'status': 'error'}

            data = {field: kw[field] for field in required_fields}

            subscription = request.env['subscription.request'].create(data)

            _logger.info(f"Subscription created with ID: {subscription.id}")

            return {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "status": "success",
                    "data": {
                        "id": subscription.id,
                        "name": subscription.name,
                        "state": subscription.state,
                    }
                }
            }

        except Exception as e:
            _logger.error('Unexpected error: %s', traceback.format_exc())
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": 200,
                    "message": str(e),
                    "data": {"status": "error"}
                }
            }
