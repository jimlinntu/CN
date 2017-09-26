import socket

HOST = "irc.freenode.net"
PORT = 6667
CHAN = "#CN2017"
NICK = "Robot_Jim"
IDENT = "jim"
BUF_SIZE = 4096
readbuffer = ""
REALNAME = "Jim"

def res_handler(socket, query, channel=CHAN):
	if len(query) < 3:
		return 
	# check channel
	if channel != query[0]:
		return
	if query[1] == ":@repeat":
		
		send(socket, "PRIVMSG %s %s" % (channel, query[2]))
	elif query[1] == ":@convert":
		pass
	elif query[1] == ":@ip":
		pass	
	elif query[1] == ":@help":
		msg = "@repeat <Message>\n@convert <Number>\n@ip <String>"
		send(socket, "PRIVMSG %s %s" % (channel, msg))

def receive(socket, bufsize=BUF_SIZE):
	msg = socket.recv(bufsize)	
	return msg

def send(socket, msg):
	socket.send(bytes(msg + "\r\n"))
 
def join(socket, channel=CHAN):
	send(socket, "JOIN "+ str(channel))
	print "Join " + str(channel)
	
def login(socket):	
	socket.connect(("irc.freenode.net",PORT))	
	send(socket, "NICK {}".format(NICK))		
	send(socket, "USER %s %s bla :%s" % (IDENT, HOST, REALNAME))
	print "Login done......."

def main():
	IRCSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	# login to HOST
	login(IRCSocket)
	
	# join channel
	join(IRCSocket, CHAN)

	while 1:
		# receive data from chat
		msg = receive(IRCSocket)
		# parse message
		msg = msg.split()
		print msg
		if msg[0] == "PING":
			send(IRCSocket, "PONG %s" % msg[1])
		elif msg[1] == "PRIVMSG":
			res_handler(IRCSocket, msg[2:], CHAN)
				

		
if __name__ == "__main__":
	main()
