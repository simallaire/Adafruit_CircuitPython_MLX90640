import time
import adafruit_mlx90640
import hid
import busio

from adafruit_blinka.microcontroller.mcp2221.mcp2221 import mcp2221 as _mcp2221
from adafruit_blinka.microcontroller.mcp2221.mcp2221 import MCP2221 as _MCP2221
from adafruit_blinka.microcontroller.mcp2221.i2c import I2C as _MCP2221I2C

PRINT_TEMPERATURES = False
PRINT_ASCIIART = True


class MCP2221(_MCP2221): 
    def __init__(self, address):
        self._hid = hid.device()
        self._hid.open_path(address)
        print("Connected to "+str(address))
        self._gp_config = [0x07] * 4  # "don't care" initial value
        for pin in range(4):
            self.gp_set_mode(pin, self.GP_GPIO)  # set to GPIO mode
            self.gpio_set_direction(pin, 1)  # set to INPUT


class MCP2221I2C(_MCP2221I2C):
    def __init__(self, mcp2221, *, frequency=800000):
        self._mcp2221 = mcp2221
        self._mcp2221.i2c_configure(frequency)


class I2C(busioI2C):
    def __init__(self, mcp2221_i2c, *, frequency=800000):
        self._i2c = mcp2221_i2c


addresses = [mcp["path"] for mcp in hid.enumerate(0x04D8, 0x00DD)]


mlx_cameras = []
mlx_cameras.append(adafruit_mlx90640.MLX90640(I2C(MCP2221I2C(_mcp2221))))

for addr in addresses:
    try:
        mlx_camera = adafruit_mlx90640.MLX90640(I2C(MCP2221I2C(MCP2221(addr))))
        mlx_cameras.append(mlx_camera)
    except OSError:
        print("Device path: " +str(addr)+ "is used")


for mlx in mlx_cameras:
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

frame = [0] * 768
while True:
    for mlx in mlx_cameras:
        stamp = time.monotonic()
        try:
            mlx.getFrame(frame)
        except ValueError:
            # these happen, no biggie - retry
            continue
        print("Read 2 frames in %0.2f s" % (time.monotonic() - stamp))
        for h in range(24):
            for w in range(32):
                t = frame[h * 32 + w]
                if PRINT_TEMPERATURES:
                    print("%0.1f, " % t, end="")
                if PRINT_ASCIIART:
                    c = "&"
                    # pylint: disable=multiple-statements
                    if t < 20:
                        c = " "
                    elif t < 23:
                        c = "."
                    elif t < 25:
                        c = "-"
                    elif t < 27:
                        c = "*"
                    elif t < 29:
                        c = "+"
                    elif t < 31:
                        c = "x"
                    elif t < 33:
                        c = "%"
                    elif t < 35:
                        c = "#"
                    elif t < 37:
                        c = "X"
                    # pylint: enable=multiple-statements
                    print(c, end="")
            print()
        print()
