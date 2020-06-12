import cv2
import numpy as np
import socket
import sys
import pickle
from picamera import PiCamera
import struct ### new code

camera = cv2.VideoCapture(0)

clientsocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
clientsocket.connect(('192.168.31.60',8089))
while True:
    ret,frame=camera.read()
    data = pickle.dumps(frame) ### new code
    clientsocket.sendall(struct.pack("L", len(data))+data) ### new code
