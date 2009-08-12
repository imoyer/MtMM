#RML to Virtual Machine Controller Language

import sys
import commands
import csv
import numpy



rml = 0
movetable = 0
feedmodetable = 0
zup = 0
tableindex = 0
usevirtualmachine = "virtualmachine9"
rmlunits = 0.001 #rml units in thousandths of an inch

traversespeed = 8 #units are in/min
retractspeed = 8 #units are in/min


try:
	rmlfile = sys.argv[1] #stores filename of source RML file into x
	vmcfile = rmlfile.replace('.rml','.py')
	rmlfile = open(rmlfile, mode = 'r')   #opens RML file as object rmlfile
	rmlfile.seek(0,0)   #sets file pointer at beginning

	rmlparser = csv.reader(rmlfile, delimiter=';', quoting = csv.QUOTE_ALL)     #parses rmlfile as a semi-colon delimited file
	rml = rmlparser.next()
	rmlfile.close()
except IndexError:
	print "Please enter name of RML file following virtualmachine.py"
	

zup = 0 #Initialize RML z axis up position
zdown = 0 #Initialize RML z axis down position
currentx = 0 #Initialize current x axis position
currenty = 0 #Initialize current y axis position
penposition = "down"
                   

rmllength = len(rml)
vmc = open(vmcfile, 'w')
returnchar = "\n"

vmc_header = "import " + usevirtualmachine + " as vm" + returnchar + returnchar
vmc.write(vmc_header)

vmc_traversespeed = "traverse_speed = " + str(traversespeed) + returnchar
vmc.write(vmc_traversespeed)

vmc_retractspeed = "retract_speed = " + str(retractspeed) + returnchar
vmc.write(vmc_retractspeed)

for h in xrange(rmllength):
	commander = 0
	firstterm = 0
	secondterm = 0
	currententry = rml[h]
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
			vmc_cuttingspeed = "cutting_speed = " + str(xyspeed) + returnchar
			vmc.write(vmc_cuttingspeed)
			
		elif currententry[i:j]== "VZ": #z travel speed
			commander = "VZ"
			firstterm = j
			zspeed = currententry[firstterm:entrylength]
			zspeed = float(zspeed)
			vmc_plungespeed = "plunge_speed = " + str(zspeed) + returnchar
			vmc.write(vmc_plungespeed)
			
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
		vmc_zdown = "z_down = " + str(zdown*rmlunits) + returnchar
		vmc_zup = "z_up = " + str(zup*rmlunits) + returnchar
		
		vmc.write(vmc_zdown)
		vmc.write(vmc_zup)
		

	if commander == "PD": #Pen down RML command.
		
		if penposition == "down":
		
			currentx = currententry[firstterm:secondterm]
			currenty = currententry[secondterm+1:entrylength]
			currentx = float(currentx)
			currenty = float(currenty)
			
			vmc_move = "vm.move(" + str(currentx*rmlunits) + "," + str(currenty*rmlunits) + ", z_down, cutting_speed)" + returnchar
			vmc.write(vmc_move)
		
		elif penposition == "up":
		
		
			vmc_move = "vm.move( z = z_down, rate = plunge_speed)" + returnchar
			vmc.write(vmc_move)
			
			currentx = currententry[firstterm:secondterm]
			currenty = currententry[secondterm+1:entrylength]
			currentx = float(currentx)
			currenty = float(currenty)
			
			vmc_move = "vm.move(" + str(currentx*rmlunits) + "," + str(currenty*rmlunits) + ", z_down, cutting_speed)" + returnchar
			vmc.write(vmc_move)
			penposition = "down"	


	if commander == "PU": #Pen up RML command.
		
		if penposition == "up":
			
			currentx = currententry[firstterm:secondterm]
			currenty = currententry[secondterm+1:entrylength]                   
			currentx = float(currentx)
			currenty = float(currenty)
							
			vmc_move = "vm.move(" + str(currentx*rmlunits) + "," + str(currenty*rmlunits) + ", z_up, traverse_speed)" + returnchar
			vmc.write(vmc_move)						
							
		elif penposition == "down":
			
			vmc_move = "vm.move( z = z_up, rate = retract_speed)" + returnchar
			vmc.write(vmc_move)
			
			currentx = currententry[firstterm:secondterm]
			currenty = currententry[secondterm+1:entrylength]
			currentx = float(currentx)
			currenty = float(currenty)
			
			vmc_move = "vm.move(" + str(currentx*rmlunits) + "," + str(currenty*rmlunits) + ", z_up, traverse_speed)" + returnchar
			vmc.write(vmc_move)
			penposition = "up"				




print vmcfile
