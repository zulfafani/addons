from datetime import datetime, timedelta
import time


# kalau ada case store nya beda zona waktu gimana

class DataIntegrator:
    def __init__(self, source_client, target_client):
        self.source_client = source_client
        self.target_client = target_client

    def log_record_success(self, record, modul):
        gmt_7_now = datetime.now() - timedelta(hours=7)  # Odoo menggunakan UTC, belum diatur zona waktunya
        record_log = {
            'vit_doc_type': modul,
            'vit_trx_key': record.get('name'),
            'vit_trx_date': record.get('create_date'),
            'vit_sync_date': gmt_7_now.strftime('%Y-%m-%d %H:%M:%S'),
            'vit_sync_status': 'Success',
            'vit_sync_desc': f"Data yang masuk: {record}"}
        return record_log
    # perlukah record failed

    def log_runtime(self, start_time, end_time, duration, modul):
        gmt_7_start_time = datetime.fromtimestamp(start_time) - timedelta(hours=7)
        gmt_7_end_time = datetime.fromtimestamp(end_time) - timedelta(hours=7)
        runtime_log = {
            'vit_code_type': f"{modul}",
            'vit_start_sync': gmt_7_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'vit_end_sync': gmt_7_end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'vit_duration': f"{duration:.2f} minutes"}
        return runtime_log

    def transfer_data(self, model, fields, modul):
        # search_read all fields 0.09 minutes
        data_list = self.source_client.call_odoo('object', 'execute_kw', self.source_client.db, self.source_client.uid,
                                                 self.source_client.password, model, 'search_read', [[]],
                                                 {'fields': fields})

        # jika create_date dan write_date kemarin sampai hari ini

        for record in data_list:

            # terdapat pengecekan existing data, nama field nya mau apa
            param_existing = self.get_param_existing_data(modul)
            existing_data = self.get_existing_data(model, modul, param_existing)
            if not any(record.get(param_existing) == data.get(param_existing) for data in existing_data):
                start_time = time.time()
                valid_record = self.validate_record_data(record, model)     # untuk case data type many2many
                self.create_data(model, valid_record)
                end_time = time.time()
                duration = end_time - start_time

                self.create_log_note_odoo(record, modul)
                self.create_log_runtime_odoo(start_time, end_time, duration, modul) # masih ngelooping belum dikeluarin
            else:
                # kalau misalkan ada data, yang diupdate semua data apa difiter lagi pakai apa #apakah target client dikasih akses untuk create dan update master

                start_time = time.time()
                self.update_data(model, record)
                end_time = time.time()
                duration = end_time - start_time

            # except Exception as e:
            #     print(f"Error occurred while transferring record {record.get('name')}: {e}")

    def validate_record_data(self, record, model):
        try:
            # Retrieve model fields and their metadata
            type_fields = self.get_type_data_source(model)
            for field_name, field_value in record.items():
                if field_name in type_fields:
                    field_metadata = type_fields[field_name]
                    if field_metadata['type'] == 'many2one' and isinstance(field_value, list):
                        # For Many2one fields, extract ID from list
                        record[field_name] = field_value[0] if field_value else False
                    # Add more validation rules for other field types if needed
            return record
        except Exception as e:
            print(f"Error occurred while validating record data: {e}")
            return None


    def delete_data(self):
        try:
            filter_domain = [['vit_code_type', '=', 'Master']]
            data_logruntime = self.target_client.call_odoo('object', 'execute_kw', self.target_client.db,
                                                           self.target_client.uid, self.target_client.password,
                                                           'log.code.runtime', 'search_read', [filter_domain],
                                                           {'fields': ['id'], 'limit': 1})
            print("masuk function")
            for record in data_logruntime:
                record_id = record['id']
                self.target_client.call_odoo('object', 'execute_kw', self.target_client.db, self.target_client.uid,
                                             self.target_client.password, 'log.code.runtime', 'unlink', [[record_id]])
                print(f"Deleted record with ID: {record_id}")
        except Exception as e:
            print(f"Error occurred when delete data: {e}")

    def update_data(self, model, record):
        try:
            self.target_client.call_odoo('object', 'execute_kw', self.target_client.db, self.target_client.uid,
                                         self.target_client.password, model, 'write', [record])
        except Exception as e:
            print(f"Error occurred when update data: {e}")

    def create_data(self, model, record):
        try:
            self.target_client.call_odoo('object', 'execute_kw', self.target_client.db, self.target_client.uid,
                                         self.target_client.password, model, 'create', [record])
        except Exception as e:
            print(f"Error occurred when create data: {e}")

    def create_log_note_odoo(self, record, modul):
        try:
            log_record = self.log_record_success(record, modul)
            self.source_client.call_odoo('object', 'execute_kw', self.source_client.db, self.source_client.uid,
                                         self.source_client.password, 'log.note', 'create', [log_record])
            print(f"Data log note yang masuk: {log_record}")
        except Exception as e:
            print(f"Error occurred when create log note: {e}")

    def create_log_runtime_odoo(self, start_time, end_time, duration, modul):
        try:
            runtime_log = self.log_runtime(start_time, end_time, duration, modul)
            self.source_client.call_odoo('object', 'execute_kw', self.source_client.db, self.source_client.uid,
                                         self.source_client.password, 'log.code.runtime', 'create', [runtime_log])
            print(f"Data log runtime yang masuk: {runtime_log}")
        except Exception as e:
            print(f"Error occurred when create log runtime: {e}")

    def get_param_existing_data(self, modul):
        try:
            if modul == 'Master Customer':
                param_existing = 'customer_code'
            elif modul == 'Master Item':
                param_existing = 'default_code'
            elif modul == 'Master Item Group':
                param_existing = 'display_name'
            elif modul == 'Master Users':
                param_existing = 'login'
            elif modul == 'Master Location':
                param_existing = 'complete_name'
            elif modul == 'Master Pricelist Header':
                param_existing = 'name'
            else:
                param_existing = None
            return param_existing
        except Exception as e:
            print(f"Error occurred when get param existing data: {e}")
            return None

    def get_existing_data(self, model, modul, field_uniq):
        try:
            if modul == 'Master Customer':
                existing_data = self.target_client.call_odoo('object', 'execute_kw', self.target_client.db,
                                                   self.target_client.uid, self.target_client.password, model,
                                                   'search_read', [[]], {'fields': [field_uniq]})
            elif modul == 'Master Item':
                existing_data = self.target_client.call_odoo('object', 'execute_kw', self.target_client.db,
                                                   self.target_client.uid, self.target_client.password, model,
                                                   'search_read', [[]], {'fields': [field_uniq]})
            else:
                existing_data = None
            return existing_data
        except Exception as e:
            print(f"Error occurred when get existing data: {e}")
            return None

    def get_type_data_source(self, model):
        try:
            type_info = self.source_client.call_odoo('object', 'execute_kw', self.source_client.db,
                                                      self.source_client.uid, self.source_client.password,
                                                      model, 'fields_get', [], {'attributes': ['type']})
            return type_info
        except Exception as e:
            print(f"Error occurred while retrieving model fields: {e}")
            return {}

