import logging

from subprocess import Popen

logger = logging.getLogger("__name__")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("logs.txt")
fh.setLevel(logging.INFO)
logger.addHandler(fh)
logger.info('Started main script')


p1 = Popen(["python3", "cons.py", "1"])
p2 = Popen(["python3", "cons.py", "2"])
p3 = Popen(["python3", "prod.py", "0"])


p1.wait(); p2.wait(); p3.wait()
