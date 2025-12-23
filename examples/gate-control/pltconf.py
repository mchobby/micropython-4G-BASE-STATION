""" pltconf.py - Plateform Config  (storage and update) """
from ostls import file_exists
import json


# ===  Rights =========================
ADD_USER = "AU" # CAN Add/Remove users or Admin
NOTIF_IN1 = "I1" # Get Notification SMS on IN1
NOTIF_IN2 = "I2" # Get Notification SMS on IN2 
NOTIF_IN3 = "I3" # Get Notification SMS on IN3
NOTIF_IN4 = "I4" # Get Notification SMS on IN4 
NOTIF_OUT1 = "O1" # Get Notification SMS on OUT1 activated
NOTIF_OUT2 = "O2" # Get Notification SMS on OUT2 activated
CAN_OUT1 = "C1" # Can activate OUT1 (with call)
CAN_OUT2 = "C2" # Can activate OUT2 (with SMS)

ALL_RIGHTS = [ ADD_USER, NOTIF_IN1, NOTIF_IN2, NOTIF_IN3, NOTIF_IN4, NOTIF_OUT1, NOTIF_OUT2, CAN_OUT1, CAN_OUT2 ]
RESTRICTED_RIGHTS = [ ADD_USER ] # Right with RESTRICTED conditions on "transmission"...

DEFAULT_RIGHTS = {  'master' : ':AU:I1:I2:I3:I4:O1:O2:C1:C2:',
					'admins' : ':I1:I2:I3:I4:O1:O2:C1:C2:',
					'users'  : ':C1:'}

MODE_PULSE = "P"
MODE_TOGGLE = "T"

def create_config():
	""" Initialize a basic configuration structure """
	return  {
			"version":1, 
			"main":{
				"master":None, # Master Phone Number
				"pswd":None,   # Master Password (if any)
				"poweron-label":"Starting",
				"in1-label":"IN1 activated!",
				"in2-label":"IN2 activated!",
				"in3-label":"IN3 activated!",
				"in4-label":"IN4 activated!",
				"out1-label":"OUT1 activated",
				"out2-label":"OUT2 activated",
				"out1-cmd":"OUT1",
				"out1-mode":MODE_PULSE, # Pulse or Toggle
				"out1-sec":3, # 3 seconds Pulse time
				"out2-cmd":"OUT2",
				"out2-mode":MODE_PULSE,
				"out2-sec":3,
				"in1-mode":"D",
				"in1-obs":1,
				"in1-idle":2,
				"in1-irst":1,
				"in1-ntyp":"S",
				"in2-mode":"D",
				"in2-obs":1,
				"in2-idle":2,
				"in2-irst":1,
				"in2-ntyp":"S",
				"in3-mode":"D",
				"in3-obs":1,
				"in3-idle":2,
				"in3-irst":1,
				"in3-ntyp":"S",
				"in4-mode":"D",
				"in4-obs":1,
				"in4-idle":2,
				"in4-irst":1,
				"in4-ntyp":"S"
				} ,
			"admins":{
				# Phone = comma separated right 
				},
			"users":{
				# List of autorised phone number = right (extra right like CAN_OUT2)
				}
			
			}
	

def upgrade_config( config ):
	""" Upgrade internal structure from one version to the other """
	pass


class PlateformConfig:
	def __init__( self, json_filename ):
		self._config = None
		self._filename = json_filename
		if not file_exists( json_filename ):
			self._config = create_config()
		else:
			with open( json_filename,"r") as f:
				self._config = json.load( f )
		upgrade_config( self._config )


	def save( self ):
		with open( self._filename, "w" ) as f:
			json.dump( self._config, f )


	def value( self, key, default=None ):
		""" Extract the parameter value from "main" entry """
		if key in self._config['main']:
			return self._config['main'][key]
		else:
			return default

	def set_value( self, key, value ):
		""" Set the value of a "main" entry """
		self._config['main'][key] = value

	@property
	def main( self ):
		""" access to the main parameters """
		return self._config['main']

	@property
	def admins( self ):
		""" dict of admin numbers """
		return self._config['admins']

	@property
	def users( self ):
		""" dict of users numbers """
		return self._config['users']

	def get_rights( self, phone_nr ):
		""" List of :right:right:right: for a given phone number """
		if phone_nr in self._config['admins']:
			return self._config['admins'][phone_nr]
		elif phone_nr in self._config['users']:
			return self._config['users'][phone_nr]
		else:
			return None

	def set_rights( self, phone_nr, rights ):
		""" set the list of :right:right:right: for a given phone number """
		if phone_nr in self._config['admins']:
			self._config['admins'][phone_nr] = rights
		elif phone_nr in self._config['users']:
			self._config['users'][phone_nr] = rights
		else:
			raise Exception('set_right: invalid %ss' % phone_nr)

	def add_right( self, phone_nr, shortcode ):
		shortcode = shortcode.strip().upper()
		rights = self.get_rights( phone_nr )
		assert rights
		assert shortcode in ALL_RIGHTS
		if (':%s:'%shortcode) in rights: # nothing to do
			return 
		rights += (':%s:'%shortcode)
		self.set_rights( phone_nr, rights.replace('::',':') )

	def del_right( self, phone_nr, shortcode ):
		shortcode = shortcode.strip().upper()
		rights = self.get_rights( phone_nr )
		assert rights
		assert shortcode in ALL_RIGHTS
		self.set_rights( phone_nr, rights.replace(':%s:'%shortcode,':') )


	def phones_for( self, right ):
		""" return the list of phone_nr having the given right """
		right = ':%s:' % right
		_l = []
		for phone_nr, rights in self._config['admins'].items():
			if right in rights:
				_l.append( phone_nr )
		for phone_nr, rights in self._config['users'].items():
			if right in rights:
				_l.append( phone_nr )
		return _l