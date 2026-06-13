#!/usr/bin/env python3
# coding: utf-8
#import Arm_Lib.
import rospy
import cv2 as cv
import threading
from time import sleep
#from dofbot_config import *
from std_msgs.msg import String
from Speech_Lib import Speech
from garbage_library import GarbageTransport
from yahboomcar_msgs.msg import *
spe = Speech()

num=0
dp = []
msg = {}

recyclable_waste=['Newspaper','Zip_top_can','Book','Old_school_bag']
toxic_waste=['Syringe','Expired_cosmetics','Used_batteries','Expired_tablets']
wet_waste=['Fish_bone','Egg_shell','Apple_core','Watermelon_rind']
dry_waste=['Toilet_paper','Peach_pit','Cigarette_butts','Disposable_chopsticks']

class Spech_Garbage_Identify:
    def __init__(self):
        self.img = None
        self.garbage_index=0
        self.name = None
        self.garbage_result = 999
        self.garbage_transbot = GarbageTransport()
        self.sub_msg = rospy.Subscriber('DetectMsg',String,self.sub_msg_callback)
        print("init done")
    def process(self):
        sleep(0.05)
        name = self.name
        #print(self.name)
        if spe.speech_read() == 94:
            print("kkk")
            if  self.name!=None:
                self.garbage_transbot.model = "Grip"
                #self.garbage_transbot.buzzer_loop()
                #self.garbage_result = self.garbage_type.garbage_result(name)            
                if self.name == 'newspaper':
                    print(self.name)
                    spe.void_write(96)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(1)
                        
                if self.name == 'zip-top_can':
                    print(self.name)
                    spe.void_write(94)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(1)
                        
                if self.name == 'book':
                    print(self.name)
                    spe.void_write(97)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(1)
                        
                if self.name == 'old_school_bag':
                    print(self.name)
                    spe.void_write(95)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(1)
                        
                if self.name == 'syringe':
                    print(self.name)
                    spe.void_write(98)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(2)
                        
                if self.name == 'expired_cosmetics':
                    print(self.name)
                    spe.void_write(100)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(2)
                        
                if self.name == 'used_batterise':
                    print(self.name)
                    spe.void_write(99)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(2)
                        
                if self.name == 'expired_tablets':
                    print(self.name)
                    spe.void_write(101)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(2)
                        
                if self.name == 'fish_bone':
                    print(self.name)
                    spe.void_write(102)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(3)
                        
                if self.name == 'egg_shell':
                    print(self.name)
                    spe.void_write(105)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(3)
                        
                if self.name == 'watermelon_rind':
                    print(self.name)
                    spe.void_write(103)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(3)
                        
                if self.name == 'apple_core':
                    print(self.name)
                    spe.void_write(104)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(3)  
                        
                if self.name == 'toilet_paper':
                    print(self.name)
                    spe.void_write(109)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(4)
                        
                if self.name == 'cigarette_butts':
                    print(self.name)
                    spe.void_write(107)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(4)
                        
                if self.name == 'peach_pit':
                    print(self.name)
                    spe.void_write(108)
                    #self.garbage_transbot.buzzer_loop()
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(4)
                    
                if self.name == 'disposable_chopsticks':
                    print(self.name)
                    spe.void_write(106)
                    while self.garbage_transbot.model !="init_point":
                        self.garbage_transbot.process(4)

            self.name=None
            self.garbage_transbot.Reset()
                    

              
    def sub_msg_callback(self,msg):
        #print("------------------")
        if msg.data:
            #print(msg.data)
            self.name = msg.data
            self.process()
        


if __name__ == '__main__':
    rospy.init_node('garbage_transport',anonymous=False)
    transport_garbage = Spech_Garbage_Identify()
    rospy.spin()

        


