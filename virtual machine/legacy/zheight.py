import virtualmachine9 as vm
import time

irate = 8

for i in range(1,4):

    vm.move(y=1.02, rate = irate)
    time.sleep(5)
    vm.move(y=1.04, rate = irate)
    time.sleep(5)
    vm.move(y=1.06, rate = irate)
    time.sleep(5)
    vm.move(y=1.04, rate = irate)
    time.sleep(5)
    vm.move(y=1.02, rate = irate)
    time.sleep(5)
    vm.move(y=1.0, rate = irate)
    time.sleep(5)

