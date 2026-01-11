#!/bin/sh

# Install the files on a pico
if [ -z "$1" ]
  then
    echo "/dev/ttyACMx parameter missing!"
                exit 0
fi

CUR_DIR=`pwd`
while :
do

clear
# echo "Wait for Pico on $1..."
# while [ ! -f /media/domeu/RPI-RP2/INFO_UF2.TXT ]; do sleep 1; done
# echo "Flashing MicroPython..."
# cp /home/domeu/Téléchargements/upy-os/rp2-pico-20230426-v1.20.0.uf2 /media/domeu/RPI-RP2/
# echo "Wait Pico reboot on $1..."
# while ! (ls $1 2>/dev/null) do sleep 1; done;

mpremote connect $1 mkdir :lib


# Install the LIBRARIES on a pico
mpremote connect $1 mip install github:mchobby/micropython-aioschedule
mpremote connect $1 mip install github:mchobby/micropython-A7682E-modem
mpremote connect $1 mip install github:mchobby/esp8266-upy/LIBRARIAN
mpremote mip install github:mchobby/esp8266-upy/bme280-bmp280


mpremote connect $1 fs mkdir lib
echo "Installing 4G-Base-Station on Pico @ $1"
for LIB_FILE in $(ls lib/*.py)
do
		mpremote connect $1 fs cp $LIB_FILE :$LIB_FILE
done

# Install the SMS-Control libs
mpremote connect $1 fs cp examples/sms-control/smsctrl.py :lib/smsctrl.py
# Keeps an installable copy
mpremote connect $1 mkdir smsctrl.bak
mpremote connect $1 fs cp examples/sms-control/main.py :smsctrl.bak/main.py
mpremote connect $1 fs cp examples/sms-control/boot.py :smsctrl.bak/boot.py

# Install the Gate-Control
mpremote connect $1 fs cp examples/gate-control/inalarm.py :lib/inalarm.py
mpremote connect $1 fs cp examples/gate-control/gatectrl.py :lib/gatectrl.py

mpremote connect $1 fs cp examples/gate-control/pltconf.py :pltconf.py
mpremote connect $1 fs cp examples/gate-control/main.py :main.py
mpremote connect $1 fs cp examples/gate-control/boot.py :boot.py
# Keeps an installable copy
mpremote connect $1 mkdir gatectrl.bak
mpremote connect $1 fs cp examples/gate-control/main.py :gatectrl.bak/main.py
mpremote connect $1 fs cp examples/gate-control/boot.py :gatectrl.bak/boot.py

# for NAME in maze_solver.py line_follower.py test_zumoshield.py test_readline2.py test_play.py test_compass.py
# do
# 		mpremote connect $1 fs cp examples/$NAME :$NAME
# done

# Test the board
mpremote connect $1 run blink.py

echo " "
echo "Done!"
done

