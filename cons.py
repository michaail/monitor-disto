import monitor
import random
import time

monit = monitor.Monitor(1)

ctr = 0
while True:
    print('consumer iter.')
    monit.request()     # wait on lock
    if monit.Data:
        element = monit.Data.pop(0)     # grab element from the top of list
    else:
        ctr += 1
        print('Lista jest pusta, czekam na dane...[%s]' % ctr)
        time.sleep(3)

    monit.exit()        # release lock

    if ctr == 3:
        print('Koniec przetwarzania')
        monit.kill()
        break
