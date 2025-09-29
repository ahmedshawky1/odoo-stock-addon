{
    'name': 'Stock',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Stock Management',
    'author': 'Your Company',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/data.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}