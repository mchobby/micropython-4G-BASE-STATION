# Customized SMS Control Software
#
# This example show how to implement action based on incoming SMS.
# The SMS contains:
# 1) CASE-INSENSITIVE Keyword (10 chars max).
# 2) an optional first parameter params[0] after a comma
# 3) an optional second parameter params[1] after another coma
# 
# 
# Just copy this file as main.py on your MicroPython board
#
# See project: https://github.com/mchobby/micropython-4G-BASE-STATION
#
from smsctrl import SmsControlApp, HandlerError
from smsctrl import __version__ as smsctrl_version

# My App Version
__version__ = '0.1.0'

class MyApp( SmsControlApp ):
	def __init__( self ):
		super().__init__()
		# *** CREATE YOUR OBJECTs GHERE ***

		# Intercept message: "keyword,first_param,second_param" parameters are optional
		self.register_sms_handler( 'say'   , self.say_handler  )
		self.register_sms_handler( 'info'  , self.info_handler ) # Keyword limited to 10 chars.
		self.register_sms_handler( 'error' , self.send_error_handler ) # Keyword limited to 10 chars.
		self.register_sms_handler( 'punish', self.punish_handler )
		self.register_sms_handler( 'on1'   , self.relay_handler )
		self.register_sms_handler( 'off1'  , self.relay_handler )
		self.register_sms_handler( 'on2'   , self.relay_handler )
		self.register_sms_handler( 'off2'  , self.relay_handler )

	# UNCOMMENT TO RESTRICT ACCESS to given phone number
	#
	#def is_auth( self, phone_nr ):
	#	return phone_nr in ('+32444661122','+32444998877')

	def update( self ):		
		# Called again and again at each loop execution

		# *** PERFORM YOUR OBJECTs UPDATES HERE ***
		
		# Execute Normal operation here
		super().update() 

	# --- SMS Handlers ---
	def say_handler( self, msg, params ):	
		# msg: incoming message
		# params[0] : None or the first parameter value (as string)
		# params[1] : None or the second parameter value (as string)

		# *** COMPUTE YOUR RESPONSE HERE ***
		self.register_message( notif_for=msg.phone, msg='I say %s!' % ("Hello" if params[0]==None else params[0]) )


	def info_handler( self, msg, params ):
		""" Just return the information about this program.

			msg: incoming message (msg is a sms.py:Message object)
		    params[0] : None or the first parameter value (as string)
			params[1] : None or the second parameter value (as string) """

		# A SMS Handler will reply with several SMS messages.
		self.register_message( msg.phone, "MyApp Version is %s" % __version__ )
		self.register_message( msg.phone, "SmsCtrl Version is %s" % smsctrl_version )
		self.register_message( msg.phone, "IN1 = %s, IN2 = %s" % (self.base.in1.value(), self.base.in2.value() ) )
		self.register_message( msg.phone, "params are : %r , %r" % (params[0],params[1]) ) # Params may be None
		

	def send_error_handler( self, msg, params ):
		""" Just throw an error to the sender """
		# Use raise HandlerError( 'blablabla' ) to return an error to the SMS sender
		i = 1
		y = 0
		print( i / y )
		raise HandlerError( 'This error message will be send to SMS sender' )


	def punish_handler( self, msg, params ):
		""" send a message to another phone number... communicated as params[0] """
		if not self.is_phone_nr( params[0] ):
			raise HandlerError( 'Invalid phone Number as parameter!' )
		# Remark: 
		#   When sending message to another recipient, it is a good habit to mention source_nr.
		#   Such a way, the recipient knows the true origin of the message.
		self.register_message( params[0], "You have been punished!", source_nr=msg.phone )


	def relay_handler( self, msg, params ): 
		""" This method is called for on1 & off1 """
		relay = None		
		if '1' in msg.message:
			relay = self.base.rel1
		elif '2' in msg.message:
			relay = self.base.rel2
		else:
			raise HandleError( 'Invalid relay number!')

		# warning the msg.message is case-sensitive.
		if 'ON' in msg.message.upper():
			relay.on()
		elif 'OFF' in msg.message.upper():
			relay.off()
		else:
			raise HandlerError( 'only "on" or "off" maybe used!' )

app = MyApp()
app.power_up()
app.run()