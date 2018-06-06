import monitor
import random
import time
import sys
import logging

cid = int(sys.argv[1])

logger = logging.getLogger("__name__")
logger.setLevel(logging.INFO)

logger.info(str(cid) + ' consument start')

monit = monitor.Monitor(cid)

ctr = 0
while True:
    monit.request()     # wait on lock
    if monit.Data:
        element = monit.Data.pop(0)     # grab element from the top of list
        
        print('%s consumed value %s' % (cid, element))
        print('###########################')
        ctr = 0
    else:
        ctr += 1
        time.sleep(random.uniform(0.2, 1.0))
        
    time.sleep(random.uniform(0.2, 1.0))
    monit.exit()        # release lock

    if ctr == 5:
        monit.kill()
        break

print('%s Koniec przetwarzania *****' % cid)
