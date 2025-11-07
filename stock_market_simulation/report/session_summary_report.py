# -*- coding: utf-8 -*-

from odoo import api, models
from collections import defaultdict


class SessionSummaryReport(models.AbstractModel):
    _name = 'report.stock.session_summary_report'
    _description = 'Trading Session Summary Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        session = self.env['stock.session'].browse(docids[0])
        
        # Get all trades in session
        trades = session.trade_ids
        
        # Get all orders in session
        orders = session.order_ids
        
        # Calculate session metrics
        total_trades = len(trades)
        total_volume = sum(trades.mapped('quantity'))
        total_value = sum(t.quantity * t.price for t in trades)
        
        # Calculate order statistics
        submitted_orders = orders.filtered(lambda o: o.status != 'draft')
        filled_orders = orders.filtered(lambda o: o.status == 'filled')
        cancelled_orders = orders.filtered(lambda o: o.status == 'cancelled')
        
        fill_rate = (len(filled_orders) / len(submitted_orders) * 100) if submitted_orders else 0
        
        # Group trades by security
        security_summary = defaultdict(lambda: {
            'trades': 0,
            'volume': 0,
            'value': 0,
            'high': 0,
            'low': float('inf'),
            'open': 0,
            'close': 0
        })
        
        for trade in trades.sorted('trade_date'):
            security = trade.security_id
            summary = security_summary[security]
            
            summary['trades'] += 1
            summary['volume'] += trade.quantity
            summary['value'] += trade.quantity * trade.price
            
            if trade.price > summary['high']:
                summary['high'] = trade.price
            if trade.price < summary['low']:
                summary['low'] = trade.price
            
            if summary['open'] == 0:
                summary['open'] = trade.price
            summary['close'] = trade.price
        
        # Calculate top traders by volume
        trader_volumes = defaultdict(float)
        for trade in trades:
            trader_volumes[trade.buyer_id] += trade.quantity * trade.price
            trader_volumes[trade.seller_id] += trade.quantity * trade.price
        
        top_traders = sorted(
            trader_volumes.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            'doc_ids': docids,
            'doc_model': 'stock.session',
            'docs': session,
            'data': data,
            'total_trades': total_trades,
            'total_volume': total_volume,
            'total_value': total_value,
            'submitted_orders': len(submitted_orders),
            'filled_orders': len(filled_orders),
            'cancelled_orders': len(cancelled_orders),
            'fill_rate': fill_rate,
            'security_summary': dict(security_summary),
            'top_traders': top_traders,
        } 