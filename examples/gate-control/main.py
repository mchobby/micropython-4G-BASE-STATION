# Gate Control Software - Main Software
#
# See project: https://github.com/mchobby/micropython-4G-BASE-STATION
#
from gatectrl import GateControlApp

app = GateControlApp()
app.power_up()
app.run()