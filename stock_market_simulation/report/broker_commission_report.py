# -*- coding: utf-8 -*-

from odoo import api, models
from datetime import datetime, timedelta


class BrokerCommissionReport(models.AbstractModel):
    _name = 'report.stock.broker_commission_report'
    _description = 'Broker Commission Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        broker = self.env['res.users'].browse(docids[0])
        
        # Get date range from data or default to last month
        date_from = data.get('date_from') if data else (datetime.now() - timedelta(days=30)).date()
        date_to = data.get('date_to') if data else datetime.now().date()
        
        # Get all trades for broker's clients
        trades = self.env['stock.trade'].search([
            ('buy_order_id.broker_id', '=', broker.id),
            ('trade_date', '>=', date_from),
            ('trade_date', '<=', date_to)
        ])
        
        # Calculate commissions by client
        client_commissions = {}
        total_commission = 0.0
        total_volume = 0.0
        
        for trade in trades:
            client = trade.buyer_id
            if client.id not in client_commissions:
                client_commissions[client.id] = {
                    'client': client,
                    'trades': [],
                    'total_volume': 0.0,
                    'total_commission': 0.0
                }
            
            trade_value = trade.quantity * trade.price
            commission = trade_value * (trade.commission_rate / 100)
            
            client_commissions[client.id]['trades'].append(trade)
            client_commissions[client.id]['total_volume'] += trade_value
            client_commissions[client.id]['total_commission'] += commission
            
            total_volume += trade_value
            total_commission += commission
        
        return {
            'doc_ids': docids,
            'doc_model': 'res.users',
            'docs': broker,
            'data': data,
            'date_from': date_from,
            'date_to': date_to,
            'client_commissions': list(client_commissions.values()),
            'total_commission': total_commission,
            'total_volume': total_volume,
            'commission_rate': broker.broker_commission_rate,
        } 