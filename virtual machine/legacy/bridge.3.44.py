import virtualmachine9 as vm

traverse_speed = 8
retract_speed = 8
cutting_speed = 4.0
plunge_speed = 4.0
z_down = -0.005
z_up = 0.05
vm.move( z = z_up, rate = retract_speed)
vm.move(1.027,1.387, z_up, traverse_speed)
vm.move( z = z_down, rate = plunge_speed)
vm.move(1.117,1.387, z_down, cutting_speed)
vm.move(1.117,1.342, z_down, cutting_speed)
vm.move(1.027,1.342, z_down, cutting_speed)
vm.move(1.027,1.387, z_down, cutting_speed)
