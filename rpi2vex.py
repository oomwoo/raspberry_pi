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

import serial, time, sys, getopt, picamera, glob, re, subprocess, os
import threading
import picamera.array
import numpy as np
from PIL import Image
from neon.util.argparser import NeonArgparser
from neon.backends import gen_backend
from neon.layers import Affine, Conv, Pooling, GeneralizedCost
from neon.models import Model
from neon.transforms import Rectlin, Softmax
from neon.initializers import Uniform
from neon.data.dataiterator import ArrayIterator


# Neural network args
parser = NeonArgparser(__doc__)
args = parser.parse_args()
args.batch_size = 1

# Communication and camera args
debug = True
fps = 90
w = 160
h = 120
quality = 23
bitrate = 0
file_name_prefix = "rec"
hor_flip = False
ver_flip = False
video_file_ext = ".h264"
log_file_ext = ".txt"
log_file = []
iso = 0
shutdown_on_exit = False
rpi_hw_version = 2
autonomous = False
video_file_name = []
log_file_name = []
autonomous_thread = []

# CNN setup
W = 32
H = W
param_file_name = "model\trained_bot_model_32c5516p22c3332p22a50e30_0.1err.prm"
# param_file_name = "model\trained_bot_model.prm"
class_names = ["forward", "left", "right", "backward"]    # from ROBOT-C bot.c
nclass = len(class_names)
be = gen_backend(backend='cpu', batch_size=1)    # NN backend
init_uni = Uniform(low=-0.1, high=0.1)           # Unnecessary NN weight initialization
bn = True                                        # enable NN batch normalization
layers = [Conv((5, 5, 16), init=init_uni, activation=Rectlin(), batch_norm=bn),
          Pooling((2, 2)),
          Conv((3, 3, 32), init=init_uni, activation=Rectlin(), batch_norm=bn),
          Pooling((2, 2)),
          Affine(nout=50, init=init_uni, activation=Rectlin(), batch_norm=bn),
          Affine(nout=nclass, init=init_uni, activation=Softmax())]
#model = Model(param_file_name)
model = Model(layers=layers)
model.load_params(param_file_name, load_states=False)
L = W*H*3
size = H, W

#def usage():
#    print "python connect_to_vex_cortex.py"
#    print "  Raspberry Pi records video, commands from VEX Cortex 2.0"
#    print "  -p " + file_name_prefix + ": file name prefix"
#    print "  -d: display received commands for debug"
#    print "  -w " + str(w) + ": video width"
#    print "  -h " + str(h) + ": video height"
#    print "  -f " + str(fps) + ": video FPS, 0 for camera default"
#    print "  -q " + str(quality) + ": quality to record video, 1..40"
#    print "  -b " + str(bitrate) + ": bitrate e.g. 15000000, 0 for unlimited"
#    print "  -i " + str(iso) + ": ISO 0 | 100 ... 800, see picamera doc, 0 for camera default"
#    print "  -m: horizontal mirror"
#    print "  -v: vertical mirror"
#    print "  -s: shut down system on exit (must run as super user)"
#    print "  -r 2: Raspberry Pi board version 2 | 3"
#    print "  -?: print usage"


class AutonomousThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        debug_print("Autonomous thread init")
        # TODO
    def run(self):
        cnt = 0
        while True:
            if not autonomous:
                debug_print("Exiting autonomous thread")
                break
            # debug Tx
            # send_cmd(0)
            # time.sleep(2)            
            # send_cmd(1)
            # time.sleep(2)
            # send_cmd(2)
            # time.sleep(2)
            # send_cmd(3)
            # time.sleep(2)

            # Grab a still frame
            stream = picamera.array.PiRGBArray(camera)
            camera.capture(stream, 'rgb', use_video_port=True)

            start_time = time.time()
            debug_print("Grabbed a still frame")
            image = Image.fromarray(stream.array)
            image = image.resize(size, Image.ANTIALIAS)
            if (debug):
                image.save("debug\capture" + str(cnt) + ".png", "PNG")
                cnt = cnt+1
            image = np.asarray(image, dtype=np.float32)

            # Run neural network
            x_new = np.zeros((1, L), dtype=np.float32)
            x_new[0] = image.reshape(1, L) # / 255
            inference_set = ArrayIterator(x_new, None, nclass=nclass, lshape=(3, H, W))
            out = model.get_outputs(inference_set)
            debug_print("--- %s seconds per decision --- " % (time.time() - start_time))
            decision = out[0].argmax()
            debug_print(class_names[decision])
            send_cmd(decision)


def get_file_max_idx(prefix, file_ext):
    rs = "[0-9][0-9][0-9][0-9][0-9]"
    file_names = glob.glob(prefix + rs + file_ext)
    if not file_names:
        return 0
    numbers = [int((re.findall('\d+', s))[0]) for s in file_names]
    return max(numbers) + 1


def start_recording():
    global log_file, video_file_name, log_file_name
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


def enable_autonomous_driving(enable):
    global autonomous, autonomous_thread
    if (not autonomous) and enable:
        # going autonomous?
        # Stop recording
        stop_recording()
        # camera.start_preview()
        # configure capturing frames into buffer (not on disk)
        autonomous = True
        autonomous_thread = AutonomousThread()
        autonomous_thread.start()
    elif autonomous and not enable:
        # going manual
        # camera.stop_preview()
        autonomous = False
        autonomous_thread.join()
        debug_print("Autonomous thread has terminated")
        autonomous_thread = []


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


def send_cmd(cmd_code):
    cmd = 'c' + format(cmd_code, '02X') + '\n'
    port.write(cmd)
    debug_print("Sent cmd=" + cmd)


# def decide_what_to_do():
#     # get camera picture
#     stream = picamera.array.PiRGBArray(camera)
#     camera.capture(stream, 'rgb', use_video_port=True)
#     print(stream.array.shape)
#
#     # run neural network
#    
#     # encode command
#    
#     return "A00"


#opts, args = getopt.getopt(sys.argv[1:], "p:l:w:h:f:q:b:i:r:?ds")
#for opt, arg in opts:
#    if opt == '-d':
#        debug = True
#    elif opt == '-l':
#        log_file_name = arg
#    elif opt == '-w':
#        w = int(arg)
#    elif opt == '-h':
#        h = int(arg)
#    elif opt == '-f':
#        fps = int(arg)
#    elif opt == '-q':
#        quality = int(arg)
#    elif opt == '-b':
#        bitrate = int(arg)
#    elif opt == '-i':
#        fps = int(arg)
#    elif opt == '-p':
#        file_name_prefix = arg
#    elif opt == '-m':
#        hor_flip = Not(hor_flip)
#    elif opt == '-v':
#        ver_flip = Not(ver_flip)
#    elif opt == '-r':
#        rpi_hw_version = int(arg)
#    elif opt == '-?':
#        usage()
#        sys.exit(2)

if rpi_hw_version == 2:
    tty_name = "/dev/ttyAMA0"
#elif rpi_hw_version == 3:
#    tty_name = "/dev/ttyS0"
else:
    print "Unsupported Raspberry Pi board version " + str(rpi_hw_version) + " Only rpi v2 is supported"
    exit()

port = serial.Serial(tty_name, baudrate=115200, timeout=3.0)

camera = picamera.PiCamera()
camera.resolution = (w, h)
if fps > 0:
    camera.framerate = fps
if iso > 0:
    camera.iso = iso
camera.hflip = hor_flip
camera.vfilp = ver_flip
camera.led = False
camera.exposure_mode = 'fixedfps'

while True:
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

        # autonomous mode - ignore all commands except return to Manual Control
        if autonomous and not val == 1:
            pass
        
        if val == 255:
            # LFF: terminate link (this script quits)
            debug_print("Terminating link")
            break
        elif val == 1:
            # L01: stop autonomous (manual control)
            debug_print("Transferring control to human")
            enable_autonomous_driving(False)
        elif val == 2:
            # L02: transfer control to robot (autonomous control)
            debug_print("Transferring control to robot")
            enable_autonomous_driving(True)
        elif val == 3:
            # L03: start recording
            if not autonomous and start_recording():
                write_to_log(rcv)
        elif val == 4:
            # L04: stop capture
            if camera.recording():
                stop_recording()
        elif val == 253:
            # LFD: discard current recording (if human made a mistake in training)
            if camera.recording():
                debug_print("Discarding current recording")
                stop_recording()
                # Delete video and associated log
                os.remove(video_file_name)
                os.remove(log_file_name)
                # Resume recording
                if start_recording():
                    write_to_log(rcv)
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
enable_autonomous_driving(False)
