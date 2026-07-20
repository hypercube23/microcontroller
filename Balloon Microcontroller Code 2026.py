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
droptime = (140*60) # CONFIRM: must be longer than the predicted climb to dropaltitude, or it fires first
dropped = False # Have we dropped the balloon? i.e., released the ser #
my_servo.angle = 180
maxaltitude = 0 #accumulates later, check
groundaltitude = None # pad elevation, set on the first GPS fix
launchtime = None # droptime counts from here, not from power-up
last_print = time.monotonic()
try:
    fp = open('/datalog.txt', 'a')
except OSError as e:
    fp = None
    print('LOG OPEN FAILED, is A0 grounded?:', e)
while True:
    try:
        #Read the GPS output from UART0
        gps.update()


        current = time.monotonic() #whats the difference between last_print and current?? Don't understand the starting conditional -- SW
        if current - last_print >= 1.0:
            data = str(current) + ',' + str(dropped) + ','

            # Read the BME280
            data += str(bme280.temperature)+','+str(bme280.humidity)+','+str(bme280.pressure)+','+str(bme280.altitude)+','

            if gps.has_fix: #what does have fix mean?? - SW
                data += str(gps.latitude) +','+ str(gps.longitude) + ',' + str(gps.altitude_m)
                # the BME280 is only spec'd to 300 hPa (~9 km), so altitude logic runs off GPS
                if gps.altitude_m > maxaltitude:
                    maxaltitude = gps.altitude_m
                if groundaltitude is None:
                    groundaltitude = gps.altitude_m
                if launchtime is None and gps.altitude_m > groundaltitude + 300:
                    launchtime = current
            else:
                data += 'nofix, nofix, nofix'


            last_print = current
            # write this data string to a file...
            print(data)

            if fp is not None:
                fp.write(data + '\n')
                fp.flush()
            pixel.fill((0, 100, 0)) #why this? - SW
            time.sleep(0.1)
            pixel.fill((0,0,0))


            if not dropped:
                if gps.has_fix and gps.altitude_m > dropaltitude:
                    dropped = True
                elif gps.has_fix and gps.altitude_m < (maxaltitude - 250):
                    dropped = True
                elif launchtime is not None and current - launchtime > droptime:
                    dropped = True
                if dropped:
                    my_servo.angle = 0

    except Exception as e: # one bad sensor read must not end the flight
        print('loop error:', e)
        time.sleep(0.5)

