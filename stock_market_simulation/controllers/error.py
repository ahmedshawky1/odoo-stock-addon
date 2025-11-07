# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class StockErrorController(http.Controller):
    """Stock market portal error handling controller"""

    @http.route('/market/error/403', type='http', auth='public', website=True, sitemap=False)
    def stock_error_403(self, **kwargs):
        """Enhanced 403 error page for stock market portal"""
        return self._render_stock_error(403, 'Access Denied', 
                                       'You do not have permission to access this stock market content.')

    @http.route('/market/error/404', type='http', auth='public', website=True, sitemap=False)
    def stock_error_404(self, **kwargs):
        """Enhanced 404 error page for stock market portal"""
        return self._render_stock_error(404, 'Page Not Found', 
                                       'The stock market page you are looking for does not exist.')

    @http.route('/market/error/500', type='http', auth='public', website=True, sitemap=False)
    def stock_error_500(self, **kwargs):
        """Enhanced 500 error page for stock market portal"""
        return self._render_stock_error(500, 'Server Error', 
                                       'An unexpected error occurred while processing your request.')

    def _render_stock_error(self, status_code, status_message, description):
        """Common error page renderer"""
        values = {}
        
        # Get some active sessions to suggest (only for 404/403)
        if status_code in [404, 403]:
            try:
                suggested_sessions = request.env['stock.session'].sudo().search([
                    ('state', 'in', ['active', 'planned']),
                ], order='start_date desc', limit=6)
            except:
                suggested_sessions = []
            
            # Get some popular securities
            try:
                popular_securities = request.env['stock.security'].sudo().search([
                    ('active', '=', True),
                ], order='name', limit=6)
            except:
                popular_securities = []
                
            values.update({
                'suggested_sessions': suggested_sessions,
                'popular_securities': popular_securities,
            })
        
        values.update({
            'status_code': status_code,
            'status_message': status_message,
            'description': description,
            'page_title': f'{status_code} - {status_message}',
            'show_suggestions': status_code in [404, 403],
        })
        
        return request.render('stock_market_simulation.stock_error_page', values, status=status_code)