from onl.platform.base import *
from onl.platform.accton import *

# Platform Config Version: 2.2.0-kernel6.1
# Last Modified: 2025-11-14
# Changes: Use modprobe for i2c-ismt following PR #1018 pattern to fix timing issue.
#          Root cause: self.insmod() with try/except silently failed on first boot.
#          iSMT is bus 55 (confirmed on both Debian 9 and Debian 12 with kernel 6.1).

class OnlPlatform_x86_64_accton_as5712_54x_r0(OnlPlatformAccton,
                                              OnlPlatformPortConfig_48x10_6x40):

    PLATFORM='x86-64-accton-as5712-54x-r0'
    MODEL="AS5712-54X"
    SYS_OBJECT_ID=".5712.54"
    CONFIG_VERSION="2.2.0-kernel6.1-20251114"

    def baseconfig(self):
        # Load i2c-ismt module FIRST using modprobe (following PR #1018 pattern)
        # This must happen before any other module loading to ensure iSMT adapter
        # is available when platform devices are initialized
        os.system("modprobe i2c-ismt")

        # Bind ismt_smbus driver to PCI device to create I2C adapter
        os.system("echo 0000:00:13.0 > /sys/bus/pci/drivers/ismt_smbus/bind 2>/dev/null || true")

        # Find which bus is iSMT (Debian 9: bus 55, Debian 12: bus 1)
        import time
        import glob
        ismt_bus = None
        for attempt in range(50):  # Wait up to 5 seconds
            for name_file in glob.glob('/sys/bus/i2c/devices/i2c-*/name'):
                try:
                    with open(name_file) as f:
                        if 'iSMT' in f.read():
                            ismt_bus = int(name_file.split('/')[-2].split('-')[1])
                            break
                except:
                    pass
            if ismt_bus is not None:
                break
            time.sleep(0.1)

        if ismt_bus is None:
            raise RuntimeError("iSMT I2C adapter not found after modprobe and bind")

        # Load modules, ignoring errors if already loaded
        try:
            self.insmod('optoe')
        except:
            pass
        try:
            self.insmod('cpr_4011_4mxx')
        except:
            pass
        try:
            self.insmod("ym2651y")
        except:
            pass
        for m in [ 'cpld', 'fan', 'psu', 'leds' ]:
            try:
                self.insmod("x86-64-accton-as5712-54x-%s.ko" % m)
            except:
                pass

        ########### initialize I2C bus 0 ###########
        # initialize CPLDs
        self.new_i2c_devices(
            [
                ('as5712_54x_cpld1', 0x60, 0),
                ('as5712_54x_cpld2', 0x61, 0),
                ('as5712_54x_cpld3', 0x62, 0),
                ]
            )
        # initialize SFP devices (kernel 6.1: CPLD mux starts at bus 1, not 2)
        for port in range(1, 49):
            self.new_i2c_device('optoe2', 0x50, port)
            subprocess.call('echo port%d > /sys/bus/i2c/devices/%d-0050/port_name' % (port, port), shell=True)

        # Initialize QSFP devices (kernel 6.1: buses shifted down by 1)
        self.new_i2c_device('optoe1', 0x50, 49)
        self.new_i2c_device('optoe1', 0x50, 50)
        self.new_i2c_device('optoe1', 0x50, 51)
        self.new_i2c_device('optoe1', 0x50, 52)
        self.new_i2c_device('optoe1', 0x50, 53)
        self.new_i2c_device('optoe1', 0x50, 54)
        subprocess.call('echo port49 > /sys/bus/i2c/devices/49-0050/port_name', shell=True)
        subprocess.call('echo port52 > /sys/bus/i2c/devices/50-0050/port_name', shell=True)
        subprocess.call('echo port50 > /sys/bus/i2c/devices/51-0050/port_name', shell=True)
        subprocess.call('echo port53 > /sys/bus/i2c/devices/52-0050/port_name', shell=True)
        subprocess.call('echo port51 > /sys/bus/i2c/devices/53-0050/port_name', shell=True)
        subprocess.call('echo port54 > /sys/bus/i2c/devices/54-0050/port_name', shell=True)

        ########### initialize iSMT I2C bus (bus 55 in kernel 6.1) ###########
        # Note: iSMT adapter is bus 55 (confirmed on both Debian 9 and 12 with kernel 6.1)
        # CPLD mux on bus 0 creates channels buses 1-54
        # pca9548 mux on bus 55 creates channels buses 56-63
        # i2c-ismt module loaded at start of baseconfig() using modprobe

        self.new_i2c_devices(
            [
                # initiate multiplexer (PCA9548) on iSMT bus (Debian 9: 55, Debian 12: 1)
                ('pca9548', 0x70, ismt_bus),

                # initiate PSU-1 AC Power (on pca9548 mux channels)
                ('as5712_54x_psu1', 0x38, ismt_bus+1),
                ('cpr_4011_4mxx',  0x3c, ismt_bus+1),
                ('as5712_54x_psu1', 0x50, ismt_bus+1),
                ('ym2401',  0x58, ismt_bus+1),

                # initiate PSU-2 AC Power (on pca9548 mux channels)
                ('as5712_54x_psu2', 0x3b, ismt_bus+2),
                ('cpr_4011_4mxx',  0x3f, ismt_bus+2),
                ('as5712_54x_psu2', 0x53, ismt_bus+2),
                ('ym2401',  0x5b, ismt_bus+2),

                # initiate lm75 (on pca9548 mux channels)
                ('lm75', 0x48, ismt_bus+5),
                ('lm75', 0x49, ismt_bus+6),
                ('lm75', 0x4a, ismt_bus+7),

                # System EEPROM on iSMT bus
                ('24c02', 0x57, ismt_bus),
                ]
            )

        return True
