import subprocess
import json


class InteractDevice:

    def subprocess_popen(self, command, url):
        if url:
            return subprocess.Popen('console_test_fr_drv_ng.exe '
                                    + command + ' -a '
                                    + ' "' + url + '" '
                                    + ' -p 30',
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        else:
            return subprocess.Popen('console_test_fr_drv_ng.exe '
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
                parsed_output[key] = value
            return parsed_output
        else:
            exit()

    def read_tables(self, command, url):
        read = self.subprocess_popen(command, url)
        output, _ = read.communicate()
        if output:
            lines = output.decode().split('\r\n')
            lines = [line for line in lines if line]
            return lines[0]
        else:
            exit()

    def beep(self, url):
        self.subprocess_popen('beep', url).communicate()


def main():
    search_device = InteractDevice()

    devices = ['tcp://192.168.137.111:7778?timeout=15000&protocol=v1',
               'serial://COM3?timeout=15000&baudrate=115200&protocol=v1']
    # devices = search_device.discover()
    protocol_dict = {}
    n = 1
    for line in devices:
        protocol_dict[f'Protocol {n}'] = line
        n += 1

    # search_device.beep(devices[0])

    status_dict = search_device.read_statuses('status', devices[0])
    fs_status_dict = search_device.read_statuses('fs-status', devices[0])
    fs_exchange_dict = search_device.read_statuses('fs-exchange-status',
                                                   devices[0])
    fs_get_eol = search_device.read_statuses('fs-get-eol', devices[0])

    fields = {
        '1. Заводской номер ККТ:': '18.1.1',
        '2. ИНН:': '18.1.2',
        '3. РНМ:': '18.1.3',
        '4. Заодской номер ФН:': '18.1.4',
        '5. Система налогооблажения:': '18.1.5',
        '6. Режим работы:': '18.1.6',
        '7. Пользователь:': '18.1.7',
        '8. Оператор:': '18.1.8',
        '9. Адрес:': '18.1.9',
        '10. ОФД:': '18.1.10',
        '11. URL ОФД:': '18.1.11',
        '12. ИНН ОФД:': '18.1.12',
        '13. URL налоговой:': '18.1.13',
        '14. Место расчетов:': '18.1.14',
        '15. Email отправителя:': '18.1.15',
    }
    table_dict = {}
    for key, value in fields.items():
        field = search_device.read_tables(f'read {value}', devices[0])
        table_dict[key] = field

    nested_dict = {
        "Способы подключения": protocol_dict,
        "Статус ККТ": status_dict,
        "Статус ФН": fs_status_dict,
        "Статус передачи ФД в ОФД": fs_exchange_dict,
        "Срок действия ФН": fs_get_eol,
        "Таблица 18": table_dict
    }

    json_data = json.dumps(nested_dict, ensure_ascii=False)
    print(json_data)


if __name__ == "__main__":
    main()
