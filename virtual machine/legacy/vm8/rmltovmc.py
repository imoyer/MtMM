#RML to Virtual Machine Controller Language Converter
#Rapid Prototyping of Rapid Prototyping Machines
#
#Ilan E. Moyer
#
# CREATED 4/8/2009

#-----------IMPORTS------------------------------------------------------------

import sys
import commands
import csv

class computer(object):
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
        
        rmllength = len(self.rml)
        translationfile = open('fromrml.vmc','w')

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
                zdownstring = "zdown = " + str(zdown)
                zupstring = "zup = " + str(zup)
                translationfile.write(zdownstring)
                translationfile.write(zupstring)
                

            if commander == "PD": #Pen down RML command.
                currentmove[0,0] = currentx
                currentmove[0,1] = currenty
                currentmove[0,2] = zdown
                currentfeed[0,0] = feedmode.get('plunge')
                                
                currentx = currententry[firstterm:secondterm]
                currenty = currententry[secondterm+1:entrylength]
                currentx = float(currentx)
                currenty = float(currenty)
                            


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

        translationfile.close()

localcomputer = computer()
computer.loadrml()
computer.parserml()
