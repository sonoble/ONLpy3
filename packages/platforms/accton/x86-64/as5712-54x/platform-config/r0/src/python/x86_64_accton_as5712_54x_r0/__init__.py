from onl.platform.base import *
from onl.platform.accton import *

# Platform Config Version: 2.1.0-kernel6.1
# Last Modified: 2025-01-08
# Changes: Fixed ismt_smbus vs i2c-ismt driver conflict, iSMT is bus 1, CPLD mux is buses 2-55, pca9548 mux creates buses 56-63

class OnlPlatform_x86_64_accton_as5712_54x_r0(OnlPlatformAccton,
                                              OnlPlatformPortConfig_48x10_6x40):

    PLATFORM='x86-64-accton-as5712-54x-r0'
    MODEL="AS5712-54X"
    SYS_OBJECT_ID=".5712.54"
    CONFIG_VERSION="2.1.0-kernel6.1-20250108"

    def baseconfig(self):

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
        # Note: In kernel 6.1, CPLD mux channels use buses 2-54,
        # After loading i2c-ismt and binding driver, iSMT adapter becomes bus 55

        # Load i2c-ismt module (provides ismt_smbus driver)
        try:
            self.insmod("i2c-ismt")
        except:
            pass

        # Bind ismt_smbus driver to PCI device 0000:00:13.0 to create I2C adapter
        os.system("echo 0000:00:13.0 > /sys/bus/pci/drivers/ismt_smbus/bind 2>/dev/null || true")

        # Wait for bus 55 to be created
        import time
        for i in range(50):  # Wait up to 5 seconds
            if os.path.exists('/sys/bus/i2c/devices/i2c-55'):
                break
            time.sleep(0.1)

        self.new_i2c_devices(
            [
                # initiate multiplexer (PCA9548) on iSMT bus 55
                ('pca9548', 0x70, 55),

                # initiate PSU-1 AC Power (on pca9548 mux channels 56-63)
                ('as5712_54x_psu1', 0x38, 56),
                ('cpr_4011_4mxx',  0x3c, 56),
                ('as5712_54x_psu1', 0x50, 56),
                ('ym2401',  0x58, 56),

                # initiate PSU-2 AC Power (on pca9548 mux channels 56-63)
                ('as5712_54x_psu2', 0x3b, 57),
                ('cpr_4011_4mxx',  0x3f, 57),
                ('as5712_54x_psu2', 0x53, 57),
                ('ym2401',  0x5b, 57),

                # initiate lm75 (on pca9548 mux channels 56-63)
                ('lm75', 0x48, 60),
                ('lm75', 0x49, 61),
                ('lm75', 0x4a, 62),

                # System EEPROM on iSMT bus 55
                ('24c02', 0x57, 55),
                ]
            )

        return True
