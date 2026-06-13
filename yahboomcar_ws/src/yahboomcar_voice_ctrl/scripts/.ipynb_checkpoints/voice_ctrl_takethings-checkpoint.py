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
        self.clip = False
        self.come_back_flag = False
             
        

    def process(self):
        #sleep(0.05)
        #spe_r = spe.speech_read()
        print(self.model)
        print(self.ros_nav.goal_result)
        if self.model== "Init" and self.ros_nav.goal_result == 0 :
            sleep(0.05)
            spe_r = spe.speech_read()
            if   spe_r == 19: 
                self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['red'])
                spe.void_write(spe_r)
            if   spe_r == 20: 
                self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['green'])
                spe.void_write(spe_r)
            if   spe_r == 21:
                self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['blue'])
                spe.void_write(spe_r)
            if   spe_r == 32: 
                self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['yellow'])
                spe.void_write(spe_r)
            if   spe_r == 33: 
                self.ros_nav.PubTargetPoint(self.ros_nav.start_point)     
                self.model= "Init"
                self.ros_nav.goal_result = 0
                self.come_back_flag = True
                spe.void_write(spe_r)
        
            
        elif self.model== "Init" and self.ros_nav.goal_result == 3 and self.come_back_flag == False:
            self.model = "Grip_Target"
            self.buzzer_loop()
                
        elif self.model== "Init" and self.ros_nav.goal_result == 3 and self.come_back_flag == True:
            self.model= "Init"
            self.buzzer_loop() 
            self.come_back_flag = False
            self.ros_nav.goal_result = 0
            
        elif self.model == "Grip_Target":
            self.Grip_Target()
            
        elif self.model == "next_points":
            self.next_points()

        elif self.model == "Grip_down":
            if self.ros_nav.goal_result == 3:
                self.buzzer_loop()
                threading.Thread(target=self.Grip_down,).start()
        
    def next_points(self):
        sleep(0.05)
        spe_r = spe.speech_read()
        if   spe_r == 19: 
            self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['red'])
            self.model = "Grip_down"
            spe.void_write(spe_r)
        if   spe_r == 20: 
            self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['yellow'])
            self.model = "Grip_down"
            spe.void_write(spe_r)
        if   spe_r == 21: 
            self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['green'])
            self.model = "Grip_down"
            spe.void_write(spe_r)
        if   spe_r == 32: 
            self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['blue'])
            self.model = "Grip_down"
            spe.void_write(spe_r)
        if   spe_r == 33: 
            self.ros_nav.PubTargetPoint(self.ros_nav.start_point)
            self.model = "Grip_down"
            spe.void_write(spe_r)
            
        #self.model = "Grip_down"
        
        
        
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
        self.ros_nav.goal_result = 0
        joints = [90, 2.0, 60.0, 40.0, 90, 140]
        self.ros_nav.pubArm(joints, run_time=1000)
        sleep(1)
        self.ros_nav.pubArm([], 6, 30)
        sleep(0.5)
        joints = [90, 145, 0, 45, 90, 30]
        self.ros_nav.pubArm(joints, run_time=1000)
        sleep(1)
        spe.void_write(65)
        self.model = "Grip_Target"
        self.clip = False

    def Grip_Target(self):
        sleep(0.05)
        spe_r = spe.speech_read()
        #self.model = "Grip_Target"
        #self.Grip_status = True
        print(self.clip)

        if  spe_r == 53:
            self.clip = True
            if self.clip == True:
                self.ros_nav.goal_result = 0
                joints = [90, 145, 0, 45, 90, 30]
                self.ros_nav.pubArm(joints, run_time=1000)
                sleep(0.5)
                self.buzzer_loop()
                self.ros_nav.pubArm([], 6, 146)
                spe.void_write(34)
                sleep(2)
                self.model = "next_points"
        elif   spe_r == 19: 
            
            self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['red'])
            self.ros_nav.goal_result = 0
            self.model = "Grip_Target"
            spe.void_write(spe_r)
        elif   spe_r == 20: 
            
            self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['yellow'])
            self.ros_nav.goal_result = 0
            self.model = "Grip_Target"
            spe.void_write(spe_r)
        elif   spe_r == 21: 
            self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['green'])
            self.ros_nav.goal_result = 0
            self.model = "Grip_Target"
            spe.void_write(spe_r)
        elif   spe_r == 32: 
            
            self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['blue'])
            self.ros_nav.goal_result = 0
            self.model = "Grip_Target"
            spe.void_write(spe_r)
        elif   spe_r == 33: 
            
            self.ros_nav.PubTargetPoint(self.ros_nav.start_point)
            self.ros_nav.goal_result = 0
            self.model = "Grip_Target"
            spe.void_write(spe_r)


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
