import subprocess

TEST_FR = 'dynamic/console_test_fr_drv_ng.exe discover'

TEST_FR_CMD = {
    'discover': 'dynamic/console_test_fr_drv_ng.exe discover',
    
}


class DeviceDiscoverer:
    def discover_devices(self):
        devices = subprocess.Popen(TEST_FR_CMD['discover'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output, error = devices.communicate()
        if output:
            lines = output.decode().split('\r\n')
            lines = [line for line in lines if line]
            return lines
        else:
            return error.decode()


def main():
    discoverer = DeviceDiscoverer()
    devices = discoverer.discover_devices()
    print(devices)


if __name__ == "__main__":
    main()
