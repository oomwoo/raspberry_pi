import picamera, time

# picamera.readthedocs.io

camera = picamera.PiCamera()

camera.resolution = (160, 120)
camera.framerate = 5
camera.hflip = True
camera.vfilp = True

camera.start_recording("video.h264", quality=23)
time.sleep(5)

camera.stop_recording()
camera.close()
