from odoo import http, _
from odoo.http import request
import logging
import json

_logger = logging.getLogger(__name__)

class Routes(http.Controller):
    
    @http.route('/get_routes', type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def get_routes(self, **kw):
        try:
            _logger.info('get_routes: Parameters - %s', kw)
            
            
            domain = [('active', 'in', [True, False])]
            
            routes = request.env['factures.salesperson.routes'].sudo().search(domain)
            
            data = {
                'routes': []
            }
            for route in routes:
                data['routes'].append({
                    'id': route.id,
                    'name': route.name,
                    'code': route.code,
                    'description': route.description,
                    'salesperson': route.salesperson_id.name,
                    'active': route.active
                })
                
            return request.make_response(json.dumps(data, ensure_ascii=False), headers=[('Content-Type', 'application/json')], status=200)
        except Exception as e:
            _logger.error('Error in get_routes: %s', str(e))
            return request.make_response(json.dumps({'error': 'Internal Server Error'}, ensure_ascii=False), headers=[('Content-Type', 'application/json')], status=500)
