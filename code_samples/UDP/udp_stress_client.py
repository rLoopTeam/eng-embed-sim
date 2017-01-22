# udp_stress_client.py by Eli Fulkerson
# http://www.elifulkerson.com for updates and documentation
# You will also need udp_stress_server.py for this to do anything for you.

# "Push it to the limit!"

# This is an extremely quick-and-dirty UDP testing utility.
# All it does is shove a bunch of UDP traffic through to the server, which
# records and reports the amount of data successfully recieved and the time
# that the transmission took.  It spits out the ratio to give a rough kbps
# estimate.

# The results are very dependent on how much data you push through.  Low amounts
# of data will give you artificially low results.

# "Safety is not guaranteed."

# June 24 2006


from socket import *
import string
import time

# REMEMBER TO SPECIFY THE PROPER DETINATION HOST HERE...
# 'host' should be the address that the server half of this is running on
host = "localhost"

# if you change the port, change it on the server side as well
#port = 8106
port = 8888

UDPSock = socket(AF_INET,SOCK_DGRAM)

print "\n"
print "-" * 40
print "udp_stress_client.py"
print "Updates and documentation (if any) at http://www.elifulkerson.com"
print "-" * 40

print "\nStarting client end.  Control-C to quit."

print "\nOur target:"
print "udp_stress_server.py running on %s port %s" % (host, port)

print "\n\nEnter number of bytes to send and the number of times to send them:\n(for instance '100 10' to send 10 bursts of 100 bytes each)";

while (1):
	data = raw_input('% ')
	args = string.split(data)

	try:
                if args[0] == "reset":
                    data = "X"
                    numtimes = 1
                else:            
                    data = "X" * int(args[0])
                    numtimes = int(args[1])
        except:
                data = None
                numtimes = None
                print "Error, you need to specify two numbers.  First the number of bytes to send, second the number of times to send them."
                
	if not data:
		pass
	else:
            try:
                #the resetter...
                UDPSock.sendto("X", (host,port))
                
                for x in range(numtimes):
        		if(UDPSock.sendto(data,(host,port))):
                            print "*",
                        else:
                            print "."
                            
                        # a pause via time.sleep()
                        # not sure that this is needed.  Put it here to play with maybe not-overloading the
                        # windows tcp/ip stack, but not sure if it actually has any noticable effect.
                        time.sleep(0.0001)
                print "Done."

            except:
                print "Send failed"


UDPSock.close()
