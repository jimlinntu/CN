import socket

HOST = "irc.freenode.net"
CHAN = "#CN2017"
NICK = "Robot_Jim"
IDENT = "jim"
PORT = 6667
BUF_SIZE = 4096
readbuffer = ""
REALNAME = "Jim"

def res_handler(socket, query, msg, channel=CHAN):
	'''
	query = ["#CN2017", ":@command", "<Input>", ...]
	'''
	# check channel
	if channel != query[0]:
		return
	# when len is less than 2
	if len(query) == 2:
		if query[1] == ":@help":
			mesg = "@repeat <Message>"
			send(socket, "PRIVMSG %s :%s" % (channel, mesg))
			mesg = "@convert <Number>"	
			send(socket, "PRIVMSG %s :%s" % (channel, mesg))
			mesg = "@ip <String>"		
			send(socket, "PRIVMSG %s :%s" % (channel, mesg))
		return
	# if less than 3 query, return 
	if len(query) < 3:
		return
	if query[1] == ":@repeat":
		begin = msg.find(':@repeat') + len(":@repeat")
		# deal with many whitespaces
		user_msg = msg[begin:].strip()
		print "Receive \'repeat\' command \"{}\"".format(user_msg)		
		send(socket, "PRIVMSG %s :%s" % (channel, user_msg))
	elif query[1] == ":@convert":
		num = None
		# try to convert it to decimal first
		try:
			num = int(query[2], 10)	
		# if not, it is a hex
		except ValueError:
			print "Value error"
			pass
		if num == None:
			try:
				num = int(query[2], 16)
			except ValueError:
				send(socket, "PRIVMSG %s :%s" % (channel, "Don't cheetme baby!"))
				return
		else:
			try:
				num = hex(num)
			except ValueError:		
				send(socket, "PRIVMSG %s :%s" % (channel, "Don't cheetme baby!"))
				return
		print "Receive \'convert\' command {}".format(num)
		send(socket, "PRIVMSG %s :%s" %(channel, num))
	elif query[1] == ":@ip":
		try:
			legal_ip = ipcheck(query[2])
		except ValueError:
			send(socket, "PRIVMSG %s :%s" % (channel, "Don't cheetme baby!"))
			return
		send(socket, "PRIVMSG %s :%d" % (channel, len(legal_ip)))
		for i, ip in enumerate(legal_ip):
			send(socket, "PRIVMSG {} {}".format(channel,ip))

def ipcheck(string):
	try:
		int(string)
	except ValueError:
		raise ValueError
		return
	# check ip v4 available
	legal_ip = []
	string = list(string)
	print string
	def recursive(now_index, now_string, legal_ip):
		if len(now_string) == 4:
			legal_ip.append('.'.join(now_string))
			return
		if now_index >= len(string):		
			return
		# traverse child
		if len(now_string) == 3:
			num = int(''.join(string[now_index:]))
			if num < 256:
				now_string.append(str(num))
				recursive(len(string)+1, now_string, legal_ip)
				now_string.pop()
		else:
			for i in range(now_index, len(string)):
				if int(''.join(string[now_index:i+1])) < 256:
					now_string.append(''.join(string[now_index:i+1]))
					recursive(i+1, now_string, legal_ip)
					now_string.pop()
	now_string = []	
	recursive(0, now_string, legal_ip)
	print "legal move has {} ".format(len(legal_ip))
	print "all possible ip {}".format(legal_ip)
	return legal_ip

def receive(socket, bufsize=BUF_SIZE):
	msg = socket.recv(bufsize)	
	return msg

def send(socket, msg):
	socket.send(bytes(msg + "\r\n"))
 
def join(socket, channel=CHAN):
	send(socket, "JOIN "+ str(channel))
	send(socket, "PRIVMSG %s :%s" % (channel, "Hello! I am robot."))
	print "Join " + str(channel)
	
def login(socket):	
	socket.connect(("irc.freenode.net",PORT))	
	send(socket, "NICK {}".format(NICK))		
	send(socket, "USER %s %s bla :%s" % (IDENT, HOST, REALNAME))
	print "Login done......."

def main():
	# read config file
	global CHAN
	with open("./config", "r") as f:
		for line in f:
			CHAN = line[line.find("\'"):]
			CHAN = CHAN.strip('\n').strip('\'')
			print CHAN
	IRCSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	# login to HOST
	login(IRCSocket)
	
	# join channel
	join(IRCSocket, CHAN)

	while 1:
		# receive data from chat
		msg = receive(IRCSocket)
		# parse message
		msgsplit = msg.split()
		print msg
		if msgsplit[0] == "PING":
			print "PING it"
			send(IRCSocket, "PONG %s" % msgsplit[1])
		elif msgsplit[1] == "PRIVMSG":
			res_handler(IRCSocket, msgsplit[2:], msg, CHAN)
				

		
if __name__ == "__main__":
	main()
