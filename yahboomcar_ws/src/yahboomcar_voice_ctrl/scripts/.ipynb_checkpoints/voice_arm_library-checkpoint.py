#!/usr/bin/env python3
# encoding: utf-8
import base64
import math
import rospy
import cv2 as cv
from time import sleep
from std_msgs.msg import Bool
from yahboomcar_msgs.msg import *
from geometry_msgs.msg import Twist
from Rosmaster_Lib import Rosmaster

class Voice_Arm:
    def __init__(self):
        rospy.on_shutdown(self.cancel)
        self.Joy_active = True
        self.pubPoint = rospy.Publisher("TargetAngle", ArmJoint, queue_size=1)
        self.pubBuzzer = rospy.Publisher("Buzzer", Bool, queue_size=1)
        self.pubCmdVel = rospy.Publisher('cmd_vel', Twist, queue_size=1)
        self.sub_JoyState = rospy.Subscriber('/JoyState', Bool, self.JoyStateCallback)
        self.joints = [90.0, 145.0, 0.0, 0.0, 90.0, 31.0]
        self.run_time = 500
        self.arm_joint = ArmJoint()
        self.arm_joint.id = 6
        self.arm_joint.angle = 180
        self.arm_joint.run_time = 500
    def JoyStateCallback(self, msg):
        if not isinstance(msg, Bool): return
        self.Joy_active = not self.Joy_active
        self.pub_vel(0, 0)

    def pub_vel(self, x, y, z=0):
        twist = Twist()
        twist.linear.x = x
        twist.linear.y = y
        twist.angular.z = z
        self.pubCmdVel.publish(twist)

    def pub_buzzer(self, status):
        self.pubBuzzer.publish(status)

    def RobotBuzzer(self):
        self.pub_buzzer(True)
        sleep(1)
        self.pub_buzzer(False)
        sleep(1)
        self.pub_buzzer(False)
        for i in range(2):
            self.pub_vel(0, 0)
            sleep(0.1)

    def pub_arm(self, joints, id=6, angle=180, runtime=500):
        arm_joint = ArmJoint()
        arm_joint.id = id
        arm_joint.angle = angle
        arm_joint.run_time = runtime
        if len(joints) != 0: arm_joint.joints = joints
        else: arm_joint.joints = []
        self.pubPoint.publish(arm_joint)
        # rospy.loginfo(arm_joint)

    def init_pose(self):
        self.arm_joint.joints =[90.0, 145.0, 0.0, 0.0, 90.0, 31.0]
        self.pubPoint.publish(self.arm_joint)

    def arm_up(self):
        self.arm_joint.joints =[94.0, 93.0, 92.0, 88.0, 93.0, 175.0]
        self.pubPoint.publish(self.arm_joint)

    def arm_down(self):
        self.arm_joint.joints =[90.0, 145.0, 0.0, 0.0, 90.0, 31.0]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)
        self.arm_joint.joints =[92.0, 6.0, 90.0, 88.0, 93.0, 175.0]
        self.pubPoint.publish(self.arm_joint)

    def arm_left(self):
        self.arm_joint.joints =[90.0, 145.0, 0.0, 0.0, 90.0, 31.0]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.8)
        self.arm_joint.joints =[5.0, 145.0, 0.0, 0.0, 91.0, 32.0]
        self.pubPoint.publish(self.arm_joint)

    def arm_right(self):
        self.arm_joint.joints =[90.0, 145.0, 0.0, 0.0, 90.0, 31.0]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.8)
        self.arm_joint.joints =[179.0, 145.0, 0.0, 0.0, 91.0, 32.0]
        self.pubPoint.publish(self.arm_joint)


    def arm_clamping(self):
        self.arm_joint.joints =[89.0, 179.0, 0.0, 0.0, 90.0, 150.0]
        self.pubPoint.publish(self.arm_joint)

    def arm_loosen(self):

        self.arm_joint.joints =[89.0, 179.0, 0.0, 0.0, 90.0, 35.0]
        self.pubPoint.publish(self.arm_joint)

    def arm_dance(self):
        self.arm_joint.joints =[90, 90, 90, 90, 90, 90]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[90, 60, 120, 60, 90, 90]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[90, 45, 135, 45, 90, 90]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[90, 60, 120, 60, 90, 90]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[90, 90, 90, 90, 90, 90]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[90, 100, 80, 80, 90, 90]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[90, 120, 60, 60, 90, 90]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[90, 135, 45, 45, 90, 90]
        self.pubPoint.publish(self.arm_joint)

        self.arm_joint.joints =[90, 90, 90, 90, 90, 90]
        self.pubPoint.publish(self.arm_joint)
        self.arm_joint.joints =[90, 90, 90, 20, 90, 150]

        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)
        self.arm_joint.joints =[90, 90, 90, 90, 90, 90]

        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[90, 90, 90, 20, 90, 150]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[0, 90, 90, 90, 0, 90]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[0, 90, 180, 0, 0, 90]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[]
        self.pubPoint.publish(self.arm_joint)

        self.arm_joint.joints =[90, 90, 90, 90, 90, 90]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[90, 135, 0, 45, 90, 90]
        self.pubPoint.publish(self.arm_joint)
        sleep(0.5)

        self.arm_joint.joints =[90.0, 145.0, 0.0, 0.0, 90.0, 31.0]
        self.pubPoint.publish(self.arm_joint)

    def arm_nod(self):
        for i in range(3):
            self.arm_joint.joints =[82.0, 89.0, 93.0, 93.0, 89.0, 32.0]
            self.pubPoint.publish(self.arm_joint)    
            sleep(0.5)
            self.arm_joint.joints =[82.0, 89.0, 93.0, 33.0, 89.0, 32.0]
            self.pubPoint.publish(self.arm_joint)    
            sleep(0.5)

        self.arm_joint.joints =[90.0, 145.0, 0.0, 0.0, 90.0, 31.0]
        self.pubPoint.publish(self.arm_joint)

    def arm_kneel_down(self):
        for i in range(3):
            self.arm_joint.joints =[90, 11, 179, 0, 90, 33]
            self.pubPoint.publish(self.arm_joint)    
            sleep(1)
            self.arm_joint.joints =[90, 11, 179, 0, 90, 161]
            self.pubPoint.publish(self.arm_joint)    
            sleep(1)

        #arm_joint.joints =[90.0, 145.0, 0.0, 0.0, 90.0, 31.0]
        #self.pubPoint.publish(self.arm_joint)

    def arm_applaud(self):
        for i in range(3):
            self.arm_joint.joints =[90.0, 145.0, 0.0, 71.0, 90.0, 31.0]
            self.pubPoint.publish(self.arm_joint)    
            sleep(0.5)
            self.arm_joint.joints =[91.0, 144.0, 0.0, 71.0, 90.0, 168.0]
            self.pubPoint.publish(self.arm_joint)    
            sleep(0.5)

        self.arm_joint.joints =[90.0, 145.0, 0.0, 0.0, 90.0, 31.0]
        self.pubPoint.publish(self.arm_joint)

    def arm_stack(self):
        for i in range(3):
            
            joint4 = 68 + i*8
            print(joint4)		
            self.arm_joint.joints = [90.0, 144.0, 0.0, 44.0, 90.0, 71.0]
            sleep(2)
            self.pubPoint.publish(self.arm_joint)
            self.arm_joint.joints = [90.0, 144.0, 0.0, 44.0, 91.0, 128.0]
            sleep(1)
            self.pubPoint.publish(self.arm_joint)
            self.arm_joint.joints = [7.0, 144.0, 0.0, 44.0, 90.0, 128.0]
            sleep(1)
            self.pubPoint.publish(self.arm_joint)
            self.arm_joint.joints = [7.0, 0.0, 98.0, joint4, 90.0, 128.0]
            sleep(1)
            self.pubPoint.publish(self.arm_joint)
            self.arm_joint.joints = [7.0, 0.0, 98.0, joint4, 90.0, 71.0]
            sleep(3)
            self.pubPoint.publish(self.arm_joint)
            sleep(1)
            self.arm_joint.joints = [7.0, 38.0, 90.0, 90.0, 90.0, 72.0]
            self.pubPoint.publish(self.arm_joint)
            sleep(1)
            if i ==2:
               self.arm_joint.joints =[90.0, 145.0, 0.0, 0.0, 90.0, 31.0]
               self.pubPoint.publish(self.arm_joint)	

    def arm_pray(self):
        #self.arm_joint.joints = [89, 86, 8, 178, 90, 174]
        self.arm_joint.joints = [90, 120, 0, 0, 90, 30]        
        self.pubPoint.publish(self.arm_joint)

    def arm_scare(self):
        for i in range(3):
            self.arm_joint.joints =[138.0, 94.0, 92.0, 88.0, 92.0, 172.0]
            self.pubPoint.publish(self.arm_joint)    
            sleep(0.5)
            self.arm_joint.joints =[48.0, 94.0, 92.0, 87.0, 92.0, 172.0]
            self.pubPoint.publish(self.arm_joint)    
            sleep(0.5)
        self.arm_joint.joints =[90.0, 145.0, 0.0, 0.0, 90.0, 31.0]
        self.pubPoint.publish(self.arm_joint)

    def cancel(self):
        self.pubCmdVel.publish(Twist())
        self.pubCmdVel.unregister()
        self.pubBuzzer.unregister()
        self.pubPoint.unregister()
