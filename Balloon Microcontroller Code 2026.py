# 2025 Flight Computer code
# for YSPA 2025 High-altitude balloon payload

# GPS modulus is on UART0, main serial bus, connected to RX on RP2040
# BME280 is on I2C1 bus, connected to SDA and SCL on the RP2040 (not STEMMA quick connector)
# 5g servo is connect to D4 on RP2040, intended to release balloon line at a specific altitude or after a certain time
# In order to write data to the onboard file system, pin A0 has to be grounded... this makes the file system writable for circuitpython (see boot.py)


import time
import board
import busio
#import digitalio
import adafruit_gps
#import adafruit_lis3dh
from adafruit_bme280 import basic as adafruit_bme280
import pwmio
from adafruit_motor import servo
import neopixel


pwm = pwmio.PWMOut(board.D4, duty_cycle=2 ** 15, frequency=50)
my_servo = servo.Servo(pwm)
uart0 = busio.UART(board.TX, board.RX, baudrate=9600, timeout = 1)
i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
gps = adafruit_gps.GPS(uart0, debug=False)
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.1

#line = ""
data = ""
bme280.sea_level_pressure = 1014 #double check this
dropaltitude = 23000 #30000. Also possibly use later in while loop?
droptime = (20*60) # If not dropped by this elapsed time, release anyway
dropped = False # Have we dropped the balloon? i.e., released the ser #
my_servo.angle = 180
maxaltitude = 0 #accumulates later, check
last_print = time.monotonic()
#fp = open('/datalog.txt', 'a')
while True:
    #Read the GPS output from UART0
    gps.update()


    current = time.monotonic() #whats the difference between last_print and current?? Don't understand the starting conditional -- SW
    if current - last_print >= 1.0: 
        data = str(current) + ',' + str(dropped) + ','

        # Read the BME280
        data += str(bme280.temperature)+','+str(bme280.humidity)+','+str(bme280.pressure)+','+str(bme280.altitude)+','
        if bme280.altitude > maxaltitude:
            maxaltitude = bme280.altitude

        if gps.has_fix: #what does have fix mean?? - SW
            data += str(gps.latitude) +','+ str(gps.longitude) + ',' + str(gps.altitude_m)
        else:
            data += 'nofix, nofix, nofix'


        last_print = current
        # write this data string to a file...
        print(data)

        #fp.write(data)
        #fp.flush()
        pixel.fill((0, 100, 0)) #why this? - SW
        time.sleep(0.1)
        pixel.fill((0,0,0))


        if bme280.altitude < (maxaltitude - 100) or time.monotonic() > droptime: #why not just drop altitude
            dropped = True
            my_servo.angle = 0

