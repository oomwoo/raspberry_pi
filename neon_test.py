#!/usr/bin/env python
# Train robot to drive autonomously using Nervana Neon
# See more at https://github.com/oomwoo/
#
# Copyright (C) 2016 oomwoo.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3.0
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License <http://www.gnu.org/licenses/> for details.
"""
Train robot to drive autonomously. Use a small convolutional neural network.
"""

import picamera
import picamera.array
import numpy as np
from PIL import Image

fps = 90
w = 320
h = 240
l = 64
W = 64 # CNN input image size
H = 64
param_file_name = "trained_bot_model.prm"
nclass = 4

camera = picamera.PiCamera()
camera.resolution = (w, h)
camera.framerate = fps
camera.exposure_mode = 'fixedfps'

# Capture camera picture into numpy array
stream = picamera.array.PiRGBArray(camera)
camera.capture(stream, 'rgb', use_video_port=True)
print(stream.array.shape)
camera.close()

# Resize image
image = Image.fromarray(stream.array)
size = H, W
image = image.resize(size, Image.ANTIALIAS)
image = np.asarray(image, dtype=np.float32)

# run neural network

# parse the command line arguments
from neon.util.argparser import NeonArgparser
parser = NeonArgparser(__doc__)
args = parser.parse_args()
args.batch_size = 1

# Set up backend for inference
from neon.backends import gen_backend
be = gen_backend(backend='cpu', batch_size=1)

from neon.layers import Affine, Conv, Pooling, GeneralizedCost
from neon.models import Model
from neon.transforms import Rectlin, Softmax
from neon.initializers import Uniform
from neon.data.dataiterator import ArrayIterator

init_uni = Uniform(low=-0.1, high=0.1)

bn = True
layers = [Conv((5, 5, 16), init=init_uni, activation=Rectlin(), batch_norm=bn),
          Pooling((2, 2)),
          Conv((5, 5, 32), init=init_uni, activation=Rectlin(), batch_norm=bn),
          Pooling((2, 2)),
          Affine(nout=100, init=init_uni, activation=Rectlin(), batch_norm=bn),
          Affine(nout=4, init=init_uni, activation=Softmax())]

#model = Model(param_file_name)
model = Model(layers=layers)
model.load_params(param_file_name, load_states=False)


L = W*H*3
x_new = np.zeros((1, L), dtype=np.float32)
x_new[0] = image.reshape(1, L) # / 255

inference_set = ArrayIterator(x_new, None, nclass=nclass, lshape=(3, H, W))

# from ROBOT-C bot.c
classes = ["forward", "left", "right", "backward"]

import time
start_time = time.time()
out = model.get_outputs(inference_set)
print "--- %s seconds --- " % (time.time() - start_time)
print classes[out[0].argmax()]
