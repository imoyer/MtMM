#
# MAS.961 VIRTUAL MACHINE
#


from Tkinter import *
from string import *
from socket import *
from select import *
from tkFileDialog import *

import sys
import commands
import csv
import numpy
#import numarray
import math


import serial, time, signal


TIMEOUT = 2
END = 192
ESC = 219
ESC_END = 220
ESC_ESC = 221

def GCD(a, b):
    while b != 0:
        (a, b) = (b, a%b)
    return a


def handler(signum, frame):
   #
   # timeout handler
   #
   raise IOError, "I0 timeout"

def high(number):
   #
   # return high byte
   #
   return (number >> 8)

def low(number):
   #
   # return low byte
   #
   return (number & 255)

def idle(parent):
   #
   # idle routine
   #
   if (ser.inWaiting() != 0):
      #
      # I0 serial data waiting, read packet
      #
      # set timout alarm
      #
      signal.signal(signal.SIGALRM, handler)
      signal.alarm(TIMEOUT)
      #
      # try to read packet, otherwise set error message
      #
      try:
         get_i0_packet()
      except:
         sdata.set("I0 timeout")
      #
      # turn off alarm
      #
      signal.alarm(0)
   #
   # sleep to reduce OS load
   #
   time.sleep(0.001)
   parent.after_idle(idle,parent)

def output(byte):
   #
   # output a byte
   #
   ser.write(chr(byte))
   #time.sleep(.001) # byte spacing (if needed)


def get_i0_packet():
   #
   # read and display an I0 packet
   #
   sdata.set("reading ...")
   root.update()
   packet_length_offset = 2
   source_address_offset = 12
   destination_address_offset = 16
   source_port_offset = 20
   destination_port_offset = 22
   data_offset = 28
   #
   # find starting END
   #
   while 1:
      byte = ord(ser.read())
      if (byte == END):
         #
         # check whether beginning or end of packet
         #
         bute = ord(ser.read())
         if (byte == END):
            #
            # was end of packet, read next char
            #
            byte = ord(ser.read())
         break
   #
   # read until closing END
   #
   packet = []
   while 1:
      #
      # do SLIP mapping and save byte
      #
      if (byte == ESC):
         byte = ord(ser.read())
         if (byte == ESC_END):
            byte = END
         elif (byte == ESC_ESC):
            byte = ESC
         else:
            print "error: unknown ESC"
            break
      packet.append(byte)
      #
      # get next byte
      #
      byte = ord(ser.read())
      if (byte == END):
         source1.set(str(packet[source_address_offset+0-1]))
         source2.set(str(packet[source_address_offset+1-1]))
         source3.set(str(packet[source_address_offset+2-1]))
         source4.set(str(packet[source_address_offset+3-1]))
         dest1.set(str(packet[destination_address_offset+0-1]))
         dest2.set(str(packet[destination_address_offset+1-1]))
         dest3.set(str(packet[destination_address_offset+2-1]))
         dest4.set(str(packet[destination_address_offset+3-1]))
         sourceport.set(str(256*packet[source_port_offset+0-1]+packet[source_port_offset+1-1]))
         destport.set(str(256*packet[destination_port_offset+0-1]+packet[destination_port_offset+1-1]))
         packet_length = 256*packet[packet_length_offset+0-1]+packet[packet_length_offset+1-1]
         data = join(map(chr,packet[(data_offset-1):(data_offset+packet_length)]),sep="")
         sdata.set(data)
         return

def put_i0_packet():
   #
   # send I0 packet
   #
   ip_header_size = 20
   udp_header_size = 8
   outgoing_data_size = 10
   # ip_header_size_before_checksum = 10
   # ip_header_size_after_checksum = 8
   # outgoing_packet_size = ip_header_size + udp_header_size + outgoing_data_size
   # outgoing_start = RAMSTART
   # outgoing_source_address = outgoing_start + 12
   # outgoing_destination_address = outgoing_start + 16
   # outgoing_data = outgoing_start + ip_header_size + udp_header_size
   #
   # IP
   #
   packet = []
   packet.append(0x45) # version = 4 (4 bits), header length = 5 32-bit words (4 bits)
   packet.append(0) # type of service
   packet.append(high(ip_header_size + udp_header_size + outgoing_data_size)) # packet length
   packet.append(low(ip_header_size + udp_header_size + outgoing_data_size)) # packet length
   packet.append(0) # identification (high byte)
   packet.append(0) # identification (low byte)
   packet.append(0) # flag (3 bits), fragment offset (13 bits) (high byte)
   packet.append(0) # flag (3 bits), fragment offset (13 bits) (low byte)
   packet.append(255) # time to live
   packet.append(17) # protocol = 17 for UDP
   packet.append(0) # header checksum (to be calculated)
   packet.append(0) # header checksum (to be calculated)
   packet.append(int(source1.get())) # source address byte 1
   packet.append(int(source2.get())) # source address byte 2
   packet.append(int(source3.get())) # source address byte 3
   packet.append(int(source4.get())) # source address byte 4
   packet.append(int(dest1.get())) # destination address byte 1
   packet.append(int(dest2.get())) # destination address byte 2
   packet.append(int(dest3.get())) # destination address byte 3
   packet.append(int(dest4.get())) # destination address byte 4
   #
   # UDP
   #
   packet.append(high(int(sourceport.get()))) # source port
   packet.append(low(int(sourceport.get()))) # source port
   packet.append(high(int(destport.get()))) # destination port
   packet.append(low(int(destport.get()))) # destination port
   packet.append(high(udp_header_size + outgoing_data_size)) # payload length
   packet.append(low(udp_header_size + outgoing_data_size)) # payload length
   packet.append(0) # payload checksum (not used)
   packet.append(0) # payload checksum (not used)
   #
   # data
   #
   packet.append(int(databyte0.get())) #HW Counter
   packet.append(int(databyte1.get())) #Command_Travel0
   packet.append(int(databyte2.get())) #Command_Travel1
   packet.append(int(databyte3.get())) #Duration0
   packet.append(int(databyte4.get())) #Duration1
   packet.append(int(databyte5.get())) #Configuration

   #
   # send the packet with SLIP mapping and framing
   #
   output(END)
   for byte in range(len(packet)):
      if (packet[byte] == END):
         output(ESC)
         output(ESC_END)
      elif (packet[byte] == ESC):
         output(ESC)
         output(ESC_ESC)
      else:
         output(packet[byte])
   output(END)
   #
   # pause for bridge after sending packet
   #
   time.sleep(.05)

def sendconfigpacket():
	dest1.set(xaxisip1.get())
	dest2.set(xaxisip2.get())
	dest3.set(xaxisip3.get())
	dest4.set(xaxisip4.get())
	destport.set(xdataport.get())
	databyte0.set(xdatabyte0.get())
	databyte1.set(xdatabyte1.get())
	databyte2.set(xdatabyte2.get())
	databyte3.set(xdatabyte3.get())
	databyte4.set(xdatabyte4.get())
	databyte5.set(xdatabyte5.get())
	put_i0_packet()


	dest1.set(yaxisip1.get())
	dest2.set(yaxisip2.get())
	dest3.set(yaxisip3.get())
	dest4.set(yaxisip4.get())
	destport.set(ydataport.get())
	databyte0.set(ydatabyte0.get())
	databyte1.set(ydatabyte1.get())
	databyte2.set(ydatabyte2.get())
	databyte3.set(ydatabyte3.get())
	databyte4.set(ydatabyte4.get())
	databyte5.set(ydatabyte5.get())
	put_i0_packet()


	dest1.set(zaxisip1.get())
	dest2.set(zaxisip2.get())
	dest3.set(zaxisip3.get())
	dest4.set(zaxisip4.get())
	destport.set(zdataport.get())
	databyte0.set(zdatabyte0.get())
	databyte1.set(zdatabyte1.get())
	databyte2.set(zdatabyte2.get())
	databyte3.set(zdatabyte3.get())
	databyte4.set(zdatabyte4.get())
	databyte5.set(zdatabyte5.get())
	put_i0_packet()


def sendsyncpacket():
	dest1.set(xaxisip1.get())
	dest2.set(xaxisip2.get())
	dest3.set(xaxisip3.get())
	dest4.set(xaxisip4.get())
	destport.set(727)
	sdata.set("")
	put_i0_packet()

