from micropython import const
from machine import Pin, I2C, SPI, UART

LED = const(12)
RUN_APP = const(13)
IN1 = const(14)
IN2 = const(15)
IN3 = const(16)
IN4 = const(17)
REL1 = const(2)
REL2 = const(3)
I2C_PARAM = {'id':1, 'sda':Pin(6), 'scl':Pin(7)}  # **kwargs for I2C() creation
UART1_PARAM = ( [1], {'tx':Pin(4), 'rx':Pin(5)} ) # *args, **kwargs)
UART0_PARAM = ( [0], {'tx':Pin(0), 'rx':Pin(1)} ) # *args, **kwargs)

class BaseStation:
	""" Hardware control of the base station """
	def __init__(self):
		self.__run_app = Pin( RUN_APP, Pin.IN, Pin.PULL_UP )
		self.__in3 = None # See property in3
		self.__in4 = None # See property in4
		self.__i2c = None
		self.__uart1 = None
		self.__uart0 = None

		self.led = Pin( LED, Pin.OUT )
		self.in1 = Pin( IN1, Pin.IN )
		self.in2 = Pin( IN2, Pin.IN )
		self.rel1 = Pin( REL1, Pin.OUT )
		self.rel2 = Pin( REL2, Pin.OUT )


	@property
	def run_app(self):
		""" Return True when Run_App switch is in RUN position """
		return self.__run_app.value()

	@property
	def in3( self ):
		""" Configured as Input at first acces. May instead be used as output by user code """
		if self.__in3==None:
			self.__in3 = Pin( IN3, Pin.IN )
		return self.__in3

	@property
	def in4( self ):
		""" Configured as Input at first access. May instead be used as output by user code """
		if self.__in4==None:
			self.__in4 = Pin( IN4, Pin.IN )
		return self.__in4

	def i2c( self, **kwarg ):
		""" I2C on Qwiic & UEXT. Configure the I2C at first access """
		if self.__i2c==None:
			kwarg.update( I2C_PARAM ) #**kwarg} # Merge the **kwargs
			self.__i2c = I2C( **kwarg )
		return self.__i2c

	def uart1( self, **kwarg ):
		""" UART on the UEXT. Configure the UART at first access """
		if self.__uart1==None:
			kwarg.update( UART1_PARAM[1] )
			self.__uart1 = UART( *UART1_PARAM[0], **kwarg )
		return self.__uart1

	def uart0( self, **kwarg ):
		""" UART on the RPi GPIO. Configure the UART at first access """
		if self.__uart0==None:
			kwarg.update( UART0_PARAM[1] )
			self.__uart0 = UART( *UART0_PARAM[0], **kwarg )
		return self.__uart0