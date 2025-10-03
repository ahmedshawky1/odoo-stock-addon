# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import UserError, ValidationError, AccessError
from collections import OrderedDict
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
import logging

_logger = logging.getLogger(__name__)

class StockMarketPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        
        if 'order_count' in counters:
            values['order_count'] = request.env['stock.order'].search_count([
                ('user_id', '=', user.id)
            ]) if user.user_type == 'investor' else 0
        
        if 'position_count' in counters:
            values['position_count'] = request.env['stock.position'].search_count([
                ('user_id', '=', user.id)
            ]) if user.user_type == 'investor' else 0
        
        if 'trade_count' in counters:
            trade_domain = ['|', ('buyer_id', '=', user.id), ('seller_id', '=', user.id)]
            if user.user_type == 'broker':
                trade_domain = ['|', ('buy_broker_id', '=', user.id), ('sell_broker_id', '=', user.id)]
            values['trade_count'] = request.env['stock.trade'].search_count(trade_domain)
        
        if 'deposit_count' in counters:
            deposit_domain = [('user_id', '=', user.id)]
            if user.user_type == 'banker':
                deposit_domain = [('banker_id', '=', user.id)]
            values['deposit_count'] = request.env['stock.deposit'].search_count(deposit_domain)
        
        if 'loan_count' in counters:
            loan_domain = [('user_id', '=', user.id)]
            if user.user_type == 'banker':
                loan_domain = [('banker_id', '=', user.id)]
            values['loan_count'] = request.env['stock.loan'].search_count(loan_domain)
        
        return values

    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        """Redirect /my to /market to make it the main entry point"""
        return request.redirect('/market')

    # Portfolio View
    @http.route(['/my/portfolio', '/my/portfolio/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_portfolio(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        if user.user_type not in ['investor', 'banker']:
            return request.redirect('/my')
        
        Position = request.env['stock.position']
        domain = [('user_id', '=', user.id)]
        
        searchbar_sortings = {
            'security': {'label': _('Security'), 'order': 'security_id'},
            'value': {'label': _('Market Value'), 'order': 'market_value desc'},
            'pnl': {'label': _('P&L'), 'order': 'unrealized_pnl desc'},
        }
        
        if not sortby:
            sortby = 'value'
        order = searchbar_sortings[sortby]['order']
        
        # Position count
        position_count = Position.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/portfolio",
            url_args={'sortby': sortby},
            total=position_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content
        positions = Position.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'user': user,
            'positions': positions,
            'page_name': 'portfolio',
            'pager': pager,
            'default_url': '/my/portfolio',
            'sortby': sortby,
            'searchbar_sortings': searchbar_sortings,
        })
        
        return request.render("stock_market_simulation.portal_my_portfolio", values)

    # Orders View
    @http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        if user.user_type != 'investor':
            return request.redirect('/my')
        
        Order = request.env['stock.order']
        domain = [('user_id', '=', user.id)]
        
        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'order_date desc'},
            'name': {'label': _('Order Number'), 'order': 'name'},
            'status': {'label': _('Status'), 'order': 'status'},
        }
        
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'pending': {'label': _('Pending'), 'domain': [('status', '=', 'pending')]},
            'filled': {'label': _('Filled'), 'domain': [('status', '=', 'filled')]},
            'cancelled': {'label': _('Cancelled'), 'domain': [('status', '=', 'cancelled')]},
        }
        
        # Default values
        if not sortby:
            sortby = 'date'
        if not filterby:
            filterby = 'all'
        
        domain += searchbar_filters[filterby]['domain']
        
        # Date filter
        if date_begin and date_end:
            domain += [('order_date', '>', date_begin), ('order_date', '<=', date_end)]
        
        order = searchbar_sortings[sortby]['order']
        
        # Order count
        order_count = Order.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content
        orders = Order.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'user': user,
            'date': date_begin,
            'orders': orders,
            'page_name': 'order',
            'pager': pager,
            'default_url': '/my/orders',
            'sortby': sortby,
            'searchbar_sortings': searchbar_sortings,
            'filterby': filterby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
        })
        
        return request.render("stock_market_simulation.portal_my_orders", values)

    # Order Entry
    @http.route(['/my/order/new'], type='http', auth="user", website=True)
    def portal_order_new(self, **kw):
        """Order creation page - restricted to brokers only"""
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        # Only brokers can access order creation to place orders for clients
        if user.user_type == 'investor':
            values['error'] = "Investors cannot place orders directly. Please contact your broker to place orders on your behalf."
            return request.render("stock_market_simulation.portal_access_denied", values)
        elif user.user_type != 'broker':
            return request.redirect('/my')
        
        # Get active session
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
        if not active_session:
            values['error'] = "No active trading session"
            return request.render("stock_market_simulation.portal_order_new", values)
        
        # Get securities
        securities = request.env['stock.security'].sudo().search([('active', '=', True)])
        
        # Get broker's clients
        clients = request.env['res.users'].search([
            ('broker_id', '=', user.id),
            ('user_type', '=', 'investor')
        ])
        
        # Get positions for all clients (for sell orders)
        client_positions = request.env['stock.position'].search([
            ('user_id', 'in', clients.ids),
            ('available_quantity', '>', 0)
        ])
        
        values.update({
            'user': user,
            'securities': securities,
            'clients': clients,
            'client_positions': client_positions,
            'active_session': active_session,
            'display_currency': request.env.company.currency_id,
        })
        
        return request.render("stock_market_simulation.portal_order_new", values)

    @http.route(['/my/order/create'], type='json', auth="user", website=True)
    def portal_order_create(self, **kw):
        user = request.env.user
        
        # Allow brokers to place orders on behalf of clients
        if user.user_type == 'broker':
            client_id = kw.get('client_id')
            if not client_id:
                return {'error': 'Client must be selected'}
            
            client = request.env['res.users'].browse(int(client_id))
            if not client or client.broker_id.id != user.id:
                return {'error': 'Invalid client selected'}
            
            # Use client for order creation
            order_user = client
        elif user.user_type == 'investor':
            return {'error': 'Investors cannot place orders directly. Please contact your broker.'}
        else:
            return {'error': 'Unauthorized'}
        
        # Get active session
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
        if not active_session:
            return {'error': 'No active trading session'}
        
        try:
            # Create order on behalf of client
            order_vals = {
                'user_id': order_user.id,  # Client who owns the order
                'session_id': active_session.id,
                'security_id': int(kw.get('security_id')),
                'side': kw.get('side'),
                'order_type': kw.get('order_type'),
                'quantity': int(kw.get('quantity')),
                'price': float(kw.get('price', 0)),
            }
            
            # Additional validation with user-friendly messages
            security = request.env['stock.security'].browse(int(kw.get('security_id')))
            quantity = int(kw.get('quantity'))
            price = float(kw.get('price', 0))
            side = kw.get('side')
            
            # Check minimum order value
            if price * quantity < 100:  # Assuming min order value of $100
                return {'error': f'Order value (${price * quantity:.2f}) is below minimum required ($100.00)', 'type': 'validation'}
            
            # Check client cash balance for buy orders
            if side == 'buy':
                required_cash = price * quantity
                if order_user.cash_balance < required_cash:
                    return {'error': f'Client insufficient funds. Required: ${required_cash:,.2f}, Available: ${order_user.cash_balance:,.2f}', 'type': 'validation'}
            
            # Check client position for sell orders
            if side == 'sell':
                position = request.env['stock.position'].search([
                    ('user_id', '=', order_user.id),
                    ('security_id', '=', int(kw.get('security_id')))
                ], limit=1)
                
                if not position or position.available_quantity < quantity:
                    available = position.available_quantity if position else 0
                    return {'error': f'Client insufficient shares. Required: {quantity:,}, Available: {available:,}', 'type': 'validation'}
            
            # Create the order
            order = request.env['stock.order'].sudo().create(order_vals)
            
            # Log the broker action
            order.message_post(
                body=f"Order placed by broker {user.name} on behalf of client {order_user.name}",
                message_type='comment'
            )
            
            return {
                'success': True,
                'message': f'Order #{order.name} placed successfully for client {order_user.name}',
                'order_id': order.id
            }
            
        except Exception as e:
            return {'error': str(e)}

    # Market Data
    @http.route(['/market', '/market/home'], type='http', auth="user", website=True)
    def market_home(self, **kw):
        """Custom market portal entry point with custom layout"""
        user = request.env.user
        
        # Get active session
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
        
        # Get all active securities
        securities = request.env['stock.security'].sudo().search([('active', '=', True)])
        
        # Get market movers
        gainers = securities.filtered(lambda s: s.change_percentage > 0).sorted('change_percentage', reverse=True)[:5]
        losers = securities.filtered(lambda s: s.change_percentage < 0).sorted('change_percentage')[:5]
        
        # Financial data with fallbacks
        values = {
            'user': user,
            'user_type': user.user_type,
            'cash_balance': user.cash_balance or 0.0,
            'portfolio_value': user.portfolio_value or 0.0,
            'total_assets': user.total_assets or 0.0,
            'profit_loss': user.profit_loss or 0.0,
            'profit_loss_percentage': user.profit_loss_percentage or 0.0,
            'display_currency': request.env.company.currency_id,
            'active_session': active_session,
            'securities': securities,
            'top_gainers': gainers,
            'top_losers': losers,
            'page_name': 'market_home',
        }
        
        return request.render("stock_market_simulation.market_portal_layout", values)
    
    @http.route(['/market/portfolio'], type='http', auth="user", website=True)
    def market_portfolio(self, page=1, **kw):
        """Portfolio view in market portal"""
        user = request.env.user
        
        if user.user_type != 'investor':
            return request.redirect('/market')
        
        # Get positions
        positions = request.env['stock.position'].search([
            ('user_id', '=', user.id),
            ('quantity', '>', 0)
        ])
        
        values = {
            'user': user,
            'positions': positions,
            'cash_balance': user.cash_balance or 0.0,
            'portfolio_value': user.portfolio_value or 0.0,
            'total_assets': user.total_assets or 0.0,
            'display_currency': request.env.company.currency_id,
            'page_name': 'portfolio',
        }
        
        return request.render("stock_market_simulation.market_portfolio_view", values)
    
    @http.route(['/market/trading'], type='http', auth="user", website=True)
    def market_trading(self, **kw):
        """Trading view in market portal - for brokers to place orders on behalf of clients"""
        user = request.env.user
        
        # Only brokers can access trading interface to place orders for clients
        if user.user_type != 'broker':
            return request.redirect('/market')
        
        # Get active session
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
        
        if not active_session:
            return request.redirect('/market')
        
        # Get all active securities
        securities = request.env['stock.security'].sudo().search([('active', '=', True)])
        
        # Get broker's clients (investors assigned to this broker)
        clients = request.env['res.users'].search([
            ('broker_id', '=', user.id),
            ('user_type', '=', 'investor')
        ])
        
        # Get positions for all clients (for sell orders)
        client_positions = request.env['stock.position'].search([
            ('user_id', 'in', clients.ids),
            ('available_quantity', '>', 0)
        ])
        
        values = {
            'user': user,
            'securities': securities,
            'clients': clients,
            'client_positions': client_positions,
            'active_session': active_session,
            'display_currency': request.env.company.currency_id,
            'page_name': 'trading',
        }
        
        return request.render("stock_market_simulation.market_trading_view", values)
    
    @http.route(['/market/orders'], type='http', auth="user", website=True)
    def market_orders(self, **kw):
        """Orders view in market portal"""
        user = request.env.user
        
        if user.user_type != 'investor':
            return request.redirect('/market')
        
        # Get user orders
        orders = request.env['stock.order'].search([
            ('user_id', '=', user.id)
        ], order='create_date desc', limit=50)
        
        values = {
            'user': user,
            'orders': orders,
            'display_currency': request.env.company.currency_id,
            'page_name': 'orders',
        }
        
        return request.render("stock_market_simulation.market_orders_view", values)
    
    @http.route(['/my/market'], type='http', auth="user", website=True)
    def portal_market_data(self, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        # Get all active securities
        securities = request.env['stock.security'].sudo().search([('active', '=', True)])
        
        # Group by type
        grouped_securities = {}
        for k, g in groupbyelem(securities, itemgetter('security_type')):
            grouped_securities[k] = list(g)
        
        values.update({
            'user': user,
            'securities': securities,
            'grouped_securities': grouped_securities,
            'page_name': 'market',
        })
        
        return request.render("stock_market_simulation.portal_market_data", values)

    # Broker Commission Report
    @http.route(['/my/commissions'], type='http', auth="user", website=True)
    def portal_broker_commissions(self, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        if user.user_type != 'broker':
            return request.redirect('/my')
        
        # Get commission data
        trades = request.env['stock.trade'].search([
            '|', ('buy_broker_id', '=', user.id), ('sell_broker_id', '=', user.id)
        ])
        
        total_commission = sum(
            t.buy_commission if t.buy_broker_id == user else 0 +
            t.sell_commission if t.sell_broker_id == user else 0
            for t in trades
        )
        
        # Group by session
        session_commissions = {}
        for trade in trades:
            session = trade.session_id.name
            if session not in session_commissions:
                session_commissions[session] = 0
            
            if trade.buy_broker_id == user:
                session_commissions[session] += trade.buy_commission
            if trade.sell_broker_id == user:
                session_commissions[session] += trade.sell_commission
        
        values.update({
            'user': user,
            'total_commission': total_commission,
            'session_commissions': session_commissions,
            'recent_trades': trades[:20],
            'page_name': 'commission',
        })
        
        return request.render("stock_market_simulation.portal_broker_commissions", values)

    # API Endpoints for AJAX calls
    @http.route(['/api/market/quotes'], type='json', auth="user", methods=['POST'])
    def api_market_quotes(self, **kw):
        """Get real-time market quotes for specified securities"""
        try:
            symbol_list = kw.get('symbols', [])
            if not symbol_list:
                return {'success': False, 'error': 'No symbols provided'}
                
            securities = request.env['stock.security'].sudo().search([
                ('symbol', 'in', symbol_list),
                ('active', '=', True)
            ])
            
            quotes = []
            for security in securities:
                # Calculate change from session start
                price_change = security.current_price - security.session_start_price
                change_percentage = (price_change / security.session_start_price * 100) if security.session_start_price else 0
                
                quotes.append({
                    'symbol': security.symbol,
                    'name': security.name,
                    'current_price': security.current_price,
                    'session_start_price': security.session_start_price,
                    'price_change': price_change,
                    'change_percentage': round(change_percentage, 2),
                    'last_update': security.write_date.strftime('%H:%M:%S') if security.write_date else '',
                })
            
            return {'success': True, 'quotes': quotes}
            
        except Exception as e:
            _logger.error(f"Error in market quotes API: {str(e)}")
            return {'success': False, 'error': 'Failed to retrieve market data'}

    @http.route(['/api/portfolio/summary'], type='json', auth="user", methods=['POST'])  
    def api_portfolio_summary(self, **kw):
        """Get portfolio summary for current user"""
        try:
            user = request.env.user
            if user.user_type != 'investor':
                return {'success': False, 'error': 'Only investors can access portfolio data'}
                
            # Get positions
            positions = request.env['stock.position'].search([('user_id', '=', user.id)])
            
            portfolio_value = sum(pos.market_value for pos in positions)
            total_assets = user.cash_balance + portfolio_value
            profit_loss = total_assets - user.initial_capital
            profit_loss_percentage = (profit_loss / user.initial_capital * 100) if user.initial_capital else 0
            
            # Get recent orders
            recent_orders = request.env['stock.order'].search([
                ('user_id', '=', user.id)
            ], order='create_date desc', limit=5)
            
            orders_data = []
            for order in recent_orders:
                orders_data.append({
                    'name': order.name,
                    'symbol': order.security_id.symbol,
                    'side': order.side,
                    'quantity': order.quantity,
                    'price': order.price,
                    'status': order.status,
                    'create_date': order.create_date.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return {
                'success': True,
                'cash_balance': user.cash_balance,
                'portfolio_value': portfolio_value,
                'total_assets': total_assets,
                'profit_loss': profit_loss,
                'profit_loss_percentage': round(profit_loss_percentage, 2),
                'recent_orders': orders_data,
                'positions_count': len(positions)
            }
            
        except Exception as e:
            _logger.error(f"Error in portfolio summary API: {str(e)}")
            return {'success': False, 'error': 'Failed to retrieve portfolio data'}

    # Banker Dashboard
    @http.route(['/my/banking'], type='http', auth="user", website=True)
    def portal_banking_dashboard(self, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        if user.user_type != 'banker':
            return request.redirect('/my')
        
        # Get banking statistics
        deposits = request.env['stock.deposit'].search([('banker_id', '=', user.id)])
        loans = request.env['stock.loan'].search([('banker_id', '=', user.id)])
        
        total_deposits = sum(d.current_value for d in deposits.filtered(lambda d: d.status == 'active'))
        total_loans = sum(l.principal_outstanding for l in loans.filtered(lambda l: l.status == 'active'))
        
        values.update({
            'user': user,
            'total_deposits': total_deposits,
            'total_loans': total_loans,
            'active_deposits': deposits.filtered(lambda d: d.status == 'active'),
            'active_loans': loans.filtered(lambda l: l.status == 'active'),
            'page_name': 'banking',
        })
        
        return request.render("stock_market_simulation.portal_banking_dashboard", values) 