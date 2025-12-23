# Gate-control - boot.py
#
from machine import Pin
run_app = Pin( 13, Pin.IN, Pin.PULL_UP )
if run_app.value()==False: # Stop position 
	print( 'RUN_APP = Stop' )
	in4 = Pin( 17, Pin.IN, Pin.PULL_DOWN )
	in3 = Pin( 16, Pin.IN, Pin.PULL_UP )
	# in4 = True AND in3 = False ==> Reset configuration
	if (in4.value()==True) and (in3.value()==False):
		import os
		import ostls
		import  time
		print( 'Reset configuration' )
		if ostls.file_exists( 'config.dat' ):
			os.remove('config.dat')
		led = Pin( 25, Pin.OUT, value=1 )
		time.sleep(2)
		led.value(0)
else:
	print( 'RUN_APP = Run' )