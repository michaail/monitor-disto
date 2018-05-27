import zmq
import threading
import time
from configuration import PORTS


# using Suzuki-Kasami token based algorithm
# unique token is shared among nodes
# node which possesses the token is allowed to enter CS (critical section)
class Monitor:
    def __init__(self, mid):
        # suzuki-kasami elements
        # _Req[self._id] = num
        self._Req = [0] * len(PORTS)
        self._Last = [0] * len(PORTS)
        self._Queue = []
        self._token_granted = threading.Event()
        self._id = mid
        if self._id == 0:       # Token handling
            self.token = True   # has token at start
            self._token_granted.set()
            self._critical = True
        else:
            self.token = False  # don't have token at start

        self._critical = False
        self._token_just_granted = False

        # zmq variables
        self.publisher_port = PORTS[mid]
        self.msg_type = ''
        self.msg_value = ''
        self.msg_hid = None

        self.Data = None
        self._lock = threading.Lock()

        self.pub_sock = self.publisher_init()   # creates publisher socket
        self.msg_recvr = threading.Thread(target=self.message_recv)  # creates and initializes subscriber socket and receives
        self.msg_recvr.start()

        self._is_active = True          # indicates that monitor is up & running
        time.sleep(3)

    def request(self):
        print('***requesting CS***')
        self._lock.acquire()
        if self.token:
            self._critical = True
            print('***** Have Token & ENTERED CS *****')
            return
        else:
            self._Req[self._id] += 1        # increment own num
            self.req_broadcast(self._id, self._Req[self._id])   # send request incremented to all
            if self._lock.locked():
                self._lock.release()

        self._token_granted.wait()          # wait for token 
        self._lock.acquire()
        if self.token:
            self._token_just_granted = False
            print('***** Token granted enter CS ******')
            self._critical = True
            return
            #print('entered critical section in: %s' % self._id)


    def exit(self):
        #self._token_granted.clear()
        #print('exiting CS')
        if self.token:
            #self._lock.acquire()
            self._Last[self._id] = self._Req[self._id]
            port = list(PORTS)
            port.remove(self.publisher_port)
            self._critical = False
            for node in port:           # for every node k 
                k = PORTS.index(node)   
                if k in self._Queue:    
                    pass
                else:                   # not in the Q: Q.append(k)
                    if self._Req[PORTS.index(node)] == self._Last[PORTS.index(node)] + 1:
                        self._Queue.append(PORTS.index(node))

            if self._Queue:     # if not empty
                a_id = self._Queue.pop(0)   # takes element from the top of list
                self.pass_token(self._id, a_id, self._Queue, self._Last, self.Data)
            print('***exitted cs***')
            if self._lock.locked():
                self._lock.release()

    # Initializes whole ZMQ stuff
    def publisher_init(self):   # TODO exception handling for creating new context and port binding
        pub_ctx = zmq.Context()
        pub_sock = pub_ctx.socket(zmq.PUB)
        pub_sock.bind('tcp://*:%s' % self.publisher_port)
        print('initialized zmq objects\nWaiting for other Publishers...')
        time.sleep(8)  # wait for other publishers to populate
        return pub_sock

    # Connects all available nodes to own subscriber
    def subscriber_init(self):
        sub_ctx = zmq.Context()
        sub_sock = sub_ctx.socket(zmq.SUB)
        ports = list(PORTS)
        ports.remove(self.publisher_port)
        for port in ports:
            sub_sock.connect('tcp://localhost:%s' % port)
        topicfilter = ""
        sub_sock.setsockopt_string(zmq.SUBSCRIBE, topicfilter)
        time.sleep(1)
        poll = zmq.Poller()
        poll.register(sub_sock, zmq.POLLIN)
        return sub_sock, poll

    # passes the token to specified node
    def pass_token(self, id, a_id, Q, last, data):
        self.token = False
        msg = {'type': 'token', 'id': id, 'a_id': a_id, 'queue': Q, 'last': last, 'data': data}
        print("passing token to: %s token: Q: %s; Last: %s; Data: %s; " % (a_id, Q, last, data))
        self._token_granted.clear()
        self.pub_sock.send_json(msg)

    # Sends messages to other nods
    def req_broadcast(self, id, num):
        msg = {'type': 'broadcast', 'id': id, 'num': num}
        print('broadcasts %s' % self._Req)
        self.pub_sock.send_json(msg)

    # Receives incoming messages (works in separate thread)
    def message_recv(self):
        sub_sock, poll = self.subscriber_init()
        #sub_sock.RCVTIMEO = 500
        while self._is_active:
            # http://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/multisocket/zmqpoller.html
            socks = dict(poll.poll(1000))
            if sub_sock in socks and socks[sub_sock] == zmq.POLLIN:
            
                self._lock.acquire()
                msg = sub_sock.recv_json()  # Receive JSON object on subscriber
                
                if msg['id'] == self._id:   # Received message from myself
                    continue

                if msg['type'] == 'token':
                    if msg['a_id'] == self._id:
                        self.Data = msg['data']
                        self._Last = msg['last']
                        self._Queue = msg['queue']
                        self.token = True
                        self._token_just_granted = True
                        print('received token from: %s token: Q: %s; Last: %s; Data: %s;' % (msg['id'], msg['queue'], msg['last'], msg['data']))
                        self._token_granted.set()

                elif msg['type'] == 'broadcast':
                    self._Req[msg['id']] = max(self._Req[msg['id']], msg['num'])
                    print("received broadcast %s from %s" % (self._Req, msg['id']))
                    # checks if I have token but not in CS and other node has a fresh request
                    if self.token and self._critical == False and self._Req[msg['id']] == self._Last[msg['id']] + 1 and self._token_just_granted == False:
                        print('not in cs passes token')
                        self.pass_token(self._id, msg['id'], self._Queue, self._Last, self.Data)
                    #self._Queue.append(msg['id'])       # append nodes queue
                    # if not using?

                else:
                    print('Received unknown message!!!')
                if self._lock.locked():
                    self._lock.release()
        
        sub_sock.close()

    def kill(self):
        self.pub_sock.close()
        self._is_active = False
        self.msg_recvr.join()
        print('killed process')


