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
import pygame

#-----------OBJECTS-----------------------------------------------------------------------

DEBUG_MODE = False

def GCD(a, b):
    while b != 0:
        (a, b) = (b, a%b)
    return a



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

    motorcontrollers[0].stepsize = 0.001
    motorcontrollers[1].stepsize = 0.001
    motorcontrollers[2].stepsize = 0.0005

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
            travel = virtualmachine.move(error)
            position=position + travel
            delta = delta + error
                
        return delta


    def stepgen_old (self, traverse, rate):             #note: rate in in/min
        #IMPORTANT... THIS VERSION OF STEPGEN ONLY WORKS PROPERLY WITH 1 AND 2 AXIS SUMULTANEOUS MOVEMENT
        #THIS IMPLIES THAT ERROR MAPPING WON'T WORK YET
        
        rate = rate / 60.        #now it's in inches per second
        nomove = 0        #this flag gets set if a no-move condition is triggered
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
        



    def stepgen(self, traverse, rate):             #note: rate in in/min
        #IMPORTANT... THIS VERSION OF STEPGEN ONLY WORKS PROPERLY WITH 1 AND 2 AXIS SUMULTANEOUS MOVEMENT
        #THIS IMPLIES THAT ERROR MAPPING WON'T WORK YET
        
        rate = rate / 60.        #now it's in inches per second
        nomove = 0        #this flag gets set if a no-move condition is triggered
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
            hardwarecounterrange = numpy.ones(virtualmachine.numberofaxes)*min(hardwarecountersize)
    
            # movetime / number of sw counter ticks = time per click
            neededtimeperpulse = movetime / overall_duration
    
            prehwcounterpulsetime = prescalars / clockspeeds
    
            hardwarecounterstemp = numpy.ceil(neededtimeperpulse / prehwcounterpulsetime)
            hardwarecountersovfl = numpy.ceil(hardwarecounterstemp / hardwarecounterrange)
    
        
            softwarecounters = numpy.min([softwarecounterrange, hardwarecountersovfl], axis = 0)
            hardwarecounters = numpy.ceil(neededtimeperpulse/(prehwcounterpulsetime*softwarecounters))
    
            
            durations = numpy.zeros(virtualmachine.numberofaxes)
            numpy.put(durations, movingaxes, stepinterval)
            
            numpy.put(counter_durations, movingaxes, moving_durations)
    
            counter_durations = counter_durations * softwarecounters
            overall_duration = overall_duration * softwarecounters[0]   #this is a hack for now
        
            directions2 = numpy.zeros(virtualmachine.numberofaxes)
            numpy.put(directions2, movingaxes, directions)
    
            for i in range(virtualmachine.numberofaxes):
                virtualmachine.motorcontrollers[i].hardwarecounter = hardwarecounters[i]
                virtualmachine.motorcontrollers[i].softwarecounter = counter_durations[i]
                virtualmachine.motorcontrollers[i].duration = overall_duration
                if directions2[i] == -1:
                    directions2[i] = 2
                virtualmachine.motorcontrollers[i].direction = directions2[i]
        else:
            nomove = 1
            for i in range(virtualmachine.numberofaxes):
                    virtualmachine.motorcontrollers[i].hardwarecounter = 0
                    virtualmachine.motorcontrollers[i].softwarecounter = 0
                    virtualmachine.motorcontrollers[i].duration = 0
                    virtualmachine.motorcontrollers[i].direction = 0
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
        

        try:
            #-------CONFIGURE AND OPEN SERIAL PORT-------------------------------
            portnumber = 'COM6'
            baudrate = 19200
            sertimeout = None #in seconds
    
            serport = serial.Serial(portnumber,baudrate, timeout=sertimeout)
    
            #-------SEND COMMAND-------------------------------------------------
    
            for i in range(len(outgoing)):
                serport.write(chr(outgoing[i]))
                a = serport.read()
    
            start = time.time()
            serport.read()
            print "XINT TIME", time.time() - start
            
        except serial.SerialException, details:
            if DEBUG_MODE:
                pass
            else:
                print "\nEXCEPTION RAISED:", details
                sys.exit(0)
            
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

        #movetime = movetime * 1.4

        return [delta, rate, movetime]


