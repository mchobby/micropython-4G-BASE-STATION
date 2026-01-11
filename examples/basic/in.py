""" in.py - test the input only of the 4G-Base-Station """
import time
from station import BaseStation

base = BaseStation()

print( "in1\tin2\tin3\tin4\trun_app")
print( "-"*40 )
while True:
	base.led.toggle()

	print( "%s\t%s\t%s\t%s\t%s" % (base.in1.value(),base.in2.value(),base.in3.value(),base.in4.value(),base.run_app))
	time.sleep(0.5)
