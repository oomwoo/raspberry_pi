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

import serial, time, sys, getopt, glob, re, subprocess, os
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

# CNN setup
W = 32
H = W
test_file_name = "../../ubuntu/dataset/0/00002245.jpg"
# test_file_name = "../../ubuntu/dataset/1/00006027.jpg"
# test_file_name = "../../ubuntu/dataset/2/00016592.jpg"
# test_file_name = "../../ubuntu/dataset/3/00014907.jpg"
param_file_name = "../trained_bot_model_32c5516p22c3332p22a50e30_0.1err.prm"
# param_file_name = "trained_bot_model.prm"
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
model = Model(layers=layers)
model.load_params(param_file_name, load_states=False)
L = W*H*3
size = H, W


image = Image.open(test_file_name)
# pix = image.load()
# print(pix[1,1])
print("Loaded " + test_file_name)
start_time = time.time()
image = image.resize(size, Image.ANTIALIAS)
# pix = image.load()
# print(pix[1,1])
image = np.asarray(image, dtype=np.float32)
image = image - (104.412277, 119.213318, 126.806091)
print image

# Run neural network
x_new = np.zeros((1, L), dtype=np.float32)
x_new[0] = image.reshape(1, L) / 255
# print x_new
inference_set = ArrayIterator(x_new, None, nclass=nclass, lshape=(3, H, W))
out = model.get_outputs(inference_set)
print("--- %s seconds per decision --- " % (time.time() - start_time))
print out
decision = out[0].argmax()
print(class_names[decision])
