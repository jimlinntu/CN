class Packet:
    def __init__(self, seq_num, type, data, filename=None):
        self.seq_num = seq_num
        self.type = type
        self.data = data
        self.filename = filename