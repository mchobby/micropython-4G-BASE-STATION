""" i2c_bme.py - create the 4G-Base-Station I2C bus instance 

Use the bus to collect the data from a BME280 sensor """

import time
from station import BaseStation
# See  https://github.com/mchobby/esp8266-upy/tree/master/bme280-bmp280
from bme280 import BME280

base = BaseStation()

# I2C bus available Qwiic & UEXT 
#   first call can init the bus with extra params
i2c = base.i2c( freq=100_000 )

# Use the standard MicroPython I2C primitive with i2c

print( 'I2C Scan:', i2c.scan() )
bme = BME280( i2c=i2c, address=119 )

base.led.on()
while True:
	print( bme.raw_values )
	time.sleep(1)