#Grabs source IP address into the X Axis IP Address
def grabxip():
	xip1 = source1.get()
	xip2 = source2.get()
	xip3 = source3.get()
	xip4 = source4.get()
	xaxisip1.set(xip1)
	xaxisip2.set(xip2)
	xaxisip3.set(xip3)
	xaxisip4.set(xip4)
	
#Grabs source IP address into the Y Axis IP Address
def grabyip():
	yip1 = source1.get()
	yip2 = source2.get()
	yip3 = source3.get()
	yip4 = source4.get()
	yaxisip1.set(yip1)
	yaxisip2.set(yip2)
	yaxisip3.set(yip3)
	yaxisip4.set(yip4)

#Grabs source IP address into the Z Axis IP Address
def grabzip():
	zip1 = source1.get()
	zip2 = source2.get()
	zip3 = source3.get()
	zip4 = source4.get()
	zaxisip1.set(zip1)
	zaxisip2.set(zip2)
	zaxisip3.set(zip3)
	zaxisip4.set(zip4)

#This function called by lines in the VMC
def move( x = None, y = None, z = None, rate = 1):

    #real machine and controller parameters
    numberofaxes = 3
    clockspeed = [20000000, 20000000, 20000000]
    prescalar  = [1024, 1024, 1024]
    stepsize = [0.007, 0.007, 0.007]
    softwarecountersizes = [2**16-1, 2**16-1, 2**16-1]
    hardwarecountersizes = [2**8-1, 2**8-1, 2**8-1]

    ending_buffer = 0.1 #extra time to give nodes to finish move

        
    
    #import command and store in moveto array
    xposition = float(vmxposition.get())
    yposition = float(vmyposition.get())
    zposition = float(vmzposition.get())
    if x == None:
        x = xposition
    if y == None:
        y = yposition
    if z == None:
        z = zposition
    
    #get move delta
    machineposition = numpy.array([xposition, yposition, zposition])
    movecommand = numpy.array([x,y,z])
    feedspeed = rate

    traverse = movecommand - machineposition


    #IMPORTANT... THIS VERSION OF STEPGEN ONLY WORKS PROPERLY WITH 1 AND 2 AXIS SUMULTANEOUS MOVEMENT
    #THIS IMPLIES THAT ERROR MAPPING WON'T WORK YET
    
    rate = rate / 60.        #now it's in inches per second
    nomove = 0        #this flag gets set if a no-move condition is triggered
    distancesquaredsum = 0

    #Configure VM Variables
    clockspeeds = numpy.zeros(numberofaxes)
    prescalars = numpy.zeros(numberofaxes)
    stepsizes = numpy.zeros(numberofaxes)
    softwarecountersize = numpy.zeros(numberofaxes)
    hardwarecountersize = numpy.zeros(numberofaxes)
    
    for i in range(numberofaxes):
        distancesquaredsum = distancesquaredsum + (traverse[i]*traverse[i])
        clockspeeds[i] = clockspeed[i]
        prescalars[i] = prescalar[i]
        stepsizes[i] = stepsize[i]
        softwarecountersize[i] = softwarecountersizes[i]
        hardwarecountersize[i] = hardwarecountersizes[i]


    distance = math.sqrt(distancesquaredsum)    #Euclidean distance of move
    movetime = distance / rate                      #Duration of move in seconds
    print "MOVETIME", movetime
    #print traverse
    #drawer.goto(traverse[0], traverse[1], 'stepgen', rate=rate, movetime=movetime)

    scaledclock = clockspeeds / prescalars      #Motor controller clock speeds (ticks / second)
    
    steps = traverse / stepsizes        #number of steps needed
    steps = numpy.round(steps)           #convert steps into integers
    absteps = numpy.abs(steps)          #absolute step values
    

    movingaxes = numpy.nonzero(steps)[0]   #isolates only the moving axes
    movingsteps = numpy.take(steps, movingaxes)
    absmovingsteps = numpy.take(absteps, movingaxes)
    counter_durations = numpy.zeros(len(steps))

    directions = movingsteps/absmovingsteps        #-1 = reverse, 1 = forward

    if len(movingsteps)>2:
        print "3+ AXIS SIMULTANEOUS MOVES NOT SUPPORTED BY THIS STEP GENERATOR"

    if len(movingsteps) !=0:        
        nomove = 0
        
        if len(movingsteps) == 2:
            gcd = GCD(absmovingsteps[0], absmovingsteps[1])
            gcd_movingsteps = absmovingsteps / gcd
            
            # flip gcd_movingsteps
            moving_durations = gcd_movingsteps[::-1] 
            overall_duration = absmovingsteps[0]*moving_durations[0]
            
        else: # len == 1
            moving_durations = [1]
            overall_duration = absmovingsteps[0]
            
        maxsteps = max(absmovingsteps)
        stepinterval = overall_duration / absmovingsteps

        softwarecounterrange = (softwarecountersize / maxsteps).astype(int)
        hardwarecounterrange = numpy.ones(numberofaxes)*min(hardwarecountersize)

        # movetime / number of sw counter ticks = time per click
        neededtimeperpulse = movetime / overall_duration

        prehwcounterpulsetime = prescalars / clockspeeds

        hardwarecounterstemp = numpy.ceil(neededtimeperpulse / prehwcounterpulsetime)
        hardwarecountersovfl = numpy.ceil(hardwarecounterstemp / hardwarecounterrange)

    
        softwarecounters = numpy.min([softwarecounterrange, hardwarecountersovfl], axis = 0)
        hardwarecounters = numpy.ceil(neededtimeperpulse/(prehwcounterpulsetime*softwarecounters))

        
        durations = numpy.zeros(numberofaxes)
        numpy.put(durations, movingaxes, stepinterval)
        
        numpy.put(counter_durations, movingaxes, moving_durations)

        counter_durations = counter_durations * softwarecounters
        overall_duration = overall_duration * softwarecounters[0]   #this is a hack for now
        
        move_times = hardwarecounters * prescalar * counter_durations * absteps / clockspeed

        max_move_times = max(move_times)

        xdatabyte0.set(int(hardwarecounters[0]))
        ydatabyte0.set(int(hardwarecounters[1]))
        zdatabyte0.set(int(hardwarecounters[2]))
        
        xdatabyte1.set(low(int(counter_durations[0])))
        ydatabyte1.set(low(int(counter_durations[1])))
        zdatabyte1.set(low(int(counter_durations[2])))
        
        xdatabyte2.set(high(int(counter_durations[0])))
        ydatabyte2.set(high(int(counter_durations[1])))
        zdatabyte2.set(high(int(counter_durations[2])))

        xdatabyte3.set(low(int(absteps[0])))
        ydatabyte3.set(low(int(absteps[1])))
        zdatabyte3.set(low(int(absteps[2])))

        xdatabyte4.set(high(int(absteps[0])))
        ydatabyte4.set(high(int(absteps[1])))
        zdatabyte4.set(high(int(absteps[2])))
        
        directions2 = numpy.zeros(numberofaxes)
        numpy.put(directions2, movingaxes, directions)        
        directions3 = numpy.copy(directions2)

        for i in range(numberofaxes):
            if directions3[i] == -1:
                directions3[i] = 0
        xdatabyte5.set(int(directions3[0]))
        ydatabyte5.set(int(directions3[1]))
        zdatabyte5.set(int(directions3[2]))

        #SIMULATE MOVE
        xstepstaken = float(xdatabyte3.get()) + (256*float(xdatabyte4.get()))
        ystepstaken = float(ydatabyte3.get()) + (256*float(ydatabyte4.get()))
        zstepstaken = float(zdatabyte3.get()) + (256*float(zdatabyte4.get()))

        xtravel = xstepstaken * stepsize[0] * float(directions2[0])
        ytravel = ystepstaken * stepsize[1] * float(directions2[1])
        ztravel = zstepstaken * stepsize[2] * float(directions2[2])


        vmxposition.set(xposition+xtravel)
        vmyposition.set(yposition+ytravel)
        vmzposition.set(zposition+ztravel)
        
        sendconfigpacket()
        sendsyncpacket()
        
        print (max_move_times)        
        time.sleep (max_move_times + ending_buffer)
    


def run():
    linenumber = 0
    vmcfile = open(vmfile.get(),'r')
    for line in vmcfile.readlines():
        linenumber = linenumber + 1
        vmlinenumber.set(linenumber)
        line = line.strip()
        exec(line)
        
#
# get command line arguments
#
if (len(sys.argv) != 3):
   print "command line syntax: thtp serial_port serial_speed"
   sys.exit()
serial_port = sys.argv[1]
serial_speed = int(sys.argv[2])

#
# GUI
#

root = Tk()
root.title('MAS.961 Virtual Machine')

# Builds "i0 Network Traffic" label
networktraffic = Frame(root)
Label(networktraffic, text = "i0 Network Traffic: ").pack(side="left")
networktraffic.pack()
#

# Builds source address fields
sourceframe = Frame(root)
Label(sourceframe,text="source address: ").pack(side="left")
source1 = StringVar()
wsource1 = Entry(sourceframe, width=3, textvariable=source1)
wsource1.pack(side="left")

Label(sourceframe,text=".").pack(side="left")
source2 = StringVar()
wsource2 = Entry(sourceframe, width=3, textvariable=source2)
wsource2.pack(side="left")

Label(sourceframe,text=".").pack(side="left")
source3 = StringVar()
wsource3 = Entry(sourceframe, width=3, textvariable=source3)
wsource3.pack(side="left")

Label(sourceframe,text=".").pack(side="left")
source4 = StringVar()
wsource4 = Entry(sourceframe, width=3, textvariable=source4)
wsource4.pack(side="left")
sourceframe.pack()

# Builds destination address fields
destframe = Frame(root)
Label(destframe,text="destination address: ").pack(side="left")
dest1 = StringVar()
wdest1 = Entry(destframe, width=3, textvariable=dest1)
wdest1.pack(side="left")

Label(destframe,text=".").pack(side="left")
dest2 = StringVar()
wdest2 = Entry(destframe, width=3, textvariable=dest2)
wdest2.pack(side="left")

Label(destframe,text=".").pack(side="left")
dest3 = StringVar()
wdest3 = Entry(destframe, width=3, textvariable=dest3)
wdest3.pack(side="left")

Label(destframe,text=".").pack(side="left")
dest4 = StringVar()
wdest4 = Entry(destframe, width=3, textvariable=dest4)
wdest4.pack(side="left")
destframe.pack()

# builds port fields
portframe = Frame(root)
Label(portframe,text="source port: ").pack(side="left")
sourceport = StringVar()
wsourceport = Entry(portframe, width=4, textvariable=sourceport)
wsourceport.pack(side="left")

Label(portframe,text="  destination port: ").pack(side="left")
destport = StringVar()
wdestport = Entry(portframe, width=4, textvariable=destport)
wdestport.pack(side="left")
portframe.pack()

# builds data in field
dataframe = Frame(root)
Label(dataframe,text="data in: ").pack(side="left")
sdata = StringVar()
wdata = Entry(dataframe, width=30, textvariable=sdata)
wdata.pack(side="left")
dataframe.pack()

# builds data out field
dataoutframe = Frame(root)
Label(dataoutframe, text ="command out: ").pack(side="left")
databyte0 = StringVar()
databyte1 = StringVar()
databyte2 = StringVar()
databyte3 = StringVar()
databyte4 = StringVar()
databyte5 = StringVar()
wdatabyte0 = Entry(dataoutframe, width = 3, textvariable = databyte0)
wdatabyte0.pack(side = "left")
wdatabyte1 = Entry(dataoutframe, width = 3, textvariable = databyte1)
wdatabyte1.pack(side = "left")
wdatabyte2 = Entry(dataoutframe, width = 3, textvariable = databyte2)
wdatabyte2.pack(side = "left")
wdatabyte3 = Entry(dataoutframe, width = 3, textvariable = databyte3)
wdatabyte3.pack(side = "left")
wdatabyte4 = Entry(dataoutframe, width = 3, textvariable = databyte4)
wdatabyte4.pack(side = "left")
wdatabyte5 = Entry(dataoutframe, width = 3, textvariable = databyte5)
wdatabyte5.pack(side = "left")
dataoutframe.pack()

# Builds spacer
sectionspacer1 = Frame(root)
Label(sectionspacer1, text = "_________________________________________").pack(side="left")
sectionspacer1.pack()
#

# builds Virtual Machine Config label
vmconfig = Frame(root)
Label(vmconfig, text="Virtual Machine Configuration").pack(side="left")
vmconfig.pack()

# builds X Axis IP address field
xaxisframe = Frame(root)

Label(xaxisframe, text="X Axis IP: ").pack(side="left")
xaxisip1 = StringVar()
wxaxisip1 = Entry(xaxisframe, width=3, textvariable = xaxisip1)
wxaxisip1.pack(side = "left")

Label(xaxisframe,text=".").pack(side="left")
xaxisip2 = StringVar()
wxaxisip2 = Entry(xaxisframe, width=3, textvariable = xaxisip2)
wxaxisip2.pack(side = "left")

Label(xaxisframe,text=".").pack(side="left")
xaxisip3 = StringVar()
wxaxisip3 = Entry(xaxisframe, width=3, textvariable = xaxisip3)
wxaxisip3.pack(side = "left")

Label(xaxisframe,text=".").pack(side="left")
xaxisip4 = StringVar()
wxaxisip4 = Entry(xaxisframe, width=3, textvariable = xaxisip4)
wxaxisip4.pack(side = "left")

wgrabx = Button(xaxisframe, text="grab",command=grabxip)
wgrabx.pack(side = "left")

xaxisframe.pack()

# builds Y axis IP address field
yaxisframe = Frame(root)

Label(yaxisframe, text="Y Axis IP: ").pack(side="left")
yaxisip1 = StringVar()
wyaxisip1 = Entry(yaxisframe, width=3, textvariable = yaxisip1)
wyaxisip1.pack(side = "left")

Label(yaxisframe,text=".").pack(side="left")
yaxisip2 = StringVar()
wyaxisip2 = Entry(yaxisframe, width=3, textvariable = yaxisip2)
wyaxisip2.pack(side = "left")

Label(yaxisframe,text=".").pack(side="left")
yaxisip3 = StringVar()
wyaxisip3 = Entry(yaxisframe, width=3, textvariable = yaxisip3)
wyaxisip3.pack(side = "left")

Label(yaxisframe,text=".").pack(side="left")
yaxisip4 = StringVar()
wyaxisip4 = Entry(yaxisframe, width=3, textvariable = yaxisip4)
wyaxisip4.pack(side = "left")

wgraby = Button(yaxisframe, text="grab",command=grabyip)
wgraby.pack(side = "left")

yaxisframe.pack()

# builds Z axis IP address field
zaxisframe = Frame(root)

Label(zaxisframe, text="Z Axis IP: ").pack(side="left")
zaxisip1 = StringVar()
wzaxisip1 = Entry(zaxisframe, width=3, textvariable = zaxisip1)
wzaxisip1.pack(side = "left")

Label(zaxisframe,text=".").pack(side="left")
zaxisip2 = StringVar()
wzaxisip2 = Entry(zaxisframe, width=3, textvariable = zaxisip2)
wzaxisip2.pack(side = "left")

Label(zaxisframe,text=".").pack(side="left")
zaxisip3 = StringVar()
wzaxisip3 = Entry(zaxisframe, width=3, textvariable = zaxisip3)
wzaxisip3.pack(side = "left")

Label(zaxisframe,text=".").pack(side="left")
zaxisip4 = StringVar()
wzaxisip4 = Entry(zaxisframe, width=3, textvariable = zaxisip4)
wzaxisip4.pack(side = "left")

wgrabz = Button(zaxisframe, text="grab",command=grabzip)
wgrabz.pack(side = "left")

zaxisframe.pack()

# Builds spacer
sectionspacer2 = Frame(root)
Label(sectionspacer2, text = "_________________________________________").pack(side="left")
sectionspacer2.pack()
#

# builds Virtual Machine Output label
vmconfig = Frame(root)
Label(vmconfig, text="Virtual Machine Output").pack(side="left")
vmconfig.pack()


# builds X data out field
xdataoutframe = Frame(root)
Label(xdataoutframe, text ="X port: ").pack(side="left")
xdataport = StringVar()
wxdataport = Entry(xdataoutframe, width = 4, textvariable = xdataport)
wxdataport.pack(side = "left")
Label(xdataoutframe, text ="X command: ").pack(side="left")
xdatabyte0 = StringVar()
xdatabyte1 = StringVar()
xdatabyte2 = StringVar()
xdatabyte3 = StringVar()
xdatabyte4 = StringVar()
xdatabyte5 = StringVar()
wxdatabyte0 = Entry(xdataoutframe, width = 3, textvariable = xdatabyte0)
wxdatabyte0.pack(side = "left")
wxdatabyte1 = Entry(xdataoutframe, width = 3, textvariable = xdatabyte1)
wxdatabyte1.pack(side = "left")
wxdatabyte2 = Entry(xdataoutframe, width = 3, textvariable = xdatabyte2)
wxdatabyte2.pack(side = "left")
wxdatabyte3 = Entry(xdataoutframe, width = 3, textvariable = xdatabyte3)
wxdatabyte3.pack(side = "left")
wxdatabyte4 = Entry(xdataoutframe, width = 3, textvariable = xdatabyte4)
wxdatabyte4.pack(side = "left")
wxdatabyte5 = Entry(xdataoutframe, width = 3, textvariable = xdatabyte5)
wxdatabyte5.pack(side = "left")
xdataoutframe.pack()

# builds Y data out field
ydataoutframe = Frame(root)
Label(ydataoutframe, text ="Y port: ").pack(side="left")
ydataport = StringVar()
wydataport = Entry(ydataoutframe, width = 4, textvariable = ydataport)
wydataport.pack(side = "left")
Label(ydataoutframe, text ="Y command: ").pack(side="left")
ydatabyte0 = StringVar()
ydatabyte1 = StringVar()
ydatabyte2 = StringVar()
ydatabyte3 = StringVar()
ydatabyte4 = StringVar()
ydatabyte5 = StringVar()
wydatabyte0 = Entry(ydataoutframe, width = 3, textvariable = ydatabyte0)
wydatabyte0.pack(side = "left")
wydatabyte1 = Entry(ydataoutframe, width = 3, textvariable = ydatabyte1)
wydatabyte1.pack(side = "left")
wydatabyte2 = Entry(ydataoutframe, width = 3, textvariable = ydatabyte2)
wydatabyte2.pack(side = "left")
wydatabyte3 = Entry(ydataoutframe, width = 3, textvariable = ydatabyte3)
wydatabyte3.pack(side = "left")
wydatabyte4 = Entry(ydataoutframe, width = 3, textvariable = ydatabyte4)
wydatabyte4.pack(side = "left")
wydatabyte5 = Entry(ydataoutframe, width = 3, textvariable = ydatabyte5)
wydatabyte5.pack(side = "left")
ydataoutframe.pack()

# builds Z data out field
zdataoutframe = Frame(root)
Label(zdataoutframe, text ="Z port: ").pack(side="left")
zdataport = StringVar()
wzdataport = Entry(zdataoutframe, width = 4, textvariable = zdataport)
wzdataport.pack(side = "left")
Label(zdataoutframe, text ="Z command: ").pack(side="left")
zdatabyte0 = StringVar()
zdatabyte1 = StringVar()
zdatabyte2 = StringVar()
zdatabyte3 = StringVar()
zdatabyte4 = StringVar()
zdatabyte5 = StringVar()
wzdatabyte0 = Entry(zdataoutframe, width = 3, textvariable = zdatabyte0)
wzdatabyte0.pack(side = "left")
wzdatabyte1 = Entry(zdataoutframe, width = 3, textvariable = zdatabyte1)
wzdatabyte1.pack(side = "left")
wzdatabyte2 = Entry(zdataoutframe, width = 3, textvariable = zdatabyte2)
wzdatabyte2.pack(side = "left")
wzdatabyte3 = Entry(zdataoutframe, width = 3, textvariable = zdatabyte3)
wzdatabyte3.pack(side = "left")
wzdatabyte4 = Entry(zdataoutframe, width = 3, textvariable = zdatabyte4)
wzdatabyte4.pack(side = "left")
wzdatabyte5 = Entry(zdataoutframe, width = 3, textvariable = zdatabyte5)
wzdatabyte5.pack(side = "left")
zdataoutframe.pack()



# builds a button for initial data sending test

sendpacketframe = Frame(root)

wsendconfigpacket = Button(sendpacketframe, text = "send config packet", command = sendconfigpacket)
wsendconfigpacket.pack(side = "left")
wsendsyncpacket = Button(sendpacketframe, text = "send sync packet", command = sendsyncpacket)
wsendsyncpacket.pack(side = "left")

sendpacketframe.pack()

# Builds spacer
sectionspacer2 = Frame(root)
Label(sectionspacer2, text = "_________________________________________").pack(side="left")
sectionspacer2.pack()
#

# builds the Virtual Machine Control Frame Label

vmcontrolframelabel = Frame(root)
Label(vmcontrolframelabel, text = "Virtual Machine Control").pack(side="left")
vmcontrolframelabel.pack()

# builds the Virtual Machine Position Label

vmpositionframe = Frame(root)
Label(vmpositionframe, text = "POSITION:   X").pack(side="left")
vmxposition = StringVar()
wvmxposition = Entry(vmpositionframe, width = 6, textvariable = vmxposition)
wvmxposition.pack(side = "left")
Label(vmpositionframe, text = " Y").pack(side="left")
vmyposition = StringVar()
wvmyposition = Entry(vmpositionframe, width = 6, textvariable = vmyposition)
wvmyposition.pack(side = "left")
Label(vmpositionframe, text = " Z").pack(side="left")
vmzposition = StringVar()
wvmzposition = Entry(vmpositionframe, width = 6, textvariable = vmzposition)
wvmzposition.pack(side = "left")
vmpositionframe.pack()

# builds the Status Bar

vmstatusframe = Frame(root)
Label(vmstatusframe, text = "STATUS: ").pack(side = "left")
vmstatus = StringVar()
wvmstatus = Entry(vmstatusframe, width = 40, textvariable = vmstatus)
wvmstatus.pack(side = "left")
vmstatusframe.pack()

# builds the File Bar
vmfileframe = Frame(root)
Label(vmfileframe, text = "FILE: ").pack(side = "left")
vmfile = StringVar()
wvmfile = Entry(vmfileframe, width = 30, textvariable = vmfile)
wvmfile.pack(side = "left")
vmfileframe.pack()

# builds the Run Bar
vmrunframe = Frame(root)
Label(vmrunframe, text = "LINE: ").pack(side = "left")
vmlinenumber = StringVar()
wvmlinenumber = Entry(vmrunframe, width = 5, textvariable = vmlinenumber)
wvmlinenumber.pack(side = "left")
wvmrun = Button(vmrunframe, text = "RUN!", command = run)
wvmrun.pack(side = "left")
vmrunframe.pack()

# sets initial values for source IP address
source1.set(132)
source2.set(98)
source3.set(24)
source4.set(187)

#sets initial values for x, y, and z commands for testing

xdatabyte0.set(255)
xdatabyte1.set(10)
xdatabyte2.set(0)
xdatabyte3.set(50)
xdatabyte4.set(0)
xdatabyte5.set(0)
xdataport.set(890)

ydatabyte0.set(255)
ydatabyte1.set(10)
ydatabyte2.set(0)
ydatabyte3.set(50)
ydatabyte4.set(0)
ydatabyte5.set(0)
ydataport.set(890)

zdatabyte0.set(255)
zdatabyte1.set(10)
zdatabyte2.set(0)
zdatabyte3.set(50)
zdatabyte4.set(0)
zdatabyte5.set(0)
zdataport.set(890)

#sets initial machine position
vmxposition.set(0)
vmyposition.set(0)
vmzposition.set(0)

vmstatus.set("IDLE")

#
# open serial port
#
ser = serial.Serial(port=serial_port, baudrate=serial_speed)
ser.flushInput()


root.after(100,idle,root)
root.mainloop()
