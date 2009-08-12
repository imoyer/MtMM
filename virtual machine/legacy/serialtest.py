# Serial Port Tester
# 056 PCB Mill
#
# Ilan E. Moyer
#
#1/1/09
#
#--------IMPORTS-----------------------------------------------------

import sys, commands
import time
import serial

serport = serial.Serial('COM6',19200, timeout=None)

a=255
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=6
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=0
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=0
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=0
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=0
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=50
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=0
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=196
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=9
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=0
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=0
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
a=16
serport.write(chr(a))
s = serport.read()
t=ord(s)
print t
