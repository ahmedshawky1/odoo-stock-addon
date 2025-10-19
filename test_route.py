    @http.route(['/test/user/fields'], type='http', auth="user", website=True)
    def test_user_fields(self, **kw):
        """Test route to check user computed fields"""
        user = request.env.user
        
        try:
            result = {
                'user_id': user.id,
                'user_type': user.user_type,
                'cash_balance': user.cash_balance,
                'portfolio_value': user.portfolio_value,
                'total_assets': user.total_assets,
                'profit_loss': user.profit_loss,
                'profit_loss_percentage': user.profit_loss_percentage,
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            import traceback
            return f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"