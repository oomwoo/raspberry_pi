# Connect Raspberry Pi to VEX Cortex using bi-directional UART serial link
# and test transmission
# This code runs on Raspberry Pi (tested with Raspberry Pi 2 model B)
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

import serial

port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=3.0)

cmd = "s60\n"

while True:
    port.write(cmd)
    print cmd
    rcv = port.readline()
#    rcv = port.read(10)
    print "You sent: ", repr(rcv)
