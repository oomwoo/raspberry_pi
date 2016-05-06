import serial

port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=3.0)

cmd = "s60\n"

while True:
    port.write(cmd)
    print cmd
    rcv = port.readline()
#    rcv = port.read(10)
    print "You sent: ", repr(rcv)