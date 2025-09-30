# -*- coding: utf-8 -*-

from odoo import api, models, fields
from datetime import datetime


class BankerPortfolioReport(models.AbstractModel):
    _name = 'report.stock.banker_portfolio_report'
    _description = 'Banker Portfolio Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        banker = self.env['res.users'].browse(docids[0])
        
        # Get all deposits managed by banker
        deposits = self.env['stock.deposit'].search([
            ('banker_id', '=', banker.id),
            ('status', 'in', ['active', 'pending'])
        ])
        
        # Get all loans managed by banker
        loans = self.env['stock.loan'].search([
            ('banker_id', '=', banker.id),
            ('status', 'in', ['active', 'pending'])
        ])
        
        # Calculate totals
        total_deposits = sum(deposits.mapped('current_value'))
        total_loans = sum(loans.mapped('principal_outstanding'))
        total_interest_earned = sum(deposits.mapped('interest_earned'))
        total_interest_to_pay = sum(loans.mapped('total_interest'))
        
        # Group deposits by type
        deposit_summary = {
            'savings': deposits.filtered(lambda d: d.deposit_type == 'savings'),
            'fixed': deposits.filtered(lambda d: d.deposit_type == 'fixed'),
            'recurring': deposits.filtered(lambda d: d.deposit_type == 'recurring'),
        }
        
        # Group loans by type
        loan_summary = {
            'personal': loans.filtered(lambda l: l.loan_type == 'personal'),
            'secured': loans.filtered(lambda l: l.loan_type == 'secured'),
            'margin': loans.filtered(lambda l: l.loan_type == 'margin'),
        }
        
        # Calculate risk metrics
        overdue_loans = loans.filtered(lambda l: l.next_payment_date and l.next_payment_date < fields.Date.today())
        defaulted_loans = loans.filtered(lambda l: l.status == 'defaulted')
        
        return {
            'doc_ids': docids,
            'doc_model': 'res.users',
            'docs': banker,
            'data': data,
            'deposits': deposits,
            'loans': loans,
            'total_deposits': total_deposits,
            'total_loans': total_loans,
            'total_interest_earned': total_interest_earned,
            'total_interest_to_pay': total_interest_to_pay,
            'net_interest_margin': total_interest_to_pay - total_interest_earned,
            'deposit_summary': deposit_summary,
            'loan_summary': loan_summary,
            'overdue_loans': overdue_loans,
            'defaulted_loans': defaulted_loans,
            'report_date': datetime.now(),
        } 