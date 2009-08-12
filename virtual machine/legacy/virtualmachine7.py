# Virtual Machine
# Rapid Prototyping of Rapid Prototyping Machines
#
# Ilan E. Moyer
# for the MIT Center for Bits and Atoms
#
# 5/9/08
#

#------------IMPORTS-----------------------------------------------------------------------

import sys
import commands
import csv
import numpy
#import numarray
import time
import math
import serial

#-----------OBJECTS-----------------------------------------------------------------------

class computer(object):

    rml = 0
    movetable = 0
    feedmodetable = 0
    zup = 0
    tableindex = 0
    
    def loadrml(self):
        try:
            rmlfile = sys.argv[1] #stores filename of source RML file into x
            rmlfile = open(rmlfile, mode = 'r')   #opens RML file as object rmlfile
            rmlfile.seek(0,0)   #sets file pointer at beginning

            rmlparser = csv.reader(rmlfile, delimiter=';', quoting = csv.QUOTE_ALL)     #parses rmlfile as a semi-colon delimited file
            rml = rmlparser.next()
            self.rml = rml
            rmlfile.close()
        except IndexError:
            print "Please enter name of RML file following virtualmachine.py"
        
    def parserml(self):
        zup = 0 #Initialize RML z axis up position
        zdown = 0 #Initialize RML z axis down position
        currentx = 0 #Initialize current x axis position
        currenty = 0 #Initialize current y axis position
        movetable = numpy.array([[1,1,1],[1,1,1]],float)  #table of xyz moves in x,y,z format
        currentmove = numpy.array([[1,1,1],[1,1,1]],float)    #current move in x,y,z format

        feedmodetable = numpy.array([[1],[1]],float) #table of feed modes (0 = plunge, 1 = retract, 2 = downfeed, 3 = upfeed)
        feedmode = {'plunge':0, 'retract':1, 'downfeed':2, 'upfeed':3}
        
        currentfeed = numpy.array([[1],[1]],float) #current feedrate in in/min                       

        rmllength = len(self.rml)

        for h in xrange(rmllength):
            commander = 0
            firstterm = 0
            secondterm = 0
            currententry = self.rml[h]
            entrylength = len(currententry)
            for i in xrange(entrylength):
                j = i+2
                if currententry[i:j]=="PA": #no idea what the hell this is
                    commander = "PA"
                elif currententry[i:j] == "VS": #xy travel speed
                    commander = "VS"
                    firstterm = j
                    xyspeed = currententry[firstterm:entrylength]
                    xyspeed = float(xyspeed)
                elif currententry[i:j]== "VZ": #z travel speed
                    commander = "VZ"
                    firstterm = j
                    zspeed = currententry[firstterm:entrylength]
                    zspeed = float(zspeed)
                elif currententry[i:j] == "PZ":
                    commander = "PZ"
                    firstterm = j
                elif currententry[i:j] == "PU":
                    commander = "PU"
                    firstterm = j
                elif currententry[i:j] == "PD":
                    commander = "PD"
                    firstterm = j
                elif currententry[i] == ",":
                    secondterm = i
                    
            if commander == "PZ": #Set Z pen positions in down, up format
                zdown = currententry[firstterm:secondterm]
                zup = currententry[secondterm+1:entrylength]
                zdown = float(zdown)
                zup = float(zup)

            if commander == "PD": #Pen down RML command.
                currentmove[0,0] = currentx
                currentmove[0,1] = currenty
                currentmove[0,2] = zdown
                currentfeed[0,0] = feedmode.get('plunge')
                                
                currentx = currententry[firstterm:secondterm]
                currenty = currententry[secondterm+1:entrylength]
                currentx = float(currentx)
                currenty = float(currenty)
                                
                currentmove[1,0] = currentx
                currentmove[1,1] = currenty
                currentmove[1,2] = zdown
                currentfeed[1,0] = feedmode.get('downfeed')
                                
                movetable = numpy.concatenate((movetable,currentmove),0)
                feedmodetable = numpy.concatenate((feedmodetable,currentfeed),0)


            if commander == "PU": #Pen up RML command.
                currentmove[0,0] = currentx
                currentmove[0,1] = currenty
                currentmove[0,2] = zup
                currentfeed[0,0] = feedmode.get('retract')

                currentx = currententry[firstterm:secondterm]
                currenty = currententry[secondterm+1:entrylength]                   
                currentx = float(currentx)
                currenty = float(currenty)
                                
                currentmove[1,0] = currentx
                currentmove[1,1] = currenty
                currentmove[1,2] = zup
                currentfeed[1,0] = feedmode.get('upfeed')
                                
                movetable = numpy.concatenate((movetable,currentmove),0)
                feedmodetable = numpy.concatenate((feedmodetable,currentfeed),0)
                                
        movetable = movetable[3::,:]    #removes blank seed
        feedmodetable = feedmodetable[3::,:]
                
        #movetable[1,2]=zdown          #sets the height of the initial retract move

        movetable = movetable / 1000    #converts movetable to units of inches
                                        # had been in modela units of 0.001 in
        self.movetable=movetable
        self.feedmodetable=feedmodetable
        self.zup = zup

class motorcontroller (object):
    clockspeed = 0 #clock speed in Hz
    prescalar = 0 #internal prescalar
    counterrate = 0 #counter rate
    stepsize = 0 #travel per step in inches
    direction = 0 # 0 = off, 1 = forward, 2 = reverse
    rate = 0 #next move time between steps (in prescaled clock steps)
    softwarecountersize = 0
    hardwarecountersize = 0
    duration = 0 #next move total duration (in prescaled clock steps)
    softwarecounter = 0 
    hardwarecounter = 0

    
    
    
    
class guide(object):
        
    vector = [0,0,0]    #establishes vector of motion
        
    def move(self,s):
        vectorarray = numpy.array(self.vector)
        travel = vectorarray*s
        return travel

class transmission(object):
    ratio = 0   #transmission ratio (in/rad)

class motor(object):
    ratio = 0   #conversion ratio (rad/step)

    
class machine(object):
    
    numberofaxes = 3
    
    dynamicrangeresolution = 6000   #this sets the minimum slope ratio resolution
    maxcountersize = dynamicrangeresolution**2    #this is the max counter capacity needed based on calculations in notebook from 1/26/09
    softwarecounternumber = math.ceil(math.log(maxcountersize,2)/8)     #max number of bytes needed
    
    guides = range(numberofaxes)
    motorcontrollers = range(numberofaxes)
    
    for i in range(numberofaxes):
        guides[i]=guide()
        motorcontrollers[i] = motorcontroller()
        motorcontrollers[i].softwarecounter = numpy.zeros(softwarecounternumber)
        
    position = numpy.zeros(numberofaxes) #current machine position (inches).
        
    guides[0].vector = [1,0,0]
    guides[1].vector = [0,1,0]
    guides[2].vector = [0,0,1]

    motorcontrollers[0].clockspeed = 20000000
    motorcontrollers[1].clockspeed = 20000000
    motorcontrollers[2].clockspeed = 20000000

    motorcontrollers[0].prescalar = 1024
    motorcontrollers[1].prescalar = 1024
    motorcontrollers[2].prescalar = 1024

    motorcontrollers[0].stepsize = 0.014
    motorcontrollers[1].stepsize = 0.014
    motorcontrollers[2].stepsize = 0.014

    motorcontrollers[0].softwarecountersize = 2**16-1
    motorcontrollers[1].softwarecountersize = 2**16-1
    motorcontrollers[2].softwarecountersize = 2**16-1

    motorcontrollers[0].hardwarecountersize = 2**8-1
    motorcontrollers[1].hardwarecountersize = 2**8-1
    motorcontrollers[2].hardwarecountersize = 2**8-1
    

    def move(self,commandmove):
        #this function defines how the virtual machine moves based on its configuration and perhaps additional sensor inputs.
        #the goal is to create a model of the the machine which can be used in a virtual feedback loop by the controller.
        returnmove = numpy.zeros(self.numberofaxes)
        for i in range(self.numberofaxes):
            returnmove=returnmove + self.guides[i].move(commandmove[i])
        return returnmove
            

class controller(object):

    movtol = 0.0001     #error tolerance for positioning axes (inches)
    
    def movegen(self, moveto):

        error = self.movtol*2*numpy.ones(len(moveto))       #ensures that error always starts out larger than the tolerance
        position = virtualmachine.position                     #copies machine position to hypothetical position
        delta = numpy.zeros(len(moveto))
        
        while max(error)>self.movtol:
            error = moveto - position
            #print error[1]
            travel = virtualmachine.move(error)
            position=position + travel
            delta = delta + error
                
        return delta

    def stepgen (self, traverse, rate):             #note: rate in in/min
        #IMPORTANT... THIS VERSION OF STEPGEN ONLY WORKS PROPERLY WITH 1 AND 2 AXIS SUMULTANEOUS MOVEMENT
        #THIS IMPLIES THAT ERROR MAPPING WON'T WORK YET
        
        rate = rate / 60.        #now it's in inches per second
	nomove = 0		#this flag gets set if a no-move condition is triggered
        distancesquaredsum = 0
        clockspeeds = numpy.zeros(virtualmachine.numberofaxes)
        prescalars = numpy.zeros(virtualmachine.numberofaxes)
        stepsizes = numpy.zeros(virtualmachine.numberofaxes)
        softwarecountersize = numpy.zeros(virtualmachine.numberofaxes)
        hardwarecountersize = numpy.zeros(virtualmachine.numberofaxes)
        
                                  
        for i in range(virtualmachine.numberofaxes):
            distancesquaredsum = distancesquaredsum + (traverse[i]*traverse[i])
            clockspeeds[i] = virtualmachine.motorcontrollers[i].clockspeed
            prescalars[i] = virtualmachine.motorcontrollers[i].prescalar
            stepsizes[i] = virtualmachine.motorcontrollers[i].stepsize
            softwarecountersize[i] = virtualmachine.motorcontrollers[i].softwarecountersize
            hardwarecountersize[i] = virtualmachine.motorcontrollers[i].hardwarecountersize

            
        distance = math.sqrt(distancesquaredsum)    #Euclidean distance of move
        movetime = distance / rate                      #Duration of move in seconds
        scaledclock = clockspeeds / prescalars      #Motor controller clock speeds (ticks / second)
        
        steps = traverse / stepsizes        #number of steps needed
        steps = numpy.round(steps)           #convert steps into integers
        absteps = numpy.abs(steps)          #absolute step values
        

        movingaxes = numpy.nonzero(steps)[0]   #isolates only the moving axes
        movingsteps = numpy.take(steps, movingaxes)
        absmovingsteps = numpy.take(absteps, movingaxes)

        directions = movingsteps/absmovingsteps        #-1 = reverse, 1 = forward

        if len(movingsteps)>2:
            print "3+ AXIS SIMULTANEOUS MOVES NOT SUPPORTED BY THIS STEP GENERATOR"

	if len(movingsteps) !=0:        
		nomove = 0
        	maxsteps = max(absmovingsteps)
        	minsteps = min(absmovingsteps)

       		duration = minsteps*maxsteps

    
        	stepinterval = duration / absmovingsteps

        	softwarecounterrange = (softwarecountersize / maxsteps).astype(int)
        	hardwarecounterrange = numpy.ones(virtualmachine.numberofaxes)*min(hardwarecountersize)

        	neededtimeperpulse = movetime / duration

       		prehwcounterpulsetime = prescalars / clockspeeds

        	hardwarecounterstemp = numpy.ceil(neededtimeperpulse / prehwcounterpulsetime)
        	hardwarecountersovfl = numpy.ceil(hardwarecounterstemp / hardwarecounterrange)

        
        	softwarecounters = numpy.min([softwarecounterrange, hardwarecountersovfl], axis = 0)
        	hardwarecounters = numpy.ceil(neededtimeperpulse/(prehwcounterpulsetime*softwarecounters))


        	durations = numpy.zeros(virtualmachine.numberofaxes)
        	numpy.put(durations, movingaxes, stepinterval)

        	durations = durations * softwarecounters
        	duration = duration * softwarecounters[0]   #this is a hack for now
        
        	directions2 = numpy.zeros(virtualmachine.numberofaxes)
        	numpy.put(directions2, movingaxes, directions)

        	for i in range(virtualmachine.numberofaxes):
            		#print "axis ", i
            		virtualmachine.motorcontrollers[i].hardwarecounter = hardwarecounters[i]
            		#print "hardware ", hardwarecounters[i]
            		virtualmachine.motorcontrollers[i].softwarecounter = durations[i]
            		#print "software ", durations[i]
            		virtualmachine.motorcontrollers[i].duration = duration
            		#print "duration ", duration
            		if directions2[i] == -1:
                		directions2[i] = 2
            		virtualmachine.motorcontrollers[i].direction = directions2[i]
            		#print "direction ", directions2[i]
	else:
		nomove = 1
        	for i in range(virtualmachine.numberofaxes):
            		virtualmachine.motorcontrollers[i].hardwarecounter = 0
            		virtualmachine.motorcontrollers[i].softwarecounter = 0
            		virtualmachine.motorcontrollers[i].duration = 0
            		virtualmachine.motorcontrollers[i].direction = 0
            		#print "direction ", directions2[i]
        return nomove
        

    def xmit(self):
        #packet format:
        #byte0 - Start Byte
        #byte1 - hwcounter
        #byte2 - AXIS 1 Rate 0
        #byte3 - AXIS 1 Rate 1
        #byte4 - AXIS 2 Rate 0
        #byte5 - AXIS 2 Rate 1
        #byte6 - AXIS 3 Rate 0
        #byte7 - AXIS 3 Rate 1
        #byte8 - move duration 0
        #byte9 - move duration 1
        #byte10 - move duration 2
        #byte11 - move duration 3
        #byte12 - sync / motor direction (00ZrZfYrYfXrXf) where r is reverse and f is forward
        packetlength = 13
        xmitteraxes = virtualmachine.numberofaxes
        outgoing = numpy.zeros(packetlength)
        outgoing[0] = 255
        outgoing[1] = virtualmachine.motorcontrollers[0].hardwarecounter
        for i in range(xmitteraxes):
            outgoing[i*2+2] = int(virtualmachine.motorcontrollers[i].softwarecounter % 256)
            outgoing[i*2+3] = int(virtualmachine.motorcontrollers[i].softwarecounter / 256)
            outgoing[12] = outgoing[12] + virtualmachine.motorcontrollers[i].direction*(4**i)
            
        duration = virtualmachine.motorcontrollers[0].duration

        outgoingindex = 11
        remainder = duration
        for i in range(4):
            outgoing[11-i] = int(remainder / 256**(3-i))
            remainder = remainder % 256**(3-i)
        

        #print outgoing
        #print duration
        #print outgoing[8]+outgoing[9]*256+outgoing[10]*256**2+outgoing[11]*256**3
        
        #-------CONFIGURE AND OPEN SERIAL PORT-------------------------------
        portnumber = 3
        baudrate = 19200
        sertimeout = None #in seconds

        serport = serial.Serial(portnumber,baudrate, timeout=sertimeout)

        #-------SEND COMMAND-------------------------------------------------

        for i in range(len(outgoing)):
            serport.write(chr(outgoing[i]))
            a = serport.read()
            #print ord(a)


        serport.read()
        return outgoing


    def simmove(self, outgoing):
        
        xmitteraxes = virtualmachine.numberofaxes
        hardwarecounter = numpy.ones(xmitteraxes)*outgoing[1]
        softwarecounter = numpy.ones(xmitteraxes)
        stepsize = numpy.zeros(xmitteraxes)
        clockspeeds = numpy.zeros(xmitteraxes)
        prescalars = numpy.zeros(xmitteraxes)
        directions = numpy.zeros(xmitteraxes)
        steps = numpy.zeros(xmitteraxes)
        
        for i in range(3):
            softwarecounter[i]=outgoing[i*2+2]+outgoing[i*2+3]*256
            stepsize[i]=virtualmachine.motorcontrollers[i].stepsize
            clockspeeds[i] = virtualmachine.motorcontrollers[i].clockspeed
            prescalars[i] = virtualmachine.motorcontrollers[i].prescalar

        duration = outgoing[8]+outgoing[9]*256+outgoing[10]*256**2+outgoing[11]*256**3

        remainder = outgoing[12]
        for i in range(3):
            directions[2-i] = int(remainder / 4**(2-i))
            remainder = remainder % 4**(2-i)
            if directions[2-i] == 2:
                directions[2-i] = -1

        movingaxes = numpy.nonzero(directions)[0]   #isolates only the moving axes
        movingcounters = numpy.take(softwarecounter, movingaxes)

        movingsteps = numpy.floor(duration / movingcounters)
        numpy.put(steps, movingaxes, movingsteps)
        delta = steps * stepsize*directions

        deltasquared = delta**2
        distancesquared = numpy.sum(deltasquared)
        distance = math.sqrt(distancesquared)
        minclockspeed = min(clockspeeds)
        maxprescalar = max(prescalars)
        maxhardwarecounter = max(hardwarecounter)
        
        movetime =   maxprescalar * maxhardwarecounter * duration / minclockspeed

        minutes = movetime / 60 #time in minutes

        rate = distance / minutes

        movetime = movetime * 1.4


        return [delta, rate, movetime]
        

    


        

#moveto = numpy.array([0.5,0.5,0])
virtualmachine = machine()
machinecontroller = controller()
localcomputer = computer()
localcomputer.loadrml()
localcomputer.parserml()
#print localcomputer.movetable
#print localcomputer.feedmodetable

plungespeed = 4
retractspeed = 4
downfeedspeed = 32
upfeedspeed = 32

virtualmachine.position = localcomputer.movetable[0]	#this is a hack to prevent 3D motion and still be able to set tool height





for i in range(len(localcomputer.movetable)):
	print "RML Line: ", i
	moveto = localcomputer.movetable[i]
	feedmode = localcomputer.feedmodetable[i]
	if feedmode == 0:
		feedspeed = plungespeed
	if feedmode == 1:
		feedspeed = retractspeed
	if feedmode == 2:
		feedspeed = downfeedspeed
	if feedmode == 3:
		feedspeed = upfeedspeed
	print "commandedposition: ", moveto
	delta = machinecontroller.movegen(moveto)
	nomove = machinecontroller.stepgen(delta, feedspeed)
	if nomove != 1:
		outgoing = machinecontroller.xmit()
		[delta, rate, movetime] = machinecontroller.simmove(outgoing)
		print "MOVE COMPLETE"
	else:
		delta = numpy.zeros(virtualmachine.numberofaxes)
		print "NO MOVE HERE!"

	virtualmachine.position = virtualmachine.position + delta

	
	print "machine position: " , virtualmachine.position
	print ""

    

