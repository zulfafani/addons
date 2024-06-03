from config import Config
from odoo_client import OdooClient
from data_integrator import DataIntegrator
from decouple import config as get_config


def main():
    file_path = r'C:\odoo\server\addons\integrasi_odoo_pos\controllers\config.json'
    key = get_config('key').encode()
    config = Config(file_path, key)

    instance1 = config.get_instance('odoo_db1')
    instance2 = config.get_instance('odoo_db2')
    # sql_db_config = config.get_instance('sql_db')

    decrypted_password1 = config.decrypt_password(instance1['password'])
    decrypted_password2 = config.decrypt_password(instance2['password'])
    # decrypted_sql_password = config.decrypt_password(sql_db_config['password'])

    odoo_client1 = OdooClient(instance1['url'], instance1['db'], instance1['username'], decrypted_password1)
    odoo_client2 = OdooClient(instance2['url'], instance2['db'], instance2['username'], decrypted_password2)

    integrator = DataIntegrator(odoo_client1, odoo_client2)
    # integrator.delete_data()
    # integrator.transfer_data('res.partner', ['id','name', 'street', 'street2', 'phone', 'mobile', 'email', 'website','title','customer_rank', 'supplier_rank', 'write_uid', 'create_date', 'write_date'], 'Master Customer')
    integrator.transfer_data('product.category', ['id', 'name', 'parent_id', 'property_valuation', 'write_uid', 'create_date', 'write_date'], 'Master Item Group')  # 'property_account_income_categ_id', 'product_account_expense_categ_id', 'property_cost_method', not exist
    integrator.transfer_data('product.template', ['id', 'name', 'sale_ok', 'purchase_ok', 'detailed_type', 'invoice_policy', 'uom_id', 'uom_po_id', 'list_price', 'standard_price', 'taxes_id', 'categ_id',  'default_code', 'write_uid', 'create_date', 'write_date'], 'Master Item')
    # integrator.transfer_data('res.users', ['id', 'login', 'write_uid', 'create_date', 'write_date'], 'Master Users')
    # integrator.transfer_data('stock.location', ['id', name, location_id, usage, company_id, scrap_location, return_location, replenish_location, 'write_uid', 'create_date', 'write_date'], 'Master Location')
    # integrator.transfer_data('product.pricelist', ['id', 'name', 'currency_id', 'write_uid', 'create_date', 'write_date'], Master Pricelist Header) #perlu menambah lines/ detail
    # integrator.transfer_data('product.pricelist.item', ['id', min_quantity, date_start, date_end, 'write_uid', 'create_date', 'write_date'], Master Pricelist Detail) #perlu menambah lines/ detail name, price not exist

    # sql_db = SQLDatabase(sql_db_config['server'], sql_db_config['port'], sql_db_config['database'], sql_db_config['user'], decrypted_sql_password)
    # query_result = sql_db.execute_query('SELECT * FROM your_table')
    # print(query_result)


if __name__ == '__main__':
    main()