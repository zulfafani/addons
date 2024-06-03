from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import UserError


class IntegrationSalesOrder(models.Model):
    _inherit = 'sale.order'

    BATCH_SIZE = 100

    def sales_order_integration(self):
        data_sales_order = self.target_client.call_odoo('object', 'execute_kw', self.target_client.db, self.target_client.uid,
                                                 self.target_client.password, 'sale.order' , 'search_read', [[]],
                                                 {'fields': fields})