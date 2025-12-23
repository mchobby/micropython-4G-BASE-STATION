# This script is designed to test the InAlarm component
# of the Gate-Control project
from machine import Pin
from inalarm import *
import time

STATE_TEXT = [ 'OFF', 'OBSERVATION', 'ALARM', 'IDLE' ]


# Configuration dictionnary
params = {}
params['in4-mode']=InAlarm.MODE_LOW # Activate alarm on Low Signal
params['in4-obs']=10 # Observation time = 10 seconds
params['in4-idle']=1 # 1 minute idle time
params['in4-irst']=1 # idle reset = False

print( "\x1b[2J\x1b[H" ) # Clear Screen
in4 = Pin(17, Pin.IN, Pin.PULL_UP) 
alarm = InAlarm(in4,params,'in4')
while True:
	alarm.update()
	# Go home
	print( "\x1b[H" ) # Go Home
	print( "in4 state     : %s" % in4.value() )
	print( "")
	print( "Current State : %11s" % STATE_TEXT[alarm._state] )
	if alarm.alarm_notif_once:
		print( "Alarm_once    : ALARM!")
		time.sleep(1) # give time to see the ALARM! message
	else:
		print( "Alarm_once    : ---   ")

	time.sleep_ms( 100 )