# Virtual Machine
# Rapid Prototyping of Rapid Prototyping Machines
#
# Ilan E. Moyer
# for the MIT Center for Bits and Atoms
#
# 5/4/08
#

#--------IMPORTS----------------------------------------------------------
import sys, commands
import csv
import numpy
import numarray
import time

#-------DEFINITIONS-------------------------------------------------------

class virtual_machine_defs(object):
    xresolution = 0.001
    yresolution = 0.001
    zresolution = float(1)/float(20*96)

    processorfrequency = float(20000000) #20MHz Virtual Machine Clock Frequency
    counterprescaler = float(128)
    xyhardwarecounter = float(146)    #This centers the dynamic range of the possible axis feed speeds.
                                    #With this configuration, the step frequency dynamic range is
                                    #133.77Hz:0.00304Hz (65536:1).
                                    #The max feedrate of a single axis with a step size of 0.001
                                    #is 0.133 in/s or 7.8 in/min
                                    #The min feedrate while still allowing a slope of of 1/3000,
                                    #or one minor step per 6" of travel, is 0.00304*3 = 0.009 in/s
                                    #or 0.54 in/min.
    zhardwarecounter = float(70)

    xyhardwaresteptime = xyhardwarecounter*counterprescaler/processorfrequency
    zhardwaresteptime = zhardwarecounter*counterprescaler/processorfrequency

class virtual_machine_state(object):
    vm_x = 0
    vm_y = 0
    vm_z = 0

#--------FUNCTIONS--------------------------------------------------------

#--------VIRTUAL MACHINE CONFIGURATION FUNCTION---------------------------
#INPUTS: Requested move distances in inches
#OUTPUTS: Steps, direction, and time for three axes of movement
#NOTES: THIS CODE PRODUCES MUCH FASTER NET FEEDRATES THAN IS DESIRABLE
def virtual_machine_configuration(needmovex,needmovey,needmovez, needfeed):
    
    xresolution = virtual_machine_defs.xresolution
    yresolution = virtual_machine_defs.yresolution
    zresolution = virtual_machine_defs.zresolution

    xyhardwaresteptime = virtual_machine_defs.xyhardwaresteptime
    zhardwaresteptime = virtual_machine_defs.zhardwaresteptime

    xsteps = int(needmovex/xresolution)
    ysteps = int(needmovey/yresolution)
    zsteps = int(needmovez/zresolution)

    if xsteps>0:
        xdirection = 1
    else:
        xdirection = 0

    if ysteps>0:
        ydirection = 1
    else:
        ydirection = 0

    if zsteps>0:
        zdirection = 1
    else:
        zdirection = 0
        
    xactual = float(xsteps)*xresolution
    yactual = float(ysteps)*yresolution
    zactual = float(zsteps)*zresolution

    xsteps = abs(xsteps)
    ysteps = abs(ysteps)
    zsteps = abs(zsteps)

    needfeed = needfeed/60      #needed feedrate in inches/s
    totaldistance=numpy.sqrt(needmovex**2+needmovey**2+needmovez**2)
    if needfeed != 0:
        movetime=totaldistance/needfeed         #movetime in seconds
        if xsteps != 0:
            xsteptime = movetime/xsteps         #steptime in seconds per step
            xtimenotzero = xsteptime/xyhardwaresteptime     #this is placed before xtime to prevent overspeed errors
            xtime = int(xtimenotzero)
            if xtime==0:
                print "X-AXIS OVERSPEED ERROR"
        else:
            xsteptime = 0
            xtime = 0
            xtimenotzero=2**16  #an impossible time
            
        if ysteps != 0:
            ysteptime = movetime/ysteps
            ytimenotzero = ysteptime/xyhardwaresteptime
            ytime=int(ytimenotzero)
            if ytime == 0:
                print "Y-AXIS OVERSPEED ERROR"
        else:
            ysteptime = 0
            ytime = 0
            ytimenotzero=2**16

        if zsteps != 0:
            zsteptime = movetime/zsteps
            ztimenotzero = zsteptime/zhardwaresteptime
            ztime=int(ztimenotzero)
            if ztime == 0:
                print "Z-AXIS OVERSPEED ERROR"
        else:
            zsteptime = 0
            ztime = 0
            ztimenotzero=2**16

        #This section deals with the discreet nature of the steps.
            
        mintime= min(xtimenotzero,ytimenotzero,ztimenotzero)
        

        if xtime==mintime:
            xsteptime=xtime*xyhardwaresteptime
            movetime=xsteps*xsteptime
            if ysteps != 0:
                ysteptime = movetime/ysteps
                ytime = int(ysteptime/xyhardwaresteptime)
                if ytime == 0:
                    print "Y-AXIS OVERSPEED ERROR"
            else:
                ysteptime = 0
                ytime = 0
            if zsteps != 0:
                zsteptime = movetime/zsteps
                ztime = int(zsteptime/zhardwaresteptime)
                if ztime == 0:
                    print "Z-AXIS OVERSPEED ERROR"
            else:
                zsteptime = 0
                ztime = 0

        if ytime==mintime:
            ysteptime=ytime*xyhardwaresteptime
            movetime=ysteps*ysteptime            
            if xsteps != 0:
                xsteptime = movetime/xsteps         #steptime in seconds per step
                xtime = int(xsteptime/xyhardwaresteptime)
                if xtime==0:
                    print "X-AXIS OVERSPEED ERROR"
            else:
                xsteptime = 0
                xtime = 0

            if zsteps != 0:
                zsteptime = movetime/zsteps
                ztime = int(zsteptime/zhardwaresteptime)
                if ztime == 0:
                    print "Z-AXIS OVERSPEED ERROR"
            else:
                zsteptime = 0
                ztime = 0

        if ztime==mintime:
            zsteptime=ztime*zhardwaresteptime
            movetime=zsteps*zsteptime
            if xsteps != 0:
                xsteptime = movetime/xsteps         #steptime in seconds per step
                xtime = int(xsteptime/xyhardwaresteptime)
                xtimenotzero = xtime
                if xtime==0:
                    print "X-AXIS OVERSPEED ERROR"
            else:
                xsteptime = 0
                xtime = 0
                xtimenotzero=2**16  #an impossible time
                
            if ysteps != 0:
                ysteptime = movetime/ysteps
                ytime = int(ysteptime/xyhardwaresteptime)
                ytimenotzero=ytime
                if ytime == 0:
                    print "Y-AXIS OVERSPEED ERROR"
            else:
                ysteptime = 0
                ytime = 0
                
        if xtime!=0:    
            xactualfeed=(float(xresolution)/(xyhardwaresteptime*xtime))*60
        else:
            xactualfeed=0
        if ytime!=0:
            yactualfeed=(float(yresolution)/(xyhardwaresteptime*ytime))*60
        else:
            yactualfeed=0
        if ztime!=0:
            zactualfeed=(float(zresolution)/(zhardwaresteptime*ztime))*60
        else:
            zactualfeed=0
#        print "REQUESTED FEED: ", needfeed*60       
#        print "ACTUAL FEED: ",numpy.sqrt(xactualfeed**2+yactualfeed**2+zactualfeed**2)


    else:
        print "ERROR: ZERO FEED RATE"
        movetime = 0
    
    return xsteps, xdirection, xtime,xactual,ysteps, ydirection, ytime, yactual, zsteps, zdirection, ztime, zactual


def real_machine(xsteps,xdirection,xtime,ysteps,ydirection,ytime,zsteps,zdirection,ztime):
    print "X STEPS: ", xsteps, " @ ", xtime
    print "X DIREC: ", xdirection
    print""
    print "Y STEPS: ", ysteps, " @ ", ytime
    print "Y DIREC: ", ydirection
    print ""
    print "Z STEPS: ", zsteps, " @ ", ztime
    print "Z DIREC: ", zdirection
    print ""
    return None

def virtual_machine(xsteps,xdirection,xtime,ysteps,ydirection,ytime,zteps,zdirection,ztime):
    
    xresolution = virtual_machine_defs.xresolution
    yresolution = virtual_machine_defs.yresolution
    zresolution = virtual_machine_defs.zresolution

    xyhardwaresteptime = virtual_machine_defs.xyhardwaresteptime
    zhardwaresteptime = virtual_machine_defs.zhardwaresteptime

    xmovetime = xyhardwaresteptime*xsteps*xtime
    ymovetime = xyhardwaresteptime*ysteps*ytime
    zmovetime = zhardwaresteptime*zsteps*ztime

    maxmovetime = max(xmovetime,ymovetime,zmovetime)
    time.sleep(maxmovetime)

    virtual_machine_state.vm_x = virtual_machine_state.vm_x + xresolution*xsteps*(xdirection*2-1)
    virtual_machine_state.vm_y = virtual_machine_state.vm_y + yresolution*ysteps*(ydirection*2-1)
    virtual_machine_state.vm_z = virtual_machine_state.vm_z + zresolution*zsteps*(zdirection*2-1)

    print "VM POSITION: ",virtual_machine_state.vm_x," ",virtual_machine_state.vm_y," ",virtual_machine_state.vm_z
    print " "
    print " "
    print " "
    return None

#------- FEEDRATE DEFINITIONS TO BE INPUT BY USER ------------------------

retractfeed = 7 #tool retraction feedrate (in/min)
plungefeed = 4 #tool plunge feedrate (in/min)
traversefeed = 7 #feedrate to be used during locating moves (in/min)
cutfeed = 4 #feedrate to be used during cutting moves (in/min)

#-------COORDINATE TRANSFORMATION DEFINITIONS TO BE INPUT BY USER---------

xtrans = 0
ytrans = 0
ztrans = 0

xtheta = 0  #in radians
ytheta = 0  #in radians
ztheta = 0  #in radians


#-------CURRENT POSITION--------------------------------------------------
#NOTE: These values should get defined when the user sets x,y,z home.

xposition = 1 #inches
yposition = 1
zposition = 0


#------- CONVERTS RML TO GLOBAL COORDINATE SYSTEM TOOLPATH ---------------
#
# INPUTS:   sys.argv    -this is the filename argument passed to the script
# OUTPUTS:  movetable   -a matrix containing x,y,z global coordinates

try:
    x = sys.argv[1] #stores filename of source RML file into x
except IndexError:
    print "Please enter name of RML file following virtualmachine.py"

rmlfile = open(x, mode = 'r')   #opens RML file as object rmlfile
rmlfile.seek(0,0)   #sets file pointer at beginning

rmlparser = csv.reader(rmlfile, delimiter=';', quoting = csv.QUOTE_ALL)     #parses rmlfile as a semi-colon delimited file
parsedrml = rmlparser.next()

zspeed = 0  #RML z axis feed speed
xyspeed = 0 #RML xy axis feed speed
zup = 0 #RML z axis up position
zdown = 0 #RML z axis down position
currentx = xposition*1000 #current x axis position
currenty = yposition*1000 #current y axis position
movetable = numpy.array([[1,1,1],[1,1,1]],float)  #table of xyz moves in x,y,z format
currentmove = numpy.array([[1,1,1],[1,1,1]],float)    #current move in x,y,z format

feedtable = numpy.array([[1],[1]],float) #table of feedrates in in/min
currentfeed = numpy.array([[1],[1]],float) #current feedrate in in/min                       

rmllength = len(parsedrml)

for h in xrange(rmllength):
    commander = 0
    firstterm = 0
    secondterm = 0
    currententry = parsedrml[h]
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
        currentfeed[0,0] = plungefeed
                        
        currentx = currententry[firstterm:secondterm]
        currenty = currententry[secondterm+1:entrylength]
        currentx = float(currentx)
        currenty = float(currenty)
                        
        currentmove[1,0] = currentx
        currentmove[1,1] = currenty
        currentmove[1,2] = zdown
        currentfeed[1,0] = cutfeed
                        
        movetable = numpy.concatenate((movetable,currentmove),0)
        feedtable = numpy.concatenate((feedtable,currentfeed),0)


    if commander == "PU": #Pen up RML command.
        currentmove[0,0] = currentx
        currentmove[0,1] = currenty
        currentmove[0,2] = zup
        currentfeed[0,0] = retractfeed

        currentx = currententry[firstterm:secondterm]
        currenty = currententry[secondterm+1:entrylength]                   
        currentx = float(currentx)
        currenty = float(currenty)
                        
        currentmove[1,0] = currentx
        currentmove[1,1] = currenty
        currentmove[1,2] = zup
        currentfeed[1,0] = traversefeed
                        
        movetable = numpy.concatenate((movetable,currentmove),0)
        feedtable = numpy.concatenate((feedtable,currentfeed),0)
                        
