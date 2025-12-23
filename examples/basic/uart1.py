""" uart1.py - create the 4G-Base-Station UART instance 

The UART1 is available on the UEXT connectors
The UART0 is available on the RPi GPIO connectors """

import time
from station import BaseStation

base = BaseStation()

# UART available UEXT 
#   first call can init the UART with extra params
uart1 = base.uart1( bits=8, parity=None, stop=1, baudrate=9600 )

# UART available on RPi GPIO
#   first call can init the UART with extra params
#   This one will be used by the 4G Modem
uart0 = base.uart0( baudrate=115200 ) # 8N1 is the default config


# Use the standard MicroPython UART primitive with uart1 or uart0