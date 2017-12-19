from import_modules import *
from packet import Packet
class Agent:
    def __init__(self, args):
        self.loss_prob = args.loss_prob
        self.packet_size = 1000000
        self.receiver_ip = self.sender_ip = self.ip = args.IP
        self.data_port = args.data_port
        self.ack_port = args.ack_port
        self.sender_port = args.sender_port
        self.receiver_port = args.receiver_port
        # create socket
        print("Bind sock_data_from at ", (self.ip, self.data_port))
        self.sock_data_from = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_data_from.bind((self.ip, self.data_port))
        self.sock_data_forward = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("Bind sock_ack_from at ", (self.ip, self.ack_port))
        self.sock_ack_from = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_ack_from.bind((self.ip, self.ack_port))
        self.sock_ack_forward = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # counter
        self.data_counter = 0
        self.drop_counter = 0
    
    def get_packet_and_fwd_from_sender(self):
        while True:
            ready = select.select([self.sock_data_from], [], [], 0.)
            if ready[0]:
                # receive packet
                packet, addr = self.sock_data_from.recvfrom(self.packet_size)
                packet = pickle.loads(packet)
                if packet.type == "data":
                    print("get\t{}\t#{}".format(packet.type, packet.seq_num))
                else:
                    print("get\t{}".format(packet.type))
                # drop and fwd
                self.drop_and_fwd_packet_from_sender(packet)
            else:
                break

    def drop_and_fwd_packet_from_sender(self, packet):
        # if packet is data, data_counter += 1
        if packet.type == "data":
            self.data_counter += 1
        # drop 
        if packet.type == "data" and random.uniform(0, 1) < self.loss_prob:
            print("drop\tdata\t#{}".format(packet.seq_num))
            self.drop_counter += 1
            return True
        else:
            # foward
            self.sock_data_forward.sendto(pickle.dumps(packet), (self.receiver_ip, self.receiver_port))
            if packet.type == "data":
                print("fwd\t{}\t#{},\tloss rate = {}".format(packet.type, packet.seq_num, 
                    self.drop_counter/self.data_counter))
            else:
                print("fwd\t{}".format(packet.type))
            return False

    def get_ack_and_fwd_from_receiver(self):
        while True:
            ready = select.select([self.sock_ack_from], [], [], 0.)
            if ready[0]:
                packet, addr = self.sock_ack_from.recvfrom(self.packet_size)
                packet = pickle.loads(packet)
                if packet.type == "ack":
                    print("get\t{}\t#{}".format(packet.type, packet.seq_num))
                else:
                    print("get\t{}".format(packet.type))
                # foward ack/finack
                self.fwd_ack(packet)
            else:
                break       


    def fwd_ack(self, packet):
        self.sock_ack_forward.sendto(pickle.dumps(packet), (self.sender_ip, self.sender_port))
        if packet.type == "ack":
            print("fwd\t{}\t#{}".format(packet.type, packet.seq_num))
        else:
            print("fwd\t{}".format(packet.type))
        return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--IP", type=str, help="IP", default="127.0.0.1")
    parser.add_argument("--data_port", type=int, help="port", default=5006)
    parser.add_argument("--ack_port", type=int, help="port", default=5008)
    parser.add_argument("--sender_port", type=int, help="port", default=5005)
    parser.add_argument("--receiver_port", type=int, help="port", default=5007)
    parser.add_argument("--loss_prob", type=float, help="loss prob", default=0.5)
    args = parser.parse_args()
    # create Agent
    agent = Agent(args)
    # Run agent process
    while True:
        # get and forward from sender
        agent.get_packet_and_fwd_from_sender()
        # get and forward from receiver
        agent.get_ack_and_fwd_from_receiver()


if __name__ == '__main__':
    import sys, traceback, pdb
    try:
        main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)