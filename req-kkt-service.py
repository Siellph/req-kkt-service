import subprocess
import json
import requests
import re


class InteractDevice:

    def subprocess_popen(self, command, url):
        if url:
            return subprocess.Popen('dynamic/console_test_fr_drv_ng.exe '
                                    + command + ' -a '
                                    + ' "' + url + '" '
                                    + ' -p 30',
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        else:
            return subprocess.Popen('dynamic/console_test_fr_drv_ng.exe '
                                    + command,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

    def discover(self):
        devices = self.subprocess_popen('discover', None)
        output, _ = devices.communicate()
        if output:
            lines = output.decode().split('\r\n')
            lines = [line for line in lines if line]
            return lines
        else:
            exit()

    def read_statuses(self, command, url):
        status = self.subprocess_popen(command, url)
        output, _ = status.communicate()
        if output:
            lines = output.decode().split('\r\n')
            lines = [line for line in lines if line]
            parsed_output = {}
            for line in lines:
                key, value = line.split('\t')
                new_key = key.strip().replace(' ', '_').lower()
                new_key = re.sub(r'[0-9]+\._', '', new_key)
                new_key = re.sub(
                    r'[0-9]+_', '', new_key).replace(
                        '(', '_').replace(
                            '__', '_').replace(
                                ')', '').replace(
                                    '%', '_percent')
                parsed_output[new_key] = value
            return parsed_output
        else:
            exit()

    def read_tables(self, command, url):
        read = self.subprocess_popen(command, url)
        output, _ = read.communicate()
        if output:
            lines = output.decode().replace('\r\n', '').strip()
            return lines
        else:
            exit()

    def beep(self, url):
        self.subprocess_popen('beep', url).communicate()


def main():
    search_device = InteractDevice()

    fields = {
        'serial': '18.1.1',
        'inn': '18.1.2',
        'rnm': '18.1.3',
        'factory_num_fs': '18.1.4',
        'tax': '18.1.5',
        'work_mode': '18.1.6',
        'user': '18.1.7',
        'operator': '18.1.8',
        'address': '18.1.9',
        'ofd': '18.1.10',
        'url_ofd': '18.1.11',
        'inn_ofd': '18.1.12',
        'url_tax': '18.1.13',
        'place': '18.1.14',
        'email': '18.1.15',
    }

    # devices = ['tcp://192.168.137.111:7778?timeout=15000&protocol=v1',
    #            'serial://COM3?timeout=15000&baudrate=115200&protocol=v1']
    devices = search_device.discover()
    protocol_dict = {}
    n = 1
    for line in devices:
        protocol_dict[f'protocol_{n}'] = line
        n += 1
    for device in devices:
        search_device.beep(device)

        fr_status_dict = search_device.read_statuses('status', device)
        fs_status_dict = search_device.read_statuses('fs-status', device)
        fs_exchange_dict = search_device.read_statuses('fs-exchange-status',
                                                       device)
        fs_get_eol = search_device.read_statuses('fs-get-eol', device)

        table_dict = {}
        for key, value in fields.items():
            field = search_device.read_tables(f'read {value}', device)
            table_dict[key] = field

        nested_dict = {
            'serial': table_dict['serial'],
            'connection_methods': protocol_dict,
            'status_fr': fr_status_dict,
            'status_fs': fs_status_dict,
            'status_exchange_fs': fs_exchange_dict,
            'eol_fs': fs_get_eol,
            'table_18': table_dict
        }

        json_data = json.dumps(nested_dict, ensure_ascii=True)
        response = requests.post(
            'http://127.0.0.1:8000/fr-data', data=json_data)
        print(response.text)


main()
