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
        else:
            self.token = False  # don't have token at start

        self._critical = False

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
        #print('requesting CS')
        self._lock.acquire()
        if not self.token:
            self._Req[self._id] += 1        # increment own num
            self.req_broadcast(self._id, self._Req[self._id])   # send request incremented to all
            self._lock.release()
            self._token_granted.wait()      # waiting for token
        else:
            self._critical = True
            #print('entered critical section in: %s' % self._id)
            self._lock.release()


    def exit(self):
        #self._token_granted.clear()
        #print('exiting CS')
        self._lock.acquire()
        self._Last[self._id] = self._Req[self._id]
        port = list(PORTS)
        port.remove(self.publisher_port)
        for node in port:
            if self._Req[PORTS.index(node)] == self._Last[PORTS.index(node)] + 1:
                self._Queue.append(PORTS.index(node))

        if self._Queue:     # if not empty
            a_id = self._Queue.pop(0)   # takes element from the top of list
            self.pass_token(self._id, a_id, self._Queue, self._Last, self.Data)
        self._critical = False
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
            print('Subscriber connected')
        topicfilter = ""
        sub_sock.setsockopt_string(zmq.SUBSCRIBE, topicfilter)
        time.sleep(1)
        return sub_sock

    # passes the token to specified node
    def pass_token(self, id, a_id, Q, last, data):
        msg = {'type': 'token', 'id': id, 'a_id': a_id, 'queue': Q, 'last': last, 'data': data}
        print("passing token to: %s" % a_id)
        self.token = False
        self._token_granted.clear()
        self.pub_sock.send_json(msg)

    # Sends messages to other nods
    def req_broadcast(self, id, num):
        msg = {'type': 'broadcast', 'id': id, 'num': num}
        print('broadcasts %s' % self._Req)
        self.pub_sock.send_json(msg)

    # Receives incoming messages (works in separate thread)
    def message_recv(self):
        sub_sock = self.subscriber_init()
        #sub_sock.RCVTIMEO = 500
        while self._is_active:
            msg = sub_sock.recv_json()  # Receive JSON object on subscriber
            self._lock.acquire()
            if msg['id'] == self._id:   # Received message from myself
                continue

            if msg['type'] == 'token':
                if msg['a_id'] == self._id:
                    self.Data = msg['data']
                    self._Last = msg['last']
                    self._Queue = msg['queue']
                    self.token = True
                    print('received token from: %s' % msg['id'])
                    self._token_granted.set()

            elif msg['type'] == 'broadcast':
                self._Req[msg['id']] = msg['num']   # req[k] = num
                print("received broadcast %s" % self._Req)
                # checks if I have token but not in CS and other node has a fresh request
                if self.token and not self._critical and self._Req[msg['id']] == self._Last[msg['id']] + 1:
                    self.pass_token(self._id, msg['id'], self._Queue, self._Last, self.Data)
                #self._Queue.append(msg['id'])       # append nodes queue
                # if not using?

            else:
                print('Received unknown message!!!')
            self._lock.release()
        sub_sock.close()

    def kill(self):
        self.pub_sock.close()
        self._is_active = False
        self.msg_recvr.join()
        print('killed process')


