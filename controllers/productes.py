from datetime import timedelta
from odoo import http, _
from odoo.http import request
from odoo import _, api, fields, models
import logging
import json

_logger = logging.getLogger(__name__)

class Productes(http.Controller):
    @http.route('/get_products',type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def get_products(self, **kw):
        _logger.info('get_products')
        category_id = kw.get('category_id', False)
        max_price = kw.get('max_price', False)
        keyword = kw.get('keyword', False)
        id = kw.get('id', False)
        page = kw.get('page', 1)        
        limit = kw.get('limit', 10)# to get all products, set limit to -1
        company_id = kw.get('company_id', False)
        if limit == -1:
            limit = 1000000
        offset = ((int(page) - 1) * int(limit))
        if offset <= 0:
            offset = 1
        
        domain = []
        if category_id:
            domain.append(('categ_id', '=', category_id))
        if max_price:
            domain.append(('list_price', '<=', max_price))
        if keyword:
            domain.append(('name', 'ilike', keyword))
        if id:
            domain.append(('id', '=', id))
            
            
        
        products = request.env['product.product'].sudo().search(domain, offset=offset, limit=limit)
        if company_id:
            products = products.filtered(lambda p: p.company_id.id == int(company_id))
        data = {
            'domain': domain,
            'products': []
            
        }
        for product in products:
            data['products'].append({
                'id': product.id,
                'name': product.name,
                'price': product.list_price,
                'code' : product.default_code,
                'qty_packaging': product.packaging_ids[0].qty if product.packaging_ids else 1,
                'product_packaging_id': product.packaging_ids[0].id if product.packaging_ids else '',
                'product_packaging_name': product.packaging_ids[0].name if product.packaging_ids else '',
                #string fields
                'product_company_id': str(product.company_id.id)
            })
            
        return request.make_response(json.dumps(data, ensure_ascii=False), headers=[('Content-Type', 'application/json')])
    
    
    #Get the products that a customer has bought in the last x months
    @http.route('/get_products_bought',type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def get_products_bought(self, **kw):
        _logger.info('get_products_bought')
        client_id = kw.get('client_id', False)
        months = kw.get('months', 6)
        
        if not client_id:
            return request.make_response(json.dumps({'error': 'client_id is required'}, ensure_ascii=False), headers=[('Content-Type', 'application/json')], status=400)
        
        domain = [
            ('order_id.partner_id.id', '=', client_id),            
            # ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', fields.Datetime.now() - timedelta(days=30*int(months)))
        ]


        lines = request.env['sale.order.line'].sudo().search(domain)
        data = {
            'products': []
        }
        for line in lines:
            data['products'].append({
                'id': line.product_id.id,
                'name': line.product_id.name,
                'price': line.price_unit,
                'date_order': line.order_id.date_order.strftime('%d/%m/%Y %H:%M:%S'),
                'code' : line.product_id.default_code
                
            })
            
        return request.make_response(json.dumps(data, ensure_ascii=False), headers=[('Content-Type', 'application/json')])
    
   