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
from pltconf import *
from ledtls import SuperLed
from station import *
from inalarm import *
from timetls import TimeoutTimer
from maps import slice_by
import time

DENIED_STR = 'Denied!'
DONE_STR   = 'Done'
ERROR_STR  = 'ERROR!'

__version__ = '0.1.0'

class HandlerError( Exception ):
	""" Error raise while executing an handler """
	pass

def valid_text( s ):
	for ch in s:
		if not( (48<= ord(ch) <= 90) or (97<= ord(ch) <=122) or (ch in '!#+ -.')):
			return False
	return True

class GateControlApp:
	def __init__( self ):
		self.config = PlateformConfig( 'config.dat' )
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
		self.alarms = [] # Alarm object registered for inputs 1 to 4

		self.alarms.append( InAlarm(self.base.in1,self.config.main,'in1') )
		self.alarms.append( InAlarm(self.base.in2,self.config.main,'in2') )
		self.alarms.append( InAlarm(self.base.in3,self.config.main,'in3') )
		self.alarms.append( InAlarm(self.base.in4,self.config.main,'in4') )

		self.register_sms_handler( 'Save' , self._save_config )
		self.register_sms_handler( 'UAdd' , self._user_add )
		self.register_sms_handler( 'UDel' , self._user_del )
		self.register_sms_handler( 'Ulist', self._user_list )
		self.register_sms_handler( 'Rview', self._right_view )
		self.register_sms_handler( 'Radd' , self._right_add )
		self.register_sms_handler( 'Rdel' , self._right_del )
		self.register_sms_handler( 'Plist', self._param_list )
		self.register_sms_handler( 'Pset' , self._param_set )


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

	def register_notifications( self, notif_for, msg, source_nr=None):
		""" Register notifications in notif_lst .  The main loop will send them one by one.
		    notif_for : is the "right" to check on users to send them the notificaiton. With + prefix, it is a single phone number. 
		    msg : the messahe to send. With a @ prefix, it extract the label from the configuration
		    source_nr : None or the phone_nr that raized the notification. """
		if notif_for[0]=='+': # it is a phone number
			self.notif_lst.append( (notif_for, msg, source_nr) )
		else: # it is a right
			phone_lst = self.config.phones_for( notif_for )
			for to_phone in phone_lst:
				self.notif_lst.append( (to_phone, msg, source_nr) )


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

			if not( 1<=len(code)<=6 ):
				raise Exception( "Invalid %s code length!" % code )
			if (param1!=None) and len(param1)>20:
				raise Exception( "Invalid param1 length!" )
			if (param2!=None) and (len(param2)>30):
				raise Exception( "Invalid param2 length!" )			

		except Exception as err:
			print("Fail to decode message %s from %s" % (msg.message,msg.phone) )
			print("\t%r" % err )
			self.register_notifications( notif_for=msg.phone, msg='Invalid format!' ) # Send deny
		

		match = False
		for shortcode, handler in self.sms_handlers:
			if shortcode==code:
				try:
					match = True
					handler( msg, [param1,param2] )
					self.register_notifications( notif_for=msg.phone, msg='Done' ) # Send error message
				except Exception as err:
					print("Fail to execute message %s from %s" % (msg.message,msg.phone) )
					print("\t%r" % err )
					self.register_notifications( notif_for=self.config.value('master'), msg='Fail! : %s' % msg.message, source_nr=msg.phone ) # copu msg to master
					self.register_notifications( notif_for=self.config.value('master'), msg=('%r' % err), source_nr=msg.phone ) # Send error to master
					self.register_notifications( notif_for=msg.phone, msg=ERROR_STR )
				break;
		if not( match ):
			self.register_notifications( notif_for=self.config.value('master'), msg='Invalid %s shortcode!' % code, source_nr=msg.phone ) # Notify Master
			self.register_notifications( notif_for=msg.phone, msg=ERROR_STR ) # Notify of error


	# --- SMS Handlers ---
	def _user_add( self, msg, params ):
		""" add a user (required the ADD_USER right!).
			msg is a sms.py:Message object
			params is a list of the params received in the SMS """
		# User is already an admin when this method is executed.
		# User must also have the ADD_USER right
		if not (':%s:'%ADD_USER) in self.config.get_rights( msg.phone ):
			raise HandlerError( 'Requires the ADD_USER right' )
		if not self.is_phone_nr( params[0] ):
			raise HandlerError( 'Invalid phone Number!' )
		# Already registered ?
		_r = self.config.get_rights(params[0])
		if _r!=None: 
			raise HandlerError( 'Already registered!' )
		self.config.users[params[0]]=DEFAULT_RIGHTS['users']

	def _user_del( self, msg, params ):
		if not (':%s:'%ADD_USER) in self.config.get_rights( msg.phone ):
			raise HandlerError( 'Requires the ADD_USER right' )

		if params[0] in self.config.users:
			del( self.config.users[params[0]] )
		elif params[0] in self.config.admins:
			if params[0]==self.config.value('master'):
				raise HandlerError( 'Cannot delete Master!' )
			else:
				del( self.config.admins[params[0]] )

	def _user_list( self, msg, params ):
		if not (':%s:'%ADD_USER) in self.config.get_rights( msg.phone ):
			raise HandlerError( 'Requires the ADD_USER right' )

		_l=[]
		_l.append('Admins:')
		for k,v in self.config.admins.items():
			_l.append( '  %s : %s' % (k,v.replace(':',' ')) )
		_l.append('Users:')
		for k,v in self.config.users.items():
			_l.append( '  %s : %s' % (k,v.replace(':',' ')) )

		for sub_list in slice_by(_l,5):
			sms = SMS( self.sim )
			sms.send( msg.phone, '\r\n'.join( sub_list) )

	def _save_config( self, msg, params ):
		""" Save the current configuration to the file """
		self.config.save()
		if (params[0]!=None)and(params[0].upper()=="REBOOT"):
			import sys
			sys.exit() # Soft reset

	def _right_view( self, msg, params ):
		""" View the right of a given user """
		phone_nr = params[0]
		if not self.is_phone_nr( phone_nr ):
			raise HandlerError( 'Invalid phone Number!' )
		_r = self.config.get_rights( phone_nr )
		# Direct response
		sms = SMS( self.sim )
		# replace : with space to avoids SMS content interpretation by android
		sms.send( msg.phone, _r.replace(':', ' ') if _r!=None else 'No user!')
		del( sms )

	def _right_add( self, msg, params ):
		""" add right to a given user """
		# master can update master & admins
		# Admins can update user
		sender_nr = msg.phone
		target_nr = params[0]
		if len(params)<2:
			raise HandlerError( 'missing param!' )
		# Right to add to the user
		rights = params[1].upper().strip().split(' ')

		user_right = self.config.get_rights(target_nr)
		if user_right==None:
			raise HandleError( DENIED_STR )

		# Only master can modify himself
		if ( target_nr==self.config.value('master') ) and ( sender_nr!=self.config.value('master') ):
			raise HandlerError( DENIED_STR )
		# Only master can modify admins
		if ( target_nr in self.config.admins ) and ( sender_nr!=self.config.value('master') ):
			raise HandlerError( DENIED_STR )
		# Otherwise sender_nr is an admin and it can modify the remaining accounts

		# Check that rights exists
		for right in rights:
			if not( right in ALL_RIGHTS ):
				raise HandlerError( 'Invalid right %s!' % right )
		# Check ADD_USER constraint (only the owner having it can add/remove it to others)
		for restricted in RESTRICTED_RIGHTS:
			if (restricted in rights) and not ((":%s:"%restricted) in self.config.get_rights(sender_nr)):
				raise HandlerError( 'User does own the %s right' % restricted )

		# Append the rights to the user
		for right in rights:
			self.config.add_right( target_nr, right )

	def _right_del( self, msg, params ):
		""" add right to a given user """
		# see _right_add for rules
		sender_nr = msg.phone
		target_nr = params[0]
		if len(params)<2:
			raise HandlerError( 'missing param!' )
		# Right to add to the user
		rights = params[1].upper().strip().split(' ')

		user_right = self.config.get_rights(target_nr)
		if user_right==None:
			raise HandleError( DENIED_STR )

		# Only master can modify himself
		if ( target_nr==self.config.value('master') ) and ( sender_nr!=self.config.value('master') ):
			raise HandlerError( DENIED_STR )
		# Only master can modify admins
		if ( target_nr in self.config.admins ) and ( sender_nr!=self.config.value('master') ):
			raise HandlerError( DENIED_STR )
		# Otherwise sender_nr is an admin and it can modify the remaining accounts

		# Check ADD_USER constraint (only the owner having it can add/remove it to others)
		for restricted in RESTRICTED_RIGHTS:
			if (restricted in rights) and not ((":%s:"%restricted) in self.config.get_rights(sender_nr)):
				raise HandlerError( 'User does own the %s right' % restricted )

		# remove the rights to the user
		for right in rights:
			self.config.del_right( target_nr, right )

	def _param_list( self, msg, params ):
		p_list = [ (k,v) for k,v in self.config.main.items() if (k!='master') and (k!='pswd') ]
		
		if (params[0]!=None) and (len(params)>0):
			p_filtered = [ (k,v) for k,v in p_list if params[0] in k ]
		else:
			p_filtered = p_list
		
		sms = SMS( self.sim )
		for sublist in slice_by( p_filtered, 5 ):
			# print( "\r\n".join( [ "%s = %s" % (k,v) for k,v in sublist ] ) )
			sms.send( msg.phone, "\r\n".join( [ "%s = %s" % (k,v) for k,v in sublist ] ) )
		del( sms )

	def _param_set( self, msg, params ):
		if (params[0]==None) or (params[1]==None):
			HandleError( '2 parameters required!' ) 

		param_name = params[0].strip()
		if not( param_name ) in self.config.main:
			raise HandlerError( 'Invalid %s parameter name' % param_name )
		if (param_name=='master') or (param_name=='pswd'):
			raise HandlerError( 'forbidden %s parameter name' % param_name )

		param_value = params[1].strip()
		param_datatype = type( self.config.value( param_name ) )
		if param_datatype is int:
			# IF stored value is integer THEN new value must also be an integer
			try:
				param_value = int(param_value)
			except:
				raise HandlerError( "integer value expected!")
		else:
			if not valid_text(param_value):
				raise HandlerError( "Valid text expected!")

		self.config.set_value( param_name, param_value )


	# --- Common Method ---

	def is_phone_nr( self, value ):
		""" Check if the value looks to be a phone bumber """
		return len(value)>2 and (value[0]=='+') and (value[1:].isdigit())

	def is_output_auth( self, output_nr, phone_nr ):
		""" Check if the phone NR can act on output 1 or 2 """
		# admin can also activates anything
		_rights = self.config.get_rights( phone_nr )
		return (_rights != None) and ( (":C%i:" % output_nr) in _rights )

	def output_action( self, output_nr ):
		""" Change the output 1 or 2 accordingly to the configuration """
		mode = self.config.value('out%i-mode' % output_nr).upper()
		sec  = self.config.value('out%i-sec' % output_nr)
		pin = self.base.rel1 if output_nr==1 else self.base.rel2
		if mode==MODE_PULSE:
			pin.on()
			time.sleep(sec)
			pin.off()
		elif mode==MODE_TOGGLE:
			pin.toggle()
		else:
			raise Exception( "output_action: Undefined mode %s!" % mode)

	def is_out_cmd( self, msg ):
		""" Check if the SMS contains the OUT1 or OUT2 sms and 
			returns 0 (=False), 1 or 2 """
		if ',' in msg.message:
			s = msg.message.split(',')[0].strip().upper()
		else:
			s = msg.message.strip().upper()

		if self.config.value('out1-cmd').upper() in s:
			return 1
		elif  self.config.value('out2-cmd').upper() in s:
			return 2
		return 0


	def update( self ):
		# Updates performed by the loop
		self.led.update()
		self.sim.update()
		for alarm in self.alarms:
			alarm.update()		


	def _loop( self ):
		""" Pump the notification messages and execute the actions """
		call_lst = [] # list of Phone calls
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

		bWaitMaster = False # We need a master Phone
		if self.config.value('master')==None:
			bWaitMaster = True
			print("No master phone number! Requires first call...")
			self.led.heartbeat( lit_ms=50, pause_ms=100 ) # 250ms
		else:
			# Inform Master of the startup
			sms.send( self.config.value('master'), 'v%s %s' % (__version__,self.config.value('poweron-label')) )
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
						call_lst.append( _cargo.number )
						print("\tPick-up the call")
						voice.answer()
						time.sleep_ms(100)
						print("\tHang-up the call")
						voice.hang_up()
					elif _type==Notifications.SMS:
						print("SMS received @ id %s" % _cargo )
						msg_lst.append( sms.read(_cargo) )
						sms.delete(_cargo)

					_time,_type,_msg,_cargo = self.sim.notifs.pop() # Next notification					
					idle()

				# ==== Treat incoming CALL ========================================================
				phone_nr = None
				if len(call_lst)>0:
					phone_nr=call_lst.pop()
				while phone_nr != None:
					# Master assignment
					if bWaitMaster:
						bWaitMaster=False
						print( "Assign master to %s" % phone_nr )
						self.config.set_value( 'master', phone_nr )
						# Add the right for the master 
						self.config.admins[phone_nr]=DEFAULT_RIGHTS['master']
						self.config.save()
						sms.send( self.config.value('master'), 'You are master now!' )
						self.led.pulse( 3000 ) # 3 seconds pulses
						call_lst.clear()
						msg_lst.clear()
					else:
						# check for auth on phone call
						if self.is_output_auth( 1, phone_nr ):
							print( 'Authorized CAN_OUT1 call for %s' % phone_nr )
							self.output_action( 1 )							
							self.register_notifications( notif_for=NOTIF_OUT1, msg='@out1-label', source_nr=phone_nr ) # notify other users
						else:
							print( 'Unauthorized CAN_OUT1 call for %s' % phone_nr )
							self.register_notifications( notif_for=phone_nr, msg=DENIED_STR ) # Send deny
							self.register_notifications( notif_for=self.config.value('master'), msg='CAN_OUT1 denied', source_nr=phone_nr ) # Inform master

					# pop next entry
					if len(call_lst)>0:
						phone_nr=call_lst.pop()
					else:
						phone_nr=None


				# ==== Treat incoming SMS =========================================================
				msg=None
				if len(msg_lst)>0:
					msg=msg_lst.pop()
				while  msg != None:
					# Is this the OUT1 or OUT2 SMS 
					out_nr = self.is_out_cmd( msg )
					if out_nr>0:
						# check for auth on SMS msg
						if self.is_output_auth( out_nr, msg.phone ):
							print( 'Authorized CAN_OUT%i SMS for %s' % (out_nr, msg.phone) )
							self.output_action( out_nr )
							self.register_notifications( notif_for=msg.phone, msg=DONE_STR ) # Send DONE
							self.register_notifications( notif_for=NOTIF_OUT1, msg='@out%i-label'%out_nr, source_nr=msg.phone ) # notify other users
						else:
							print( 'Unauthorized CAN_OUT%i call for %s' % (out_nr,msg.phone) )
							self.register_notifications( notif_for=msg.phone, msg=DENIED_STR ) # Send deny
							self.register_notifications( notif_for=self.config.value('master'), msg='CAN_OUT%i denied' % out_nr, source_nr=msg.phone ) # Inform master
					else:
						# only admin can send configuration message
						if not( msg.phone in self.config.admins ):
							print( 'Unauthorized msg %s from %s' % (msg.message,msg.phone) )
							self.register_notifications( notif_for=msg.phone, msg=DENIED_STR ) # Send deny
							self.register_notifications( notif_for=self.config.value('master'), msg='Denied SMS', source_nr=msg.phone ) # Inform master	
						else: # Sender is an admin... 
							# Execute the SMS command
							self.run_sms_handler( msg )
					

					# Pop next message
					if len(msg_lst)>0:
						msg=msg_lst.pop()
					else:
						msg = None

			for alarm in self.alarms:
				if alarm.alarm_notif_once:
					# extract the number (1,2,...) from alarm prefix (in1,in2,...)
					alarm_id = 0
					for c in alarm.prefix:
						if c.isdigit():
							alarm_id = (alarm_id*10) + int(c)
					print( 'alarm IN%i triggered' % alarm_id )
					# Get user to notify
					phones = self.config.phones_for( 'I%i' % alarm_id )
					print( '\t',phones )
					# Call notification
					if self.config.value( '%s-ntyp' % alarm.prefix).upper()=='C':
						if len(phones)>0:
							voice = Voice( self.sim )
							# If phone under call => Hang-up
							_l = voice.call_status
							if ( len(_l)>0 ) and ( _l[0].state!=STATE_DISCONNECT ):
								voice.hang_up()
							time.sleep_ms(500)
							# Make a new call
							voice.call( phones[0] )
							del( voice )
					else:
						# SMS notification
						for phone in phones:
							self.register_notifications( notif_for=phone, msg=self.config.value('in%i-label'%alarm_id, 'no-msg')  )

			# Output Notifications
			#  Send the SMS notification to master and other admins 
			#  Send message one by one
			if len(self.notif_lst)>0: 
				to_phone, label, for_phone = self.notif_lst.pop()
				if label[0]=='@':
					label = self.config.value(label[1:])
				if for_phone != None:
					_m = "%s : %s" % (for_phone, label)
				else:
					_m = label
				sms.send( to_phone, _m )

	def run( self ):
		try:
			self._loop()
			print( "Exit!" )
		except Exception as err:
			print( 'run: Unexpected error %r' % err )
			self.led.error( error_count=3 )
			while True:
				self.led.update()
				idle()
