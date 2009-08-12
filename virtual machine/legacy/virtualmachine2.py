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
import numarray
import time
import math

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
                
        movetable[1,2]=zup          #sets the height of the initial retract move

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
    direction = 0 # 0 = off, 1 = forward, 2 = backward
    duration = 0 #next move total duration (in prescaled clock steps)
    rate = 0 #next move time between steps (in prescaled clock steps)
    softwarecounter = 0
    hardwarecounter = 0
    softwarecountertemp = 0
    
    
    
    
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
        
    guides[0].vector = [1,0,-0.01]
    guides[1].vector = [0,1,-0.01]
    guides[2].vector = [0,0,1]

    motorcontrollers[0].clockspeed = 20000000
    motorcontrollers[1].clockspeed = 20000000
    motorcontrollers[2].clockspeed = 20000000

    motorcontrollers[0].prescalar = 1/1024.
    motorcontrollers[1].prescalar = 1/1024.
    motorcontrollers[2].prescalar = 1/1024.

    motorcontrollers[0].stepsize = 0.002
    motorcontrollers[1].stepsize = 0.002
    motorcontrollers[2].stepsize = 0.0005

    motorcontrollers[0].softwarecounter = 2**16-1
    motorcontrollers[1].softwarecounter = 2**16-1
    motorcontrollers[2].softwarecounter = 2**16-1

    motorcontrollers[0].hardwarecounter = 2**8-1
    motorcontrollers[1].hardwarecounter = 2**8-1
    motorcontrollers[2].hardwarecounter = 2**8-1
    

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
        rate = rate / 60.        #now it's in inches per second
        distancesquaredsum = 0
        clockspeeds = numpy.zeros(virtualmachine.numberofaxes)
        prescalars = numpy.zeros(virtualmachine.numberofaxes)
        stepsizes = numpy.zeros(virtualmachine.numberofaxes)
                                  
        for i in range(virtualmachine.numberofaxes):
            distancesquaredsum = distancesquaredsum + (traverse[i]*traverse[i])
            clockspeeds[i] = virtualmachine.motorcontrollers[i].clockspeed
            prescalars[i] = virtualmachine.motorcontrollers[i].prescalar
            stepsizes[i] = virtualmachine.motorcontrollers[i].stepsize

            
        distance = math.sqrt(distancesquaredsum)    #Euclidean distance of move
        time = distance / rate                      #Duration of move in seconds
        scaledclock = clockspeeds / prescalars      #Motor controller clock speeds (ticks / second)
        
        steps = traverse / stepsizes        #number of steps needed
        steps = numpy.round(steps)           #convert steps into integers

        movingaxes = numpy.nonzero(steps)[0]   #isolates only the moving axes
        movingsteps = numpy.take(steps, movingaxes)
        print movingsteps

        stepintervals = numpy.ones(len(movingsteps))/movingsteps        #this converts moving steps into time between steps
        print stepintervals

        orderedindex = numpy.argsort(stepintervals)

        movingaxes = numpy.take(stepintervals,orderedindex)     #this section places all step arrays into an order from min to max step interval
        movingsteps = numpy.take(movingsteps, orderedindex)
        stepintervals = numpy.take(stepintervals, orderedindex)
 
        stepindices = numpy.array(range(len(stepintervals)))            #here the step interval matrix gets shifted (logical rotate) by 1
        stepindicesrotated = stepindices + 1
        stepindicesrotated[len(stepindices)-1]= 0
        stepintervalsrotated = numpy.take(stepintervals,stepindicesrotated)
        print stepintervalsrotated

        dynamicratiomatrix = stepintervalsrotated/stepintervals
        
        dynamicrangematrix = stepintervalsrotated-stepintervals         #gives the difference in intervals 
        dynamicrangematrix = dynamicrangematrix[0:(len(dynamicrangematrix)-1)]

        integerresolution = 1/dynamicrangematrix
        
        print dynamicrangematrix







        #maxdynamicrange = max(dynamicratiomatrix)
        #mindynamicrange = min(dynamicratiomatrix)
        #dynamicratio = maxdynamicrange / mindynamicrange
        
        

        #print dynamicratio * stepintervals

        
        
        
        
  

        #here we determine the necessary dynamic range

        overalldynamicrange = stepintervals[len(stepintervals)-1]/stepintervals[0]  #this gives the maximum present dynamic range
        
        

    



        
        maxsteps = max(steps)               #fastest axis number of steps
        minsteps = min(steps)               #slowest axis number of steps
        dynamicrange = maxsteps / minsteps  #the dynamic range between the minimum and maximum number of steps
        
        
        minrate = time/minsteps             #amount of time between steps of the slowest axis
        minrateclocktics = scaledclock * minrate    #number of clock ticks 

        

        return steps
        

            


    


        

moveto = numpy.array([4,3,2])
virtualmachine = machine()
machinecontroller = controller()
localcomputer = computer()
localcomputer.loadrml()
localcomputer.parserml()
#print localcomputer.movetable
#print localcomputer.feedmodetable


delta = machinecontroller.movegen(moveto)
print delta
tickers = machinecontroller.stepgen(delta, 4)
print tickers
    
    

