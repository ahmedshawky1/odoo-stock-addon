# -*- coding: utf-8 -*-

from odoo import api, models
from datetime import datetime


class TradeBlotterReport(models.AbstractModel):
    _name = 'report.stock.trade_blotter_report'
    _description = 'Trade Blotter Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        # Get user and date range
        user = self.env['res.users'].browse(docids[0])
        date_from = data.get('date_from') if data else False
        date_to = data.get('date_to') if data else False
        
        # Build domain based on user role
        domain = []
        if user.has_group('stock.group_stock_investor'):
            # Investor sees their own trades
            domain.extend(['|', ('buyer_id', '=', user.id), ('seller_id', '=', user.id)])
        elif user.has_group('stock.group_stock_broker'):
            # Broker sees trades of their clients
            domain.extend(['|', 
                ('buy_order_id.broker_id', '=', user.id),
                ('sell_order_id.broker_id', '=', user.id)
            ])
        # Admin sees all trades (no additional domain)
        
        if date_from:
            domain.append(('trade_date', '>=', date_from))
        if date_to:
            domain.append(('trade_date', '<=', date_to))
        
        # Get trades
        trades = self.env['stock.trade'].search(domain, order='trade_date desc')
        
        # Calculate summary statistics
        total_trades = len(trades)
        total_volume = sum(trades.mapped('quantity'))
        total_value = sum(t.quantity * t.price for t in trades)
        
        # Group trades by date for daily summary
        daily_summary = {}
        for trade in trades:
            date = trade.trade_date.date()
            if date not in daily_summary:
                daily_summary[date] = {
                    'trades': 0,
                    'volume': 0,
                    'value': 0
                }
            daily_summary[date]['trades'] += 1
            daily_summary[date]['volume'] += trade.quantity
            daily_summary[date]['value'] += trade.quantity * trade.price
        
        return {
            'doc_ids': docids,
            'doc_model': 'res.users',
            'docs': user,
            'data': data,
            'trades': trades,
            'total_trades': total_trades,
            'total_volume': total_volume,
            'total_value': total_value,
            'daily_summary': daily_summary,
            'date_from': date_from,
            'date_to': date_to,
            'report_date': datetime.now(),
        } 