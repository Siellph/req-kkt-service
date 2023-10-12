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
        print('Поиск оборудования...')
        devices = self.subprocess_popen('discover', None)
        output, error = devices.communicate()
        if output:
            lines = output.decode().split('\r\n')
            lines = [line for line in lines if line]
            return lines
        else:
            print(error)
            print('Оборудование не найдено. Проверьте доступность портов.')
            print('Процесс прерван. Для выхода нажмите Enter')
            input()
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
    print('Для остановки нажмите сочетание Ctrl+C')
    try:
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

        devices = search_device.discover()
        for device in devices:
            search_device.beep(device)
            print('Чтение статуса ФР...')
            fr_status_dict = search_device.read_statuses('status', device)
            print('Чтение статуса ФН...')
            fs_status_dict = search_device.read_statuses('fs-status', device)
            print('Чтение статуса обмена ОФД...')
            fs_exchange_dict = search_device.read_statuses(
                'fs-exchange-status', device)
            print('Чтение срока жизни ФН...')
            fs_get_eol_dict = search_device.read_statuses('fs-get-eol', device)

            table_dict = {}
            for key, value in fields.items():
                field = search_device.read_tables(f'read {value}', device)
                table_dict[key] = field

            nested_dict = {
                'serial': table_dict['serial'],
                'status_fr': fr_status_dict,
                'status_fs': fs_status_dict,
                'status_exchange_fs': fs_exchange_dict,
                'eol_fs': fs_get_eol_dict,
                'table': table_dict
            }
            print('Отправка полученной информации на сервер...')
            json_data = json.dumps(nested_dict, ensure_ascii=True)
            requests.post('http://127.0.0.1:8000/fr-data/', data=json_data)
        print('=====================================================')
        print('Процесс выполнен успешно. Для выхода нажмите Enter...')
        print('=====================================================')
        input()
    except KeyboardInterrupt:
        print('Процесс прерван пользователем. Нажмите Enter для выхода.')
        input()
        exit()


if __name__ == '__main__':
    main()
