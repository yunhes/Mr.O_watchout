# -*- coding: utf-8 -*- 
import socket
import sys
import cv2
import pickle
import numpy as np
import struct ## new
import time
import os
import RPi.GPIO as GPIO

HOST=''
PORT=8089

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print 'Socket created'

s.bind((HOST,PORT))
print 'Socket bind complete'
s.listen(10)
print 'Socket now listening'

conn,addr=s.accept()
pre_frame = None
### new
data = ""
payload_size = struct.calcsize("L")
while True:
    #start = time.time()
    while len(data) < payload_size:
        data += conn.recv(4096)
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("L", packed_msg_size)[0]
    while len(data) < msg_size:
        data += conn.recv(4096)
    frame_data = data[:msg_size]
    data = data[msg_size:]
    ###
    fps = 30
    #pre_frame = None
     
    start = time.time()
    cur_frame=pickle.loads(frame_data)
    #print cur_frame
    #cv2.imshow('frame',frame)
    end = time.time()

    seconds = end - start
    if seconds < 1.0/fps:
        time.sleep(1.0/fps - seconds)

    cv2.namedWindow('img',0);
    #cv2.imshow('frame', cur_frame)

    #检测如何按下Q键，则退出程序
    key = cv2.waitKey(30) & 0xff
    if key == 27:
        break

    #转灰度图
    gray_img = cv2.cvtColor(cur_frame, cv2.COLOR_BGR2GRAY)
    #将图片缩放
    #if(gray_img.any() == True):print("get_grey")
    gray_img = cv2.resize(gray_img, (500, 500))
    # 用高斯滤波进行模糊处理
    gray_img = cv2.GaussianBlur(gray_img, (21, 21), 0)

    #如果没有背景图像就将当前帧当作背景图片
    if pre_frame is None:
        pre_frame = gray_img
    else:
        #print("eneter elese")
        # absdiff把两幅图的差的绝对值输出到另一幅图上面来
        img_delta = cv2.absdiff(pre_frame, gray_img)

        #threshold阈值函数(原图像应该是灰度图,对像素值进行分类的阈值,当像素值高于（有时是小于）
        #阈值时应该被赋予的新的像素值,阈值方法)
        thresh = cv2.threshold(img_delta, 25, 255, cv2.THRESH_BINARY)[1]

        #膨胀图像
        thresh = cv2.dilate(thresh, None, iterations=2)

        # findContours检测物体轮廓(寻找轮廓的图像,轮廓的检索模式,轮廓的近似办法)
        contours, hierarchy, _ =   cv2.findContours(thresh.copy(),cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)

        for c in hierarchy:
            #灵敏度
            if cv2.contourArea(c) < 100:
                print(c)
                continue
            else:
                #框选移动部分
                (x,y,w,h) = cv2.boundingRect(c)
                cv2.rectangle(cur_frame,(x,y),(x+w,y+h),(0,255,0),2)

                print("something is moving!!!")
                led = True
                #if led == True:
                    #LED闪烁
                    #for i in range(30):
                     #   GPIO.output(18,GPIO.HIGH)
                      #  time.sleep(0.03)
                       # GPIO.output(18,GPIO.LOW)
                        #time.sleep(0.03)
                        #GPIO.output(18,GPIO.LOW)
                break
        #显示
        cv2.imshow('img', cur_frame)
        pre_frame = gray_img

# release()释放摄像头
camera.release()

#destroyAllWindows()关闭所有图像窗口
cv2.destroyAllWindows()