class Drawer(object):
    """
    Draw circuitboard in window. Currently for debug, but eventually for shock and awe.
    Requires pygame.
    """
    
    def __init__(self, pen_zoom_pairs=None):
        """
        Initializes window and drawing parameters, including displaying a pygame window.
        """
        self.max_x = 840
        self.max_y = 680
        
        self.zooms = {}
        for pen, zoom in pen_zoom_pairs:
            self.zooms[pen] = zoom
            
        # line color when pen up unless more sophisticated coloring is occuring
        self.up = (255, 255, 255)
        # line color when pen down unless more sophisticated coloring is occuring
        self.down = (255, 0, 0)
        # True if pen is up, False if pen is down
        self.is_ups = {}
        # current pen location along x axis
        self.xs = {}
        # current pen location along y axis
        self.ys = {}
        
        pygame.init() 
        #create the screen
        self.window = pygame.display.set_mode((self.max_x, self.max_y))
        #set background
        #self.window.fill( (30, 30, 255) )
        self.window.fill( (0,0,0) )
        
    def init_pen(self, pen, zoom):
        self.xs[pen] = int(self.max_x / 4.0) 
        self.ys[pen] = int(self.max_y / 4.0)
        self.is_ups[pen] = True
        if not pen in self.zooms:
            self.zooms[pen] = zoom
        
    def pen_up(self, pen):
        self.is_ups[pen] = True
        
    def pen_down(self, pen):
        self.is_ups[pen] = False
    
    def goto(self, x, y, pen, relative=True, zoom=None, rate=None, movetime=None):
        """
        Draws a line (x, y) from the current pen position. x and y are assumed to be 
        relative to current position.
        
        @param x: int
        @param y: int
        @param rate: 
        @param movetime: 
        """
        if not pen in self.xs:
            self.init_pen(pen, zoom)
    
        if rate and movetime:
            diffx = abs(self.xs[pen] - x)
            diffy = abs(self.ys[pen] - y)
            h = math.sqrt(diffx*diffx + diffy*diffy)

            nrate = round(rate)
           #print "ABC", self.is_ups[pen], nrate, "   ", h, "      ", rate
            hr = rate / 9.0 * 255
            #hr = h/rate
            #hr = (h*rate / 2500) * 255
            #hr = movetime/rate * 200
            
            if hr > 255:
                hr = 255
            if hr < 0:
                hr = 0
            hg = hb = self.is_ups[pen] and hr or 0
            color = (hr, hg, hb)
            ret = hr
        else:
            color = self.is_ups[pen] and self.up or self.down
            ret = 0
        #pygame.draw.line(self.window, (255,255,255), (self.x, self.y), (self.x+self.zoom*x, self.y+self.zoom*y), 4)
        if relative:
            pygame.draw.line(self.window, color, (self.xs[pen], self.ys[pen]), (self.xs[pen]+self.zooms[pen]*x, self.ys[pen]+self.zooms[pen]*y), 1)
            self.xs[pen] += self.zooms[pen]*x
            self.ys[pen] += self.zooms[pen]*y
        else:
            pygame.draw.line(self.window, color, (self.xs[pen], self.ys[pen]), (self.zooms[pen]*x, self.zooms[pen]*y), 1)
    
        # update window
        pygame.display.flip()
        
        return ret / 1000.0 
    
    def check_keyboard(self):
        """
        pygame window loop. check if ESCAPE key is pressed to close window and exit program
        """
        for event in pygame.event.get(): 
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: 
                    sys.exit(0)
                    
                    
    def pause_for_space(self):
        """
        sleeps until SPACEBAR is pressed
        """
        while True:
            for event in pygame.event.get(): 
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return True
            time.sleep(.2)





virtualmachine = machine()
machinecontroller = controller()

drawer = Drawer([('stepgen',4000), ('simmove',100), ('feedmode',1)])

#for move in localcomputer.movetable:
#    drawer.goto(move[0], move[1], 'movetable', relative=False)

virtualmachine.position[0] = 1
virtualmachine.position[1] = 1
virtualmachine.position[2] = 0.002               #For some reason setting this also changes the local computer movetable!!! Why???

# don't end program until press ESCAPE key
#while True: 
 #   drawer.check_keyboard()


def move( x = None, y = None, z = None, rate = 1):
    LOG = True
    if x == None: x = virtualmachine.position[0]
    if y == None: y = virtualmachine.position[1]
    if z == None: z = virtualmachine.position[2]

    
    moveto = [x,y,z]
    feedspeed = rate
    
    if LOG: print "commandedposition: ", moveto
    delta = machinecontroller.movegen(moveto)
    if moveto[2] > 0:
        drawer.pen_down('stepgen')
        drawer.pen_down('simmove')
    else:
        drawer.pen_up('stepgen')
        drawer.pen_up('simmove')
    nomove = machinecontroller.stepgen(delta, feedspeed)
    # how much to pause for loop when in DEBUG_MODE
    sleep_amt = 0
    if nomove != 1:
        outgoing = machinecontroller.xmit()
        [delta, rate, movetime] = machinecontroller.simmove(outgoing)
        print "SIMMOVE MOVETIME", movetime
        sleep_amt = drawer.goto(delta[0], delta[1], 'simmove', rate=rate, movetime=movetime)
        if LOG: print "MOVE COMPLETE", delta
    else:
        delta = numpy.zeros(virtualmachine.numberofaxes)
        if LOG: print "NO MOVE HERE!"

    virtualmachine.position = virtualmachine.position + delta

    if LOG: print "machine position: " , virtualmachine.position
    if LOG: print ""
    
    print "draw line"
    drawer.check_keyboard()
    print "done drawing"
                
    if DEBUG_MODE:
        # pause to mimic line drawing
        print "go to sleep"
        time.sleep(sleep_amt)
        print "wake up"
        # wait for space bar
        #drawer.pause_for_space()
