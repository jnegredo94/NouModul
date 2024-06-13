{
    "name": "Factures",
    "version": "1.0",
    "description": "Custom Andorsoft module",
    "category": "Sales",
    "application": True,
    'author': "Bernat Soldevila",
    "depends": [
        "sale",
        "account",
        "stock"
    ],
    "auto_install": False,
    "license": "LGPL-3",
    "data": [
        "security/ir.model.access.csv",

        "report/factures_salesperson_routes_partner_report.xml",
        "report/factures_delivery_routes_partner_report.xml",
        "report/factures_delivery_routes_product_report.xml",

        "views/factures_delivery_routes_generation_views.xml",
        "views/factures_salesperson_routes_views.xml",
        "views/factures_salesperson_history_views.xml",

        "wizard/factures_payment_generation_views.xml",
        "wizard/factures_delivery_routes_partial_delivery_views.xml",
        "wizard/factures_delivery_routes_selection_views.xml",
        "wizard/factures_salesperson_routes_selection_views.xml",
        "wizard/factures_invoice_confirmation_views.xml",
        "wizard/factures_quotations_selection_views.xml",
        "wizard/factures_invoice_temp_views.xml",

        "wizard/factures_discounts_search_views.xml",

        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views_inherited.xml",
        "views/factures_delivery_routes_views.xml",
        "views/res_users_views.xml",
        "views/account_journal_views_inherited.xml",
    ],
    


}
