from import_modules import *
from packet import Packet
class Sender:
    '''
    1. 
    '''
    def __init__(self, args):
        # configuration
        self.threshold = args.threshold
        self.timeout = 1 # 1 sec
        self.receive_size = 100000
        self.packet_size = 1024 # 1024 bytes
        self.agent_ip = self.ip = args.IP
        self.port = args.send_port
        self.agent_port = args.recv_port
        
        # socket init
        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_recv.bind((self.ip, self.port))
        #self.sock.setblocking(0)

        # divide packets
        self.packets = self.divide_file(args.file)
        self.is_packets_sended = [False] * len(self.packets)
        # Go-Back-N
        self.base = 0
        self.nextseqnum = 0
        self.congestion_window = 1

        # timer
        self.timer = None
        self.timer_start = False

        # ack number
        self.ack_number = -1

        # congestion control
        self.target_ack_number = -1

    def divide_file(self, file):
        packets = []
        seq_num = 0
        with open(file, "rb") as f:
            # read util end of file
            while True:
                # add sequence number
                data = f.read(self.packet_size)
                if data == b'':
                    break
                else:
                    # make packet 
                    packet = Packet(seq_num, "data", data, file)
                    seq_num += 1

                    # append packet list
                    packets.append(packet)

        return packets

    def sendto(self, index):
        if self.is_packets_sended[index] == True:
            print("resnd\tdata\t#{},\twinSize = {}".format(index, self.congestion_window))
        else:   
            print("send\tdata\t#{},\twinSize = {}".format(index, self.congestion_window))
        # sendto
        self.sock_send.sendto(pickle.dumps(self.packets[index]), (self.agent_ip, self.agent_port))
        # tag sended
        self.is_packets_sended[index] = True

    def recvfrom(self):
        packet, addr = self.sock_recv.recvfrom(self.receive_size)
        packet = pickle.loads(packet)
        if packet.type == "ack":
            print("recv\tack\t#{}\t".format(packet.seq_num))
            return packet
        else:
            return None

    def update_congestion_window(self):
        if self.ack_number == self.target_ack_number:
            # update window
            self.congestion_window = self.congestion_window * 2 \
            if self.congestion_window < self.threshold else self.congestion_window + 1
            # update new target ack number
            self.target_ack_number = self.target_ack_number + self.congestion_window
            
    def loss_timeout_update_congestion_window(self):
        self.threshold = max(self.congestion_window // 2, 1)
        self.congestion_window = 1
        # update target ack
        self.target_ack_number = self.base + self.congestion_window - 1
        # reset next sequence number
        self.nextseqnum = self.base 

    def check_timeout(self):
        '''
        timeout
            1. restart timer
            2. reset congestion window
            3. resend all packets
        '''
        if self.timer_start and time.time() - self.timer > 1:
            # restart timer
            self.timer = time.time()
            # reset congestion window 
            self.loss_timeout_update_congestion_window()
            # print message
            print("time\tout, threshold = {}".format(self.threshold))
            # resend window packet 
            for i in range(self.base, self.base + self.congestion_window):
                self.sendto(i)
                self.nextseqnum += 1

    def send_fin(self):
        packet = Packet(None, "fin", None)
        self.sock_send.sendto(pickle.dumps(packet), (self.agent_ip, self.agent_port))
        print("send\tfin")

    def send_finack(self):
        packet = Packet(None, "finack", None)
        self.sock_send.sendto(pickle.dumps(packet), (self.agent_ip, self.agent_port))
        print("send\tfinack")
    
    def recv_fin(self):
        while True:
            packet, addr = self.sock_recv.recvfrom(self.receive_size)
            packet = pickle.loads(packet)
            if packet.type == "fin":
                print("recv\tfin")
                break

    def recv_finack(self):
        while True:
            packet, addr = self.sock_recv.recvfrom(self.receive_size)
            packet = pickle.loads(packet)
            if packet.type == "finack":
                print("recv\tfinack")
                break

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="file")
    parser.add_argument("--IP", type=str, help="IP", default="127.0.0.1")
    parser.add_argument("--send_port", type=int, help="port", default=5005)
    parser.add_argument("--recv_port", type=int, help="port", default=5006)
    parser.add_argument("--threshold", type=int, help="threshold", default=16)
    
    args = parser.parse_args()
    # 
    sender = Sender(args)

    # run sender process
    while True:
        # sender send data to agent process
        while sender.nextseqnum < sender.base + sender.congestion_window \
            and sender.nextseqnum < len(sender.packets):
            # 
            sender.sendto(sender.nextseqnum)

            # if it is the first packet to send in this window
            if sender.base == sender.nextseqnum:
                # record target ack number
                sender.target_ack_number = sender.base + sender.congestion_window - 1
                # start timer
                sender.timer_start = True
                sender.timer = time.time()
            # move to next sequence number
            sender.nextseqnum += 1
        #pdb.set_trace()
        # timeout
        sender.check_timeout()
        
        # sender receive ack from agent
        while True:
            ready = select.select([sender.sock_recv], [], [], 0.)
            if ready[0]:
                # check a ack package
                packet = sender.recvfrom()
                if packet is not None and packet.type == "ack":
                    # store largest ack
                    sender.ack_number = packet.seq_num
                    sender.base = sender.ack_number + 1

                    # update congestion window
                    sender.update_congestion_window()

                    if sender.base == sender.nextseqnum:
                        sender.timer_start = False
                    else:
                        # restart timer
                        sender.timer_start = True
                        sender.timer = time.time()
            else:
                break
        # if done
        if sender.ack_number == len(sender.packets) - 1:
            break

    # send fin
    sender.send_fin()
    sender.recv_finack()
    sender.recv_fin()
    sender.send_finack()
    time.sleep(2)
    
    


if __name__ == '__main__':
    import sys, traceback, pdb
    try:
        main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)

