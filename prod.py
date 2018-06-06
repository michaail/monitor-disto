import monitor
import random
import time
import sys
import logging

pid = int(sys.argv[1])

logger = logging.getLogger("__name__")
logger.setLevel(logging.INFO)

logger.info(str(pid) + ' producer start')

monit = monitor.Monitor(pid)

ctr = 0
while True:
    monit.request()     # wait on lock
    if ctr == 0:        # produces
        product = [0]
    else:
        product = monit.Data
        #product.append(random.randint(1, 10))
        product.append(ctr)

    time.sleep(0.2)           # time delay
    ctr += 1
    monit.Data = product    # updates data for instance
    print('%s produced new value: %s' % (pid, product))
    print('################################')
    monit.exit()            # releases lock

    if ctr == 10:
        print("produced all elements")
        monit.kill()
        break

print('%s Koniec przetwarzania *****' % pid)
