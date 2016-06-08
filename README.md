# raspberry_pi

Do-it-yourself basic, yet fully autonomous robot

- uses Raspberry Pi model 2 with camera to image surroundings and decide where to drive
- decision engine is a rudimentary convolutional neural network, runs on Nervana Neon on Raspberry Pi
- "teach" the robot by recording videos of how to drive properly, uploading videos to a training server, training CNN using Nervana Neon to generate a trained CNN model

Operate a VEX EDR robot manually and autonomously. This robot's base and drive is built from VEX components, uses VEX Cortex (ARM-based) CPU and a couple of motors. The Cortex must be connected to a properly-configured Raspberry Pi over serial UART link.

This repository contains files for Raspberry Pi. For VEX and CNN training code, see my other repositories under https://github.com/oomwoo/

[Work in progress 2016 June]
