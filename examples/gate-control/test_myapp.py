# Tuned Gate Control Software
#
# This example show how to customize the application
# to handle your own SMS.
#
# Just copy this file as main.py on your MicroPython board
#
# See project: https://github.com/mchobby/micropython-4G-BASE-STATION
#
from gatectrl import GateControlApp

class MyApp( GateControlApp ):
	def __init__( self ):
		super().__init__()
		# *** CREATE YOUR OBJECTs GHERE ***

		# Intercept message: "say,first_param,second_param" parameters are optional
		self.register_sms_handler( 'say' , self._say_response ) # Keyword limited to 6 chars.

	def update( self ):		
		# Called again and again at each loop execution
		# *** PERFORM YOUR OBJECTs UPDATES HERE ***
		
		# Execute Normal operation here
		super().update() 


	def _say_response( self, msg, params ):
		# msg: incoming message
		# params[0] : None or the first parameter value (as string)
		# params[1] : None or the second parameter value (as string)
		
		# *** COMPUTE YOUR RESPONSE HERE ***
		self.register_notifications( notif_for=msg.phone, msg='I say Hello!' )


app = MyApp()
app.power_up()
app.run()

# Now you can also use the "say" message from the master/admins.