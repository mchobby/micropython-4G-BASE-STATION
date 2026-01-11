# Gate Control Application  class
#
# === Rules ===========================
# Master ALWAYS HAVE ALL RIGHTS!
# Admins can receive Notification, can modify configuration, can possibly ADD_USER (upon right)
# Users can only call to activate OUT1, can send a SMS for o
#
# Calls activates the IN1
# SMS with "OUT2" (see out2-cmd param) will activate OUT2. Notice that user must have CAN_OUT2 right
#
# See project https://github.com/mchobby/micropython-4G-BASE-STATION
#
from machine import UART, Pin, idle
from sim76xx import *
from sim76xx.sms import SMS
from sim76xx.voice import Voice, STATE_DISCONNECT
from ledtls import SuperLed
from station import *
from timetls import TimeoutTimer
import time

DONE_STR   = 'Done'
ERROR_STR  = 'ERROR!'
DENIED_STR = 'Denied!'

__version__ = '0.1.0'

class HandlerError( Exception ):
	""" Error raise while executing an handler """
	pass

def valid_text( s ):
	for ch in s:
		if not( (48<= ord(ch) <= 90) or (97<= ord(ch) <=122) or (ch in '!#+ -.')):
			return False
	return True

class SmsControlApp:
	def __init__( self ):		
		self.base = BaseStation()
		# Activate IN3 & IN4
		self.base.in3.value()
		self.base.in4.value()

		self.led = SuperLed( self.base.led )
		self.picoled = Pin( 25, Pin.OUT, False )

		self.pwr = Pin( Pin.board.GP26, Pin.OUT, value=False )
		self.uart = UART( 0, tx=Pin.board.GP0, rx=Pin.board.GP1, baudrate=115200, bits=8, parity=None, stop=1, timeout=500)
		self.sim = SIM76XX( uart=self.uart, pwr_pin=self.pwr, uart_training=True,  ) # use a SIM without pincode

		self.notif_lst = [] # List SMS notifications to performs. List of tuple ( Phone_nr to notify, msg_str or @value_label, about_phone_nr or None )
		self.sms_handlers = [] # Register shortcode and handler to execute for configuration SMS

	def power_up( self ):
		print("Connecting mobile network")
		self.led.on()
		self.sim.power_up() # May takes time

		try:
			self.led.pulse(500) # Pluse 500ms while connecting the mobile network
			timeout = TimeoutTimer(timeout=1.0)
			while not self.sim.is_registered:
				# update LED while waiting next test
				timeout.setTimer(1.0)
				while not timeout.expired:
					self.led.update()
					idle()
			print("connected!")
			self.picoled.on()
			self.led.off()
		except Exception as err:
			print( '%r' % err )
			self.led.error( error_count=2 )
			while True:
				self.led.update()
				idle()

	def register_message( self, notif_for, msg, source_nr=None):
		""" Register SMS message in notif_lst .  The main loop will send them one by one.
		    notif_for : With + prefix, it is a single phone number. 
		    msg : the messahe to send. With a @ prefix, it extract the label from the configuration
		    source_nr : None or the phone_nr that raized the notification (useful when notifying someone else). """
		self.notif_lst.append( (notif_for, msg, source_nr) )


	def register_sms_handler( self, shortcode, handler_fn ):
		self.sms_handlers.append( (shortcode.upper(), handler_fn) )

	def run_sms_handler( self, msg ):
		""" msg is Message object containing information about the incoming SMS """
		# check the message format
		try:
			_val = msg.message.split(',')
			if not( 1<=len(_val)<=3 ):
				raise Exception( "invalid %i count of parameters" % len(_val) )
			code = _val[0].upper()
			param1=None
			if len(_val)>1:
				param1 = _val[1].strip()
			param2=None
			if len(_val)>2:
				param2= _val[2].strip()

			if not( 1<=len(code)<=41 ):
				raise Exception( "Invalid %s code length!" % code )
			if (param1!=None) and len(param1)>20:
				raise Exception( "Invalid param1 length!" )
			if (param2!=None) and (len(param2)>30):
				raise Exception( "Invalid param2 length!" )			

		except Exception as err:
			print("Fail to decode message %s from %s" % (msg.message,msg.phone) )
			print("\t%r" % err )
			self.register_message( notif_for=msg.phone, msg='Invalid format!' ) # Send deny
		

		match = False
		for shortcode, handler in self.sms_handlers:
			if shortcode==code:
				try:
					match = True
					handler( msg, [param1,param2] )
					self.register_message( notif_for=msg.phone, msg='Done' ) # Send execution message
				except HandlerError as err:
					print("HandlerError for message %s from %s" % (msg.message,msg.phone) )
					print("\t%r" % err )					
					self.register_message( notif_for=msg.phone, msg='%s'%err )  # SMS Control also send error detail
				except Exception as err:
					print("Fail to execute message %s from %s" % (msg.message,msg.phone) )
					print("\t%r" % err )
					self.register_message( notif_for=msg.phone, msg=ERROR_STR ) # Send error notification
					self.register_message( notif_for=msg.phone, msg='%r'%err )  # SMS Control also send error detail
				break;
		if not( match ):
			self.register_message( notif_for=msg.phone, msg=ERROR_STR ) # Notify of error
		

	# --- Common Method ---

	def is_phone_nr( self, value ):
		""" Check if the value looks to be a phone bumber """
		return len(value)>2 and (value[0]=='+') and (value[1:].isdigit())

	def is_auth( self, phone_nr ):
		""" Implement it in descendant to restrict to specific phone """
		return True

	def update( self ):
		# Updates performed by the loop
		self.led.update()
		self.sim.update()


	def _loop( self ):
		""" Pump the notification messages and execute the actions """
		msg_lst = [] # list if SMS message objects

		print("Creating objects")
		sms = SMS( self.sim )
		voice = Voice( self.sim )

		print("Clearing stored SMS")
		sms_list = sms.list( SMS.ALL, max_row=None )
		for item in sms_list:
			print( f"\tdeleting {item.id}" )
			sms.delete( item.id )


		print("Starting URC supervisor %s" % __version__ )
		
		# Everything normal
		self.led.pulse( 3000 ) # 3 seconds pulses

		while self.base.run_app:
			self.update()
			if self.sim.notifs.has_new:
				print( '-'*40 )
				print( "%i notifications availables" % len(self.sim.notifs) )
				# DEBUG: Show all notifications 				
				print( list(self.sim.notifs) )
				print( '-'*40 )

				# Pump all notifications
				_time,_type,_msg,_cargo = self.sim.notifs.pop()
				while _type != None: # Treat all notifications
					if (_type==Notifications.CURRENT_CALL) and (_cargo.mode == Notifications.MODE_VOICE) and (_cargo.state==Notifications.CALLSTATE_INCOMING):
						print("Incoming call from %s" % _cargo.number )
						print("\tHang-up the call")
						voice.hang_up()
					elif _type==Notifications.SMS:
						print("SMS received @ id %s" % _cargo )
						msg_lst.append( sms.read(_cargo) )
						sms.delete(_cargo)

					_time,_type,_msg,_cargo = self.sim.notifs.pop() # Next notification					
					idle()


				# ==== Treat incoming SMS =========================================================
				msg=None
				if len(msg_lst)>0:
					msg=msg_lst.pop()
				while  msg != None:
					if self.is_auth( msg.phone ):
						# Execute the SMS command
						self.run_sms_handler( msg )
					else:
						print( 'Denied from %s!' % msg.phone )
						self.register_message( msg.phone, DENIED_STR )
					

					# Pop next message
					if len(msg_lst)>0:
						msg=msg_lst.pop()
					else:
						msg = None

			# Output Messages
			#  Send the SMS notification to master and other admins 
			#  Send message one by one
			if len(self.notif_lst)>0: 
				to_phone, label, for_phone = self.notif_lst.pop()
				if for_phone != None:
					_m = "%s : %s" % (label, for_phone)
				else:
					_m = label
				try:
					sms.send( to_phone, _m )
				except SMSError as err:
					# Do not halt software on SMS ERROR
					print( '_loop: Unexpected error %r' % err )
					print( '_loop: Ignoring SMSError' )

	def run( self ):
		try:
			self._loop()
			print( "Exit!" )
		except Exception as err:
			print( 'run: Unexpected error %r' % err )
			print( 'Halting software!')
			self.led.error( error_count=3 )
			while True:
				self.led.update()
				idle()




