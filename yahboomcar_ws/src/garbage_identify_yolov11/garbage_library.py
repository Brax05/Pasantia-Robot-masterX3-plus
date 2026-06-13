import threading
from time import sleep, time
from transport_common import ROSNav
class GarbageTransport:
    def __init__(self):
        self.ros_nav = ROSNav()
        self.model = "Grip"
        self.Grip_status = True
        self.color_name = {}
        self.index = 0
        self.joints=[]
        self.point= 0

    def process(self,point):
        self.point = point
        #print(spe.speech_read())
        #sself.model = "Grip"
        #elif action == ord('r') or action == ord('R'): self.Reset()
        if self.model == "Grip" :
            
            #self.buzzer_loop()
            if self.Grip_status is True:
                threading.Thread(target=self.Grip_Target, ).start()
               
        elif self.model == "Transport":
            if self.ros_nav.Transport_status is True:
                if self.point == 1 :
                    self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['red'])
                if self.point == 2 :
                    self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['green'])
                if self.point == 3 :   
                    self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['blue'])
                if self.point == 4 : 
                    self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['yellow'])
                    
                self.model = "Grip_down"
                self.ros_nav.goal_result = 0
                self.buzzer_loop()
                #self.ros_nav.Transport_status = True
        elif self.model == "Grip_down":
            if self.ros_nav.goal_result == 3: threading.Thread(target=self.Grip_down,).start()
        elif self.model == "come_back":
            if self.ros_nav.goal_result == 3:
                self.buzzer_loop()
                sleep(1)
                self.Reset()
                self.model = "init_point"
            
            #self.model = "init_point"
        #self.ros_nav.pubImg(frame)
        

    def comeback(self):
        self.ros_nav.PubTargetPoint(self.ros_nav.start_point)
        #self.model = "come_back"
        self.model = "come_back"
        if self.ros_nav.goal_result == 3:
            self.buzzer_loop()

    def Reset(self):
        self.ros_nav.goal_result = 0
        self.model = "Grip"
        self.Grip_status = True
        self.ros_nav.Transport_status = False
        self.color_name = {}
        self.index = 0

    def Grip_down(self):
        self.model = "Grip_down"
        self.ros_nav.goal_result = 0
        self.joints = [90, 2.0, 60.0, 40.0, 90, 140]
        self.ros_nav.pubArm(self.joints, run_time=1000)
        sleep(1)
        self.ros_nav.pubArm([], 6, 30)
        sleep(0.5)
        self.joints = [90, 145, 0, 45, 90, 30]
        self.ros_nav.pubArm(self.joints, run_time=1000)
        sleep(1)
        self.buzzer_loop()
        self.comeback()


    def Grip_Target(self):
        self.model = "Grip_Target"
        # print "开启夹取流程线程"
        self.Grip_status = True
        self.buzzer_loop()
        self.joints = [90, 145, 0, 45, 90, 30] #145
        self.ros_nav.pubArm(self.joints, run_time=1000)
        sleep(0.5)
        self.ros_nav.pubArm([], 6, 149)
        self.ros_nav.Transport_status = True
        sleep(1)
        self.buzzer_loop()
        self.model = "Transport"
        #self.ros_nav.PubTargetPoint(self.ros_nav.color_pose['red'])

    def buzzer_loop(self):
        self.ros_nav.pubBuzzer(True)
        sleep(1)
        self.ros_nav.pubBuzzer(False)
        sleep(1)

    