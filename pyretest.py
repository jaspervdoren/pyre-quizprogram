from pyre import Pyre
from pyre import zhelper
from pyre import pyre_peer
import zmq
import json
import uuid
import logging
import sys
import random


	


def chat_task(ctx,pipe):
	print("communication started")

	GROUPNAME = "Quizzzzz"
	StopCmnd = "$$quit"
	OPPONENT = "opponent"
	
	print("name: %s" %NAME)
	
	connected_players = 1
	
	# set up node for the user
	n = Pyre(GROUPNAME)
	n.set_header('Name', NAME)
	
	# join the groupchat
	n.join(GROUPNAME)
	#print("UUID %s" %n.uuid())
	 
				
	# start broadcasting signal 
	n.start()

	# set up poller
	poller = zmq.Poller()
	poller.register(pipe,zmq.POLLIN)
	poller.register(n.socket(),zmq.POLLIN)

	# looping constantly to recieve messages
	while True:
		items = dict(poller.poll())
		
		if pipe in items:
			message = pipe.recv()
			if message.decode('utf-8') == StopCmnd:
				break
			# uppercase letters for question to whole group
			elif message.decode('utf-8').isupper() == True: 
				print("Question is: %s" %message)
				n.shouts(GROUPNAME,"Question to group is: %s" %message.decode('utf-8'))
				answer = 0
			# lowercase to last person who asked question in the group
			elif message.decode('utf-8').islower()  == True:
				message = NAME + "'s answer is=" + message
				n.whisper(PEER,message)
			else:
				print("please don't mix up or lowercase or use not only numbers")
	
		else:
			msgrecv = n.recv()
			#print(msgrecv)
			msg_type = msgrecv.pop(0)
			msg_sender = uuid.UUID(bytes=msgrecv.pop(0))
			PEER = msg_sender
			msg_name = msgrecv.pop(0)

			if msg_type.decode('utf-8') == "ENTER":
				headers = json.loads(msgrecv.pop(0).decode('utf-8'))
				print("New player discovered in network")
				print("New player = %s " %headers.get("Name"))
			elif msg_type.decode('utf-8') == "JOIN":
				print("New player has joined the group")
				print("New player = %s" %headers.get("Name"))
				connected_players += 1
				print("#players = %s" %connected_players)
			elif msg_type.decode('utf-8') == "SHOUT":
				print(msgrecv.pop(1))
			elif msg_type.decode('utf-8') == "WHISPER":
				if msgrecv[0] == "You have to ask next question":
					print("You have to ask next question")
					n.shout(GROUPNAME, "%s is new quizmaster" %NAME)
					answer = 0
				else:
					print(msgrecv.pop(0))
					answer +=1
					if answer == connected_players -1: #choosing new quizmaster randomly
						players = n.peers()
						next_master = players.pop(random.randint(0,connected_players-2))
						n.whisper(next_master,"You have to ask next question")
			
	
	print("Left current game")	
	n.stop()

if __name__ == '__main__':
	
	#for logging (debugging)
	logger = logging.getLogger("pyre")
	logger.setLevel(logging.INFO)
	logger.addHandler(logging.StreamHandler())
	logger.propagate = False

	ctx = zmq.Context()
	NAME = raw_input("username:")
	chat_pipe = zhelper.zthread_fork(ctx, chat_task)
	
	

	while True: 
		try:
			msg = raw_input()
			chat_pipe.send(msg.encode('utf-8'))
		except(KeyboardInterrupt, SystemExit):
			break
	chat_pipe.send(StopCmnd.encode('utf-8'))
	print("Leaving current game")


	
	
