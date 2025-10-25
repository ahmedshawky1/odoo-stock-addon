#!/bin/bash

echo "=== EMAIL VERIFICATION TEST ==="

# Check if any users or partners have missing emails
echo "Checking email status in database..."

sudo docker exec -it odoo_stock odoo shell -d stock << 'EOF'
# Check users without emails
users_no_email = env['res.users'].search([('email', '=', False)])
users_empty_email = env['res.users'].search([('email', '=', '')])
print(f"Users without email: {len(users_no_email)}")
print(f"Users with empty email: {len(users_empty_email)}")

# Check partners without emails
partners_no_email = env['res.partner'].search([('email', '=', False)])
partners_empty_email = env['res.partner'].search([('email', '=', '')])
print(f"Partners without email: {len(partners_no_email)}")
print(f"Partners with empty email: {len(partners_empty_email)}")

# Show sample of emails
sample_users = env['res.users'].search([], limit=5)
print("\nSample user emails:")
for user in sample_users:
    print(f"  {user.login}: {user.email}")

sample_partners = env['res.partner'].search([('is_company', '=', False)], limit=5)
print("\nSample partner emails:")
for partner in sample_partners:
    print(f"  {partner.name}: {partner.email}")

exit()
EOF

echo "=== Email verification complete ==="