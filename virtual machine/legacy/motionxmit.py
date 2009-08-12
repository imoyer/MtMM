# Motion Command Transmitter
# 056 PCB Mill
#
# Ilan E. Moyer
#
#1/1/09
#
#--------IMPORTS-----------------------------------------------------

import sys, commands
import serial

#-------CONFIGURE AND OPEN SERIAL PORT-------------------------------
portnumber = 3
baudrate = 19200
sertimeout = 1 #in seconds

serport = serial.Serial(portnumber,baudrate, timeout=sertimeout)

#-------MOTION PARAMETERS--------------------------------------------

startbyte = 0
overallspeed = 255
x_rate0 = 64
x_rate1 = 0
y_rate0 = 64
y_rate1 = 0
z_rate0 = 16
z_rate1 = 0

duration0 = 0
duration1 = 4
duration2 = 0
duration3 = 0

x_direction = 2 #0 is off, 1 is forward, 2 is reverse
y_direction = 2
z_direction = 0
syncbyte = (x_direction*1) + (y_direction*4) + (z_direction * 16)

serport.write(chr(startbyte))
a = serport.read()
print ord(a)
serport.write(chr(overallspeed))
a = serport.read()
print ord(a)
serport.write(chr(x_rate0))
a = serport.read()
print ord(a)
serport.write(chr(x_rate1))
a = serport.read()
print ord(a)
serport.write(chr(y_rate0))
a = serport.read()
print ord(a)
serport.write(chr(y_rate1))
a = serport.read()
print ord(a)
serport.write(chr(z_rate0))
a = serport.read()
print ord(a)
serport.write(chr(z_rate1))
a = serport.read()
print ord(a)
serport.write(chr(duration0))
a = serport.read()
print ord(a)
serport.write(chr(duration1))
a = serport.read()
print ord(a)
serport.write(chr(duration2))
a = serport.read()
print ord(a)
serport.write(chr(duration3))
a = serport.read()
print ord(a)
serport.write(chr(syncbyte))
a = serport.read()
print ord(a)


