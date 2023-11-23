import subprocess
import json
import requests
import re
import sys
import threading
import asyncio
import time
from colorama import init, Fore
from requests.exceptions import RequestException
from tqdm import tqdm
from datetime import datetime
import win32com.client
import socket

init()


class InteractDevice:

    def __init__(self, url_server, headers):
        self.URL_SERVER = url_server
        self.HEADERS = headers
        self.stop_animation = False

    def subprocess_popen(self, command, url):
        if url:
            return subprocess.Popen(
                ('dynamic/console_test_fr_drv_ng.exe '
                 f'{command} -a "{url}" -p 30'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            return subprocess.Popen(
                f'dynamic/console_test_fr_drv_ng.exe {command}',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def animated_loading(self):
        chars = ['      ', '*     ', '**    ', '***   ', ' ***  ', '  *** ',
                 '   ***', '    **', '     *', '      ', '     *', '    **',
                 '   ***', '  *** ', ' ***  ', '***   ', '**    ', '*     ']

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
                      'Процесс прерван.')
                sys.exit()

        except KeyboardInterrupt:
            self.stop_animation = True
            print(Fore.YELLOW + '\r\nПроцесс прерван пользователем.')
            sys.exit()

    def read_statuses(self, command, url, serial):
        status = self.subprocess_popen(command, url)
        output, _ = status.communicate()

        if output:
            lines = output.decode().split('\r\n')
            lines = [line for line in lines if line]
            parsed_output = {'serial': serial}

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

                if new_key == 'eol_date':
                    parsed_output[new_key] = str(datetime.strptime(
                        value,
                        '%d.%m.%Y').date())
                if new_key == 'first_document_date_and_time':
                    parsed_output[new_key] = str(datetime.strptime(
                        value,
                        '%d.%m.%Y %H:%M'))
                if new_key == 'fn_date_and_time':
                    parsed_output[new_key] = str(datetime.strptime(
                        value,
                        '%d.%m.%Y %H:%M'))
                if new_key == 'ecr_date':
                    parsed_output[new_key] = str(datetime.strptime(
                        value,
                        '%d.%m.%Y').date())
                if new_key == 'ecr_time':
                    parsed_output[new_key] = str(datetime.strptime(
                        value,
                        '%H:%M:%S').time())
                if new_key == 'firmware_date':
                    parsed_output[new_key] = str(datetime.strptime(
                        value,
                        '%d.%m.%Y').date())

            json_data = json.dumps(parsed_output, ensure_ascii=True)
            print(json_data)

            try:
                requests.post(f'{self.URL_SERVER}/{command}/',
                              data=json_data, headers=self.HEADERS)
            except RequestException:
                print(Fore.RED + '\r\nПроцесс прерван.')
                sys.exit()

    def read_tables(self, command, url):
        read = self.subprocess_popen(command, url)
        output, _ = read.communicate()

        if output:
            lines = output.decode().replace('\r\n', '').strip()
            return lines
        else:
            sys.exit()

    def beep(self, url):
        self.subprocess_popen('beep', url).communicate()

    def send_to_serv(self, url, data):
        json_data = json.dumps(data, ensure_ascii=True)
        try:
            requests.post(f'{self.URL_SERVER}/{url}/',
                          data=json_data, headers=self.HEADERS)
        except RequestException:
            print(Fore.RED + '\r\nПроцесс прерван.')
            sys.exit()


async def main():
    ecr_mode_dict = {
        1: 'Выдача данных',
        5: 'Блокировка по неправильному паролю налогового инспектора',
        6: 'Ожидание подтверждения ввода даты',
        7: 'Разрешение изменения положения десятичной точки',
        8: 'Открытый документ',
        9: 'Режим разрешения технологического обнуления',
        10: 'Тестовый прогон',
        11: 'Печать полного фискального отчета',
        12: 'Печать длинного отчета ЭКЛЗ',
        13: 'Работа с фискальным подкладным документом',
        14: 'Печать подкладного документа',
        15: 'Фискальный подкладной документ сформирован'
    }
    computer_name = socket.gethostname()
    print(f'Имя компьютера: {computer_name}')
    fr = win32com.client.Dispatch('AddIn.DrvFR')
    fr.AdminUnlockPorts()
    fr.Beep()
    fr.Password = 30
    fr.ComputerName = computer_name
    fr.GetECRStatus()
    if fr.ECRMode in [0, 2, 3, 4]:
        if fr.Connected:
            print('ККТ подключена к драйверу')
            print('Отключаем ККТ от драйвера')
            fr.Disconnect()
            print(f'ФР подключен к драйверу: {fr.Connected}')
        if fr.PortLocked:
            print('Порт заблокирован драйвером')
            print('Снимаем блокировку портов')
            fr.AdminUnlockPorts()
            print(f'Порт разблокирован: {fr.PortLocked}')
    else:
        print(f'Режим ККТ: {fr.ECRMode}, {ecr_mode_dict[fr.ECRMode]}')
        print('ККТ занята')
        sys.exit()
    url_server = 'http://178.161.130.230:15693'
    headers = {
        'accept': 'application/json',
        'X-API-Key': 'f6289205-9391-4da6-9250-3aaf0bfab3f8',
        'Content-Type': 'application/json'
    }

    print(Fore.YELLOW + 'Для остановки нажмите сочетание Ctrl+C')

    try:
        search_device = InteractDevice(url_server, headers)
        fields = {
            "serial": "18.1.1",
            "inn": "18.1.2",
            "rnm": "18.1.3",
            "factory_num_fs": "18.1.4",
            "tax": "18.1.5",
            "work_mode": "18.1.6",
            "user": "18.1.7",
            "operator": "18.1.8",
            "address": "18.1.9",
            "ofd": "18.1.10",
            "url_ofd": "18.1.11",
            "inn_ofd": "18.1.12",
            "url_tax": "18.1.13",
            "place": "18.1.14",
            "email": "18.1.15",
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
                table_dict = {}

                for key, value in fields.items():
                    field = search_device.read_tables(f'read {value}', device)
                    table_dict[key] = field

                print(table_dict)

                search_device.send_to_serv('table-18', table_dict)
                serial = table_dict['serial']
                commands = ('status', 'fs-status', 'fs-exchange-status',
                            'fs-get-eol', 'model', 'short-status',
                            'mc-exchange-status')

                for command in commands:
                    search_device.read_statuses(command, device, serial)

                pbar.update(1)
                pbar.set_description(f'Устройство {table_dict["serial"]} '
                                     'обработано')
                pbar.refresh()

                if table_dict['serial'] not in req_devices:
                    req_devices.append(table_dict['serial'])

        print(Fore.GREEN + 'Опрошенные устройства:')
        for req_device in req_devices:
            print(Fore.GREEN + f'     {req_device}')
        print(Fore.GREEN + 'Опрошенные интерфейсы:')
        for device in devices:
            print(Fore.GREEN + f'     {device}')

        print('Установка связи ККТ - Драйвер')
        fr.Connect()
        print(f'ФР подключен к драйверу: {fr.Connected}')
        print(f'Порт заблокирован: {fr.PortLocked}')

        print(Fore.GREEN + 'Процесс выполнен успешно. '
              'Данные отправлены на сервер.')
        sys.exit()

    except KeyboardInterrupt:
        print(Fore.YELLOW + 'Процесс прерван пользователем.')
        sys.exit()


if __name__ == '__main__':
    asyncio.run(main())
