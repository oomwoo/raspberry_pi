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

import serial, time, sys, getopt, picamera, glob, re

debug = False
fps = 90
w = 320
h = 240
quality = 23
bitrate = 0
file_name_prefix = "rec"
hor_flip = False
ver_flip = False
video_file_ext = ".h264"
log_file_ext = ".txt"
log_file = []
iso = 800

def usage():
    print "python connect_to_vex_cortex.py"
    print "  Raspberry Pi records video, commands from VEX Cortex 2.0"
    print "  -p rec: file name prefix"
    print "  -d: display received commands for debug"
    print "  -w 320: video width"
    print "  -h 240: video height"
    print "  -f 90: video FPS, 0 for camera default"
    print "  -q 23: quality to record video, 1..40"
    print "  -b 0: bitrate e.g. 15000000, 0 for unlimited"
    print "  -i 800: ISO 100 | 200 | 400 | 800, 0 default"
    print "  -m: horizontal mirror"
    print "  -v: vertical mirror"
    print "  -?: print usage"

def get_file_max_idx(prefix, file_ext):
    rs = "[0-9][0-9][0-9][0-9][0-9]"
    file_names = glob.glob(prefix + rs + file_ext)
    if not file_names:
        return 0
    numbers = [int((re.findall('\d+', s))[0]) for s in file_names]
    return max(numbers) + 1

def start_recording():
    global log_file
    if not(camera.recording):
        n1 = get_file_max_idx(file_name_prefix, video_file_ext)
        n2 = get_file_max_idx(file_name_prefix, log_file_ext)
        n = max(n1, n2)
        s = str(n).zfill(5)
        video_file_name = file_name_prefix + s + video_file_ext
        log_file_name = file_name_prefix + s + log_file_ext
        camera.start_recording(video_file_name, quality=quality)
        log_file = open(log_file_name, "w")
        camera.led = True

        debug_print("Recording to " + log_file_name)
        return True
    else:
        return False

    
def stop_recording():
    global log_file
    if camera.recording:
        debug_print("Stopping recording")
        camera.stop_recording()
        log_file.close()
        camera.led = False


def write_to_log(txt):
    if camera.recording:
        # Prepend timestamp
        s = repr(time.time()) + " " + txt
        # Save all commands into log file
        debug_print(s)
        log_file.write(s)


def debug_print(s):
    if debug:
        print(s)


opts, args = getopt.getopt(sys.argv[1:], "p:l:w:h:f:q:b:i:?d")

for opt, arg in opts:
    if opt == '-d':
        debug = True
    elif opt == '-l':
        log_file_name = arg
    elif opt == '-w':
        w = int(arg)
    elif opt == '-h':
        h = int(arg)
    elif opt == '-f':
        fps = int(arg)
    elif opt == '-q':
        quality = int(arg)
    elif opt == '-b':
        bitrate = int(arg)
    elif opt == '-i':
        fps = int(arg)
    elif opt == '-p':
        file_name_prefix = arg
    elif opt == '-m':
        hor_flip = Not(hor_flip)
    elif opt == '-v':
        ver_flip = Not(ver_flip)
    elif opt == '-?':
        usage()
        sys.exit(2)

# Raspberry Pi 2 Model B
port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=3.0)
# TODO detect Raspberry Pi 3
#port = serial.Serial("/dev/ttyS0", baudrate=115200, timeout=3.0)

camera = picamera.PiCamera()
camera.resolution = (w, h)
if fps > 0:
    camera.framerate = fps
if iso > 0:
    camera.iso = iso
camera.hflip = hor_flip
camera.vfilp = ver_flip
camera.led = False

# TODO send something useful
# cmd = "s60\n"

while True:
    # port.write(cmd)
    # print cmd
    rcv = port.readline()
    # print repr(rcv)

    if len(rcv) == 0:
        debug_print("Timeout receiving command")
        continue        
    else:
        write_to_log(rcv)

    # Parse link command, if present
    #   If the link control command is present ('Lxx'),
    # it must be the first command in the received string
    # This is to accelerate Python code running on Raspberry Pi
    # (no need to parse the whole string looking for Lxx)
    if rcv[0] == 'L':
        val = int(rcv[1:3], 16)
        if val == 255:
            # LFF: terminate link (this script quits)
            debug_print("Terminating link")
            break
        elif val == 1:
            # TODO L01: transfer control to human (manual control)
            debug_print("Transferring control to human")
        elif val == 2:
            # TODO L02: transfer control to robot (automomous control)
            debug_print("Transferring control to robot")
        elif val == 3:
            # L03: start recording
            if start_recording():
                write_to_log(rcv)
        elif val == 4:
            # L04: stop capture
            stop_recording()
        elif val == 253:
            # TODO LFD: forget last few seconds (when human made a mistake)
            debug_print("Forgetting a mistake")
        elif val == 254:
            # TODO LFE: terminate training and upload data to server
            debug_print("Terminating link and uploading data")
            break
        else:
            # L00 and otherwise: none (no command)
            debug_print("Unsupported link command or no command")
    else:
        write_to_log(rcv)

stop_recording()
