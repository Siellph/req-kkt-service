import subprocess


class DeviceDiscoverer:

    TEST_FR_CMD = {
        'discover': 'dynamic/console_test_fr_drv_ng.exe discover',
        'beep': 'dynamic/console_test_fr_drv_ng.exe beep'
    }

    def discover_devices(self):
        devices = subprocess.Popen(self.TEST_FR_CMD['discover'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output, error = devices.communicate()
        if output:
            lines = output.decode().split('\r\n')
            lines = [line for line in lines if line]
            return lines
        else:
            return error.decode()

    def beep(self, url):
        subprocess.Popen(self.TEST_FR_CMD['beep'] + ' -a ' + url + ' p 30',
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        return


def main():
    discoverer = DeviceDiscoverer()
    devices = discoverer.discover_devices()
    discoverer.beep(devices[0])
    discoverer.beep(devices[1])
    print(devices)


if __name__ == "__main__":
    main()