#movetable = movetable[2::,:]    #removes blank seed
        
movetable[1,2]=zup          #sets the height of the initial retract move

movetable = movetable / 1000    #converts movetable to units of inches
                                # had been in modela units of 0.001 in

movetable[0,0]=xposition     #retracts the tool at the home position
movetable[0,1]=yposition
movetable[0,2]=zposition
feedtable[0,0]=retractfeed
movetable[1,0]=xposition
movetable[1,1]=yposition
feedtable[1,0]=retractfeed


#NOTES: The array returned by this section of code, movetable, will
#       have duplicate entries whenever two PD commands occur in
#       a row. This should be filtered out before converting the move
#       commands into packets.



#------------- VIRTUAL MACHINE STARTS HERE ------------------------------

#------------- COORDINATE TRANSFORMATIONS -------------------------------
# NOTE: This is not fully implemented yet, and has no effect on the movetable.
#       Eventually this section would alter movetable to the virtual machine's
#       coordinate system. For now it is assumed that the WCS and VMCS are identical.

cosx = numpy.cos(xtheta)
sinx = numpy.sin(xtheta)
cosy = numpy.cos(ytheta)
siny = numpy.sin(ytheta)
cosz = numpy.cos(ztheta)
sinz = numpy.sin(ztheta)

htm_xtrans = numpy.array([[1, 0, 0, xtrans],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
htm_ytrans = numpy.array([[1, 0, 0, 0],[0,1,0,ytrans],[0,0,1,0],[0,0,0,1]])
htm_ztrans = numpy.array([[1, 0, 0, 0],[0,1,0,0],[0,0,1,ztrans],[0,0,0,1]])

htm_xtheta = numpy.array([[1, 0, 0, 0],[0,cosx,-sinx,0],[0,sinx,cosx,0],[0,0,0,1]])
htm_ytheta = numpy.array([[cosy, 0, siny, 0],[0,1,0,0],[-siny,0,cosy,0],[0,0,0,1]])
htm_ytheta = numpy.array([[cosz, -sinz, 0, 0],[sinz,cosz,0,0],[0,0,1,0],[0,0,0,1]])

#------------- MOVE GENERATOR -------------------------------------------

needmovex = 0   #desired move in x direction
needmovey = 0   #desired move in y direction
needmovez = 0   #desired move in z direction

xsteps = 0  #steps taken in x direction
ysteps = 0
zsteps = 0

xdirection = 0 #0 is reverse, 2 is forward
ydirection = 0
zdirection = 0

xtime = 0   #prescaled clock counts between steps in x direction
ytime = 0
ztime = 0

virtual_machine_state.vm_x = xposition  #initializes virtual machine state
virtual_machine_state.vm_y = yposition
virtual_machine_state.vm_z = zposition

for i in xrange(movetable.shape[0]):
    needmovex = movetable[i,0] - xposition
    needmovey = movetable[i,1] - yposition
    needmovez = movetable[i,2] - zposition
    needfeed = feedtable[i,0]

    
    (xsteps,xdirection,xtime,xactual,ysteps,ydirection,ytime,yactual,zsteps,zdirection,ztime,zactual)=virtual_machine_configuration(needmovex,needmovey,needmovez, needfeed)

    xposition = xposition + xactual
    yposition = yposition + yactual
    zposition = zposition + zactual

    if xsteps != 0 or ysteps != 0 or zsteps != 0:
    
        real_machine(xsteps,xdirection,xtime, ysteps, ydirection, ytime, zsteps, zdirection, ztime)
        virtual_machine(xsteps,xdirection,xtime,ysteps,ydirection,ytime,zsteps,zdirection,ztime)
        


