from import_modules import *
from packet import Packet
class Receiver:
    def __init__(self, args):
        # buffer and data 
        self.buf_size = 32
        self.buf_list = []
        self.file = b''
        self.filename = None

        self.agent_ip = self.ip = args.IP
        self.port = args.recv_port
        self.agent_port = args.agent_port

        self.sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_recv.bind((self.ip, self.port))
        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.packet_size = 1000000
        # inital ack is -1
        self.ack_number = -1

    def write_file(self, file_path, ext):
        with open(file_path + ext, "wb") as f:
            f.write(self.file)

    def recv_data(self):
        ready = select.select([self.sock_recv], [], [], 0.)
        # Receive one packet
        if ready[0]:
            packet, addr = self.sock_recv.recvfrom(self.packet_size)
            packet = pickle.loads(packet)
        else:
            return None
        '''
        if it is right sequence number
            1. put it into the buffer (if buffer is full, flush to file)
            2. send ack back
            3. add cumulative seq number
        else:
            1. send now ack number
        '''
        if packet.type == "fin":
            self.send_finack()
            return "fin"
        elif packet.type == "data":
            # get filename
            if self.filename is None:
                self.filename = packet.filename
            # if it is the right packet
            if packet.seq_num == self.ack_number + 1:
                # Until lose a packet, flush them to file
                if len(self.buf_list) == self.buf_size:
                    # flush to file
                    self.file += b''.join(self.buf_list)
                    self.buf_list = []
                    # drop packet
                    print("drop\tdata\t#{}".format(packet.seq_num))
                    # send accumulate ack number
                    self.send_ack(self.ack_number)
                    print("flush")
                else:
                    # receive data
                    print("recv\tdata\t#{}".format(packet.seq_num))
                    self.buf_list.append(packet.data)
                    # send ack sequence number
                    self.send_ack(packet.seq_num)
                    # accumulate ack
                    self.ack_number += 1
    
            elif packet.type == "data":
                print("drop\tdata\t#{}".format(packet.seq_num))
                # send duplicate ack
                self.send_ack(self.ack_number)
      
            return "data"
        


    def send_ack(self, ack_number):
        packet = Packet(ack_number, "ack", None)
        self.sock_send.sendto(pickle.dumps(packet), (self.agent_ip, self.agent_port))
        print("send\tack\t#{}".format(ack_number))

    def send_finack(self):
        packet = Packet(None, "finack", None)
        self.sock_send.sendto(pickle.dumps(packet), (self.agent_ip, self.agent_port))
    def send_fin(self):
        packet = Packet(None, "fin", None)
        self.sock_send.sendto(pickle.dumps(packet), (self.agent_ip, self.agent_port))
        print("send\tfin")
    def recv_finack(self):
        while True:
            packet, addr = self.sock_recv.recvfrom(self.packet_size)
            packet = pickle.loads(packet)
            if packet.type == "finack":
                print("recv\tfinack")
                break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", type=str, help="file")
    parser.add_argument("--IP", type=str, help="IP", default="127.0.0.1")
    parser.add_argument("--recv_port", type=int, help="port", default=5007)
    parser.add_argument("--agent_port", type=int, help="port", default=5008)

    args = parser.parse_args()
    receiver = Receiver(args)
    while True:
        # receive data
        packet_type = receiver.recv_data()
        # if fin break
        if packet_type == "fin":
            break
    # wait for a while
    time.sleep(5)
    receiver.send_fin()
    receiver.recv_finack()
    # flush packet
    receiver.file += b''.join(receiver.buf_list)
    print("flush")
    # write to file
    receiver.write_file(args.file_path, os.path.splitext(receiver.filename)[-1])
    return 0

if __name__ == '__main__':
    import sys, traceback, pdb
    try:
        main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)