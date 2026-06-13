#!/usr/bin/env python
# encoding: utf-8
import rospy
import threading
import cv2 as cv
from time import sleep, time
from transport_common import ROSNav
# import sys
# import rospkg
# sys.path.append(rospkg.RosPack().get_path("arm_autopilot") + "scripts")
# from autopilot_common import *

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
        elif H_min >= 23 and H_max <= 56: color_name = 'yellow'
        elif H_min >= 35 and H_max <= 78: color_name = 'green'
        elif H_min >= 100 and H_max <= 124: color_name = 'blue'
        txt_H = 'Hmin : ' + str(H_min) + ' Hmax : ' + str(H_max)
        cv.putText(img, txt_H, (270, 30), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
        return img, color_name

    def process(self, frame, action, text):
        if action == 32 or self.ros_nav.joy_action==2: self.model = "Grip"
        elif action == ord('r') or action == ord('R'): self.Reset()
        elif action == ord('q') or action == ord('Q'): self.ros_nav.cancel()
        if self.model == "Grip":
            if not self.Grip_status:
                frame, self.color_name = self.get_color(frame)
                if len(self.color_name) != 0: threading.Thread(target=self.Grip_Target, ).start()
        elif self.model == "Transport":
            if len(self.ros_nav.color_pose) != 0 and not self.ros_nav.Transport_status:
                if self.color_name in self.ros_nav.color_pose.keys():
                    self.ros_nav.PubTargetPoint(self.ros_nav.color_pose[self.color_name])
                    self.model = "Grip_down"
                    self.ros_nav.Transport_status = True
        elif self.model == "Grip_down":
            if self.ros_nav.goal_result == 3: threading.Thread(target=self.Grip_down,).start()
        elif self.model == "come_back":
            if self.ros_nav.goal_result == 3:
                threading.Thread(target=self.buzzer_loop,).start()
                self.Reset()
        cv.putText(frame, text, (30, 30), cv.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 200), 1)
        cv.putText(frame, color_transport.model, (30, 450), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
        self.ros_nav.pubImg(frame)
        return frame

    def comeback(self):
        self.ros_nav.PubTargetPoint(self.ros_nav.start_point)
        self.model = "come_back"

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
        self.comeback()

    def Grip_Target(self):
        self.model = "Grip_Target"
        # print "开启夹取流程线程"
        self.Grip_status = True
        self.buzzer_loop()
        joints = [90, 145, 0, 45, 90, 30]
        self.ros_nav.pubArm(joints, run_time=1000)
        sleep(0.5)
        self.buzzer_loop()
        self.ros_nav.pubArm([], 6, 146)
        sleep(1)
        self.model = "Transport"

    def buzzer_loop(self):
        self.ros_nav.pubBuzzer(True)
        sleep(1)
        self.ros_nav.pubBuzzer(False)
        sleep(1)


if __name__ == '__main__':
    rospy.init_node('color_transport',anonymous=False)
    color_transport = ColorTransport()
    capture = cv.VideoCapture("/dev/camera_usb")
    cv_edition = cv.__version__
    if cv_edition[0] == '3': capture.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*'XVID'))
    else: capture.set(cv.CAP_PROP_FOURCC, cv.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    capture.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    text = '0'
    while capture.isOpened():
        start = time()
        ret, frame = capture.read()
        action = cv.waitKey(10) & 0xFF
        if action == ord('q') or action == 113: break
        frame = color_transport.process(frame, action, text)
        text = "FPS : " + str(int(1 / (time() - start)))
        if color_transport.ros_nav.img_show: cv.imshow("frame", frame)
    capture.release()
    cv.destroyAllWindows()
