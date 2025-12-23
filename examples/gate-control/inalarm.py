# Input Alarm
#
import time

class InAlarm:
	""" Alarm detection on input for the for the 4G-Base-Station """
	MODE_HIGH = 'H'
	MODE_LOW = 'L'
	MODE_DISABLED = 'D' # Not in use

	STATE_OFF = 0 # Start/State
	STATE_OBS = 1 # Observation 
	STATE_ALARM = 2 # Alarm occured and must be acquired by callee
	STATE_IDLE  = 3 


	def __init__(self, pin, params, input_prefix ):
		""" pin : input pin to check 
			params : parameter dictionnary (eg: in1-mode, in1-obs, in1-idl, in1-rst 
			input_prefix : parameter prefix corresponding to the input (eg: in1)
		"""
		self.pin = pin
		self.last_pin_state = None
		self._state = InAlarm.STATE_OFF # State machine
		# Extract the parameter value to various variables
		# mode : which signal will trigger the alarm state
		# obs : observation time in sec
		# idl : idle detection time after alarm
		# rst : reset idle time when signal resets
		self.prefix = input_prefix 
		self.mode = InAlarm.MODE_HIGH 
		self.obs = 1 # sec
		self.idl = 2 # minutes
		self.rst = True
		self.init( params )


	def init( self, params ):
		# Initialize the various parameter form the dictionnary and RESETs all the states
		assert params['%s-mode'%self.prefix].upper() in (InAlarm.MODE_HIGH, InAlarm.MODE_LOW, InAlarm.MODE_DISABLED)
		assert type( params['%s-obs'%self.prefix]) is int
		assert type(params['%s-idle'%self.prefix]) is int
		assert type(params['%s-irst'%self.prefix]) is int

		self.mode = params['%s-mode'%self.prefix].upper()
		self.obs = int( params['%s-obs'%self.prefix] )
		self.idl = int( params['%s-idle'%self.prefix] )
		self.rst = int( params['%s-irst'%self.prefix] )>0

		# Re-initialise all internal state
		# self.last_pin_state = self.pin.value()
		self._state = InAlarm.STATE_OFF # State Machine
		self._alarm_notif = False # Alarm notification (for the callee)
		self._obs_start = time.ticks_ms() # Starting of OBSERVATION STATE
		self._idle_start = time.ticks_ms() # Starting of IDLE STATE


	def alarm_signal( self ):
		""" Check the Pin state and return True is it has the AlarmState """
		if not( self.mode in (InAlarm.MODE_HIGH, InAlarm.MODE_LOW, InAlarm.MODE_DISABLED) ):
			raise InAlarmError( 'Invalid Mode %s!' % self.mode )
		if self.mode==InAlarm.MODE_DISABLED:
			return False
		return self.pin.value()==(self.mode==InAlarm.MODE_HIGH)


	
	def update(self):
		""" Check state of the pin and manage the various internal states """
		if self.mode==InAlarm.MODE_DISABLED:
			return 

		if self._state==InAlarm.STATE_OFF:

			if self.alarm_signal(): # Having a signal alarm ?
				# Go to OBSERVATION state
				self._obs_start = time.ticks_ms()
				self._alarm_notif = False
				self._state = InAlarm.STATE_OBS
			return
			
		elif self._state==InAlarm.STATE_OBS:

			if self.alarm_signal() and ( time.ticks_diff(time.ticks_ms(),self._obs_start)>(self.obs*1000) ):
				# We do exceed the observation time 
				# => go to STATE_ALARM				
				self._state = InAlarm.STATE_ALARM
			elif not( self.alarm_signal() ):
				# back to OFF state
				self._state = InAlarm.STATE_OFF
			return

		elif self._state==InAlarm.STATE_ALARM:

			self._idle_start = time.ticks_ms()
			self._alarm_notif = True
			self._state = InAlarm.STATE_IDLE
			return

		elif self._state==InAlarm.STATE_IDLE:

			if self.rst and not(self.alarm_signal()):
				self._state = InAlarm.STATE_OFF
			if  time.ticks_diff(time.ticks_ms(),self._idle_start)>(self.idl*60*1000):
				self._state = InAlarm.STATE_OFF
			return

		else:
			raise InAlarmError( 'Invalid state %i detected' % self._state )
				


	@property
	def alarm_notif_once( self ):
		""" The alarm notification for the callee. 
			The notification is reset once read. """
		_v = self._alarm_notif
		if _v:
			self._alarm_notif=False
		return _v
