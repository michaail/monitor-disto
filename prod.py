import monitor
import random
import time

monit = monitor.Monitor(0)


ctr = 0
while True:
    print('Producer iter.')
    monit.request()     # wait on lock
    if ctr == 0:        # produces
        product = [0]
    else:
        product = monit.Data
        #product.append(random.randint(1, 10))
        product.append(ctr)

    time.sleep(1)           # time delay
    ctr += 1
    monit.Data = product    # updates data for instance
    print('produced new value: %s' % product)
    monit.exit()            # releases lock

    if ctr == 10:
        print("produced all elements")
        monit.kill()
        break
