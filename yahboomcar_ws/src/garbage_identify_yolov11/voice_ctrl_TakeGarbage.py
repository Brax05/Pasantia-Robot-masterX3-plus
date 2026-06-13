#!/usr/bin/env python
# encoding: utf-8
import rospy
import threading
import cv2 as cv
from time import sleep, time
from transport_common import ROSNav
from Speech_Lib import Speech
# import sys
# import rospkg
# sys.path.append(rospkg.RosPack().get_path("arm_autopilot") + "scripts")
# from autopilot_common import *
spe = Speech()
class ColorTransport:
    def __init__(self):
        self.ros_nav = ROSNav()
        self.model = "Init"
        self.Grip_status = False
        self.color_name = {}
        self.index = 0
             
        
    def get_color(self, img):
        H = []
        color_name = ""
        # 将彩色图转成HSV
        HSV = cv.cvtColor(img, cv.COLOR_BGR2HSV)
        # 画矩形框
        cv.rectangle(img, (280, 180), (360, 260), (0, 255, 0), 2)
        # 依次取出每行每列的H,S,V值放入容器中
        for i in range(280, 360):
            for j in range(180, 260): H.append(HSV[j, i][0])
        # 分别计算出H,S,V的最大最小
        H_min = min(H); H_max = max(H)
        # print(H_min,H_max)
        # 判断颜色
        if H_min >= 0 and H_max <= 10 or H_min >= 156 and H_max <= 180: color_name = 'red'
        elif H_min >= 26 and H_max <= 34: color_name = 'yellow'
        elif H_min >= 35 and H_max <= 78: color_name = 'green'
        elif H_min >= 100 and H_max <= 124: color_name = 'blue'
        txt_H = 'Hmin : ' + str(H_min) + ' Hmax : ' + str(H_max)
        cv.putText(img, txt_H, (270, 30), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
        return img, color_name

    def process(self):
        sleep(0.05)
        spe_r = spe.speech_read()
        if spe_r  != 999:
            if   spe_r == 19: self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['red'])
            if   spe_r == 20: self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['yellow'])
            if   spe_r == 21: self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['green'])
            if   spe_r == 32: self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['blue'])
            spe.void_write(spe_r)
            self.model = "Grip_Target" 


        elif self.model == "Grip_Target":
            if self.ros_nav.goal_result == 3: 
                #self.buzzer_loop()
                threading.Thread(target=self.Grip_Target, ).start()
                

        elif self.model == "come_back":self.comeback()

        elif self.model == "Grip_down":
            if self.ros_nav.goal_result == 3:
                threading.Thread(target=self.Grip_down,).start()
        
            '''speech_r = spe.speech_read()
            print(speech_r)
            if speech_r == 19:
                print(speech_r)
                spe.void_write(speech_r)
                #self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['red'])
                self.model = "Grip_Target"              

            elif self.model == "Grip_Target":
                if self.ros_nav.goal_result == 3: 
                #self.buzzer_loop()
                    threading.Thread(target=self.Grip_Target, ).start()
                    #self.spe.void_write(34)
                

            elif self.model == "come_back":self.comeback()

            elif self.model == "Grip_down":
                if self.ros_nav.goal_result == 3:
                    threading.Thread(target=self.Grip_down,).start()'''

    def comeback(self):
        self.ros_nav.PubTargetPoint(self.ros_nav.start_point)
        self.model = "Grip_down"

    def Reset(self):
        self.ros_nav.goal_result = 0
        self.model = "Init"
        self.Grip_status = False
        self.ros_nav.Transport_status = False
        self.color_name = {}
        self.index = 0

    def Grip_down(self):
        self.model = "Grip_down"
        self.ros_nav.goal_result = 0
        joints = [90, 2.0, 60.0, 40.0, 90, 140]
        self.ros_nav.pubArm(joints, run_time=1000)
        sleep(1)
        self.ros_nav.pubArm([], 6, 30)
        sleep(0.5)
        joints = [90, 145, 0, 45, 90, 30]
        self.ros_nav.pubArm(joints, run_time=1000)
        sleep(1)
        spe.void_write(81)

    def Grip_Target(self):
        self.model = "Grip_Target"
        self.ros_nav.goal_result = 0
        # print "开启夹取流程线程"
        self.Grip_status = True
        self.buzzer_loop()
        joints = [90, 145, 0, 45, 90, 30]
        self.ros_nav.pubArm(joints, run_time=1000)
        sleep(0.5)
        self.buzzer_loop()
        self.ros_nav.pubArm([], 6, 140)
        sleep(1)
        spe.void_write(34)
        sleep(2)
        spe.void_write(33)
        self.model = "come_back"

    def buzzer_loop(self):
        self.ros_nav.pubBuzzer(True)
        sleep(1)
        self.ros_nav.pubBuzzer(False)
        sleep(1)


if __name__ == '__main__':
    rospy.init_node('color_transport',anonymous=False)
    color_transport = ColorTransport()  
    try:
        while not rospy.is_shutdown():
            sleep(0.05)
            color_transport.process()
    except KeyboardInterrupt:
        print("Close!")
