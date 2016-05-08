#!/usr/bin/python
# Connect Raspberry Pi to VEX Cortex using bi-directional UART serial link
# and exchange certain control commands
# This code runs on Raspberry Pi.
# VEX Cortex must be running peer code for the link to operate,
# see https://github.com/oomwoo/vex
#
# Copyright (C) 2016 oomwoo.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3.0 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License <http://www.gnu.org/licenses/> for details.

import serial, time, sys, getopt, picamera

debug = False
fps = 5
w = 160
h = 120

def usage():
    print "python connect_to_vex_cortex.py"
    print "  Communicate with VEX Cortex 2.0 over UART"
    print "  -l log_file_name.txt: specify log filename, default log.txt"
    print "  -d: display received commands for debug"
    print "  -h: print usage"

def start_capture()
    if debug:
        print >> sys.stderr, "Starting capture"
    # TODO
    log_file = open(log_file_name, "a")
    camera.start_recording("video.h264", quality=23)
    
def end_capture()
    if debug:
        print >> sys.stderr, "Stopping capture"
    log_file.close()

# TODO don't overwrite log - append or increment log name

opts, args = getopt.getopt(sys.argv[1:], "ldh")
log_file_name = "log.txt"

for opt, arg in opts:
    if opt == '-d':
        debug = True
    elif opt == '-l':
        log_file_name = arg
    elif opt == '-h':
        usage()
        sys.exit(2)

# Raspberry Pi 2 Model B
port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=3.0)

camera = picamera.PiCamera()
camera.resolution = (w, h)
camera.framerate = fps
camera.hflip = True
camera.vfilp = True

# TODO send something useful
# cmd = "s60\n"

while True:
    # port.write(cmd)
    # print cmd
    rcv = port.readline()
    print repr(rcv)

    if len(rcv) == 0:
        print >> sys.stderr, "Timeout receiving command"
        continue        

    # Prepend timestamp
    s = repr(time.time()) + " " + rcv

    # Save all commands into log file
    log_file.write(s)

    if debug:
        print repr(rcv)

    # Parse link command, if present
    #   If the link control command is present ('Lxx'),
    # it must be the first command in the received string
    # This is to accelerate Python code running on Raspberry Pi
    # (no need to parse the whole string looking for Lxx)
    if rcv[0] == 'L':
        val = int(rcv[1:3], 16)
        if val == 255:
            # LFF: terminate link (this script quits)
            print >> sys.stderr, "Terminating link"
            break
        elif val == 1:
            # TODO L01: transfer control to human (manual control)
            print >> sys.stderr, "Transferring control to human"
        elif val == 2:
            # TODO L02: transfer control to robot (automomous control)
            print >> sys.stderr, "Transferring control to robot"
        elif val == 3:
            # L03: start recording
            start_capture()
        elif val == 4:
            # TODO L04: stop video capture
            print >> sys.stderr, "Stopping video capture"
        elif val == 253:
            # TODO LFD: forget last few seconds (when human made a mistake)
            print >> sys.stderr, "Forgetting a mistake"
        elif val == 254:
            # TODO LFE: terminate training and upload data to server
            print >> sys.stderr, "Terminating link and uploading data"
            break
        else:
            # L00 and otherwise: none (no command)
            print >> sys.stderr, "Unsupported link command or no command"
    
