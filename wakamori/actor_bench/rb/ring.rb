require 'actor'
include Actor

def endAll(msg)
	exit
end

def exitRing(msg)
	name = msg[0]
	actor_num = msg[1]
	actor_count = msg[2]
	if actor_num != actor_count
		actor_num += 1
		sendToActor(name + actor_num.to_s, 'exitRing', [name, actor_num, actor_count])
	else
		sendToActor('kick', 'endAll', '')
	end
	#exitActor()
	exit
end

def receive(msg)
	name = msg[0]
	actor_num = msg[1]
	actor_count = msg[2]
	loop_count = msg[3]
	if actor_num == actor_count
		loop_count -= 1
		actor_num = 1
		if loop_count == 0
			sendToActor(name + actor_num.to_s, 'exitRing', [name, actor_num, actor_count])
		end
	else
		actor_num += 1
	end
	sendToActor(name + actor_num.to_s, 'receive', [name, actor_num, actor_count, loop_count])
end

def main(actor_count, loop_count)
	port = 12345
	for i in 1..actor_count
		name = 'actor' + i.to_s
		spawn(name, port)
		port += 1
	end
	sendToActor('actor1', 'receive', ['actor', 1, actor_count, loop_count])
	act('kick', port)
end

if __FILE__ == $0
	actor_count = ARGV[0] == nil ? 3 : ARGV[0].to_i
	loop_count = ARGV[1] == nil ? 100 : ARGV[1].to_i
	main(actor_count, loop_count)
end
