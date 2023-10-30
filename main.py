import subprocess
import json
import requests
import re
from tqdm import tqdm
import sys
import asyncio
import time
import threading
from colorama import init, Fore
from requests.exceptions import RequestException

init()


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

    def animated_loading(self):
        chars = ['      ',
                 '*     ',
                 '**    ',
                 '***   ',
                 ' ***  ',
                 '  *** ',
                 '   ***',
                 '    **',
                 '     *',
                 '      ',
                 '     *',
                 '    **',
                 '   ***',
                 '  *** ',
                 ' ***  ',
                 '***   ',
                 '**    ',
                 '*     ']
        while not self.stop_animation:
            for char in chars:
                sys.stdout.write(Fore.BLUE + f'\rПоиск оборудования {char}')
                sys.stdout.flush()
                time.sleep(0.1)

    async def discover(self):
        try:
            self.stop_animation = False
            animation_thread = threading.Thread(target=self.animated_loading)
            animation_thread.daemon = True
            animation_thread.start()
            devices = self.subprocess_popen('discover', None)
            output, error = devices.communicate()
            self.stop_animation = True

            if output:
                lines = output.decode().split('\r\n')
                lines = [line for line in lines if line]
                return lines
            else:
                print(Fore.RED + '\r\nОборудование не найдено. '
                      'Проверьте доступность портов. '
                      'Процесс прерван. Для выхода нажмите Enter...',
                      end='')
                input()
                exit()
        except KeyboardInterrupt:
            self.stop_animation = True
            print(Fore.YELLOW + '\r\nПроцесс прерван пользователем. '
                  'Для выхода нажмите Enter...', end='')
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


async def main():
    print(Fore.YELLOW + 'Для остановки нажмите сочетание Ctrl+C')
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

        devices = await search_device.discover()
        req_devices = []
        with tqdm(total=len(devices),
                  desc=Fore.WHITE + 'Опрос',
                  unit='device',
                  file=sys.stdout) as pbar:
            for device in devices:
                search_device.beep(device)
                pbar.set_description(f'Опрос {device}')
                pbar.refresh()
                fr_status_dict = search_device.read_statuses(
                    'status', device)
                fs_status_dict = search_device.read_statuses(
                    'fs-status', device)
                fs_exchange_dict = search_device.read_statuses(
                    'fs-exchange-status', device)
                fs_get_eol_dict = search_device.read_statuses(
                    'fs-get-eol', device)
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
                pbar.update(1)
                pbar.set_description(
                    f'Устройство {table_dict["serial"]} обработано')
                pbar.refresh()
                if table_dict['serial'] not in req_devices:
                    req_devices.append(table_dict['serial'])
                json_data = json.dumps(nested_dict, ensure_ascii=True)
                try:
                    requests.post('http://127.0.0.1:8000/fr-data/',
                                  data=json_data)
                except RequestException as e:
                    print(Fore.RED + '\r\nПроцесс прерван. '
                          f'\r\n{e} '
                          '\r\nДанные не отправлены на сервер. '
                          '\r\nДля выхода нажмите Enter...')
                    input()
                    exit()
        print(Fore.GREEN + 'Опрошенные устройства:')
        for req_device in req_devices:
            print(Fore.GREEN + f'     {req_device}')
        print(Fore.GREEN + 'Опрошенные интерфейсы:')
        for device in devices:
            print(Fore.GREEN + f'     {device}')
        print(Fore.GREEN + 'Процесс выполнен успешно. '
              'Данные отправлены на сервер. '
              'Для выхода нажмите Enter...')
        input()
        exit()

    except KeyboardInterrupt:
        print(Fore.YELLOW + 'Процесс прерван пользователем. '
              'Для выхода нажмите Enter...', end='')
        input()
        exit()


if __name__ == '__main__':
    asyncio.run(main())
