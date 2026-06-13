#!/usr/bin/env python
# encoding: utf-8
import sys
import math
import time
import rospy
import random
import threading
import numpy as np
from math import pi
from time import sleep
from yahboomcar_msgs.msg import *
from yahboomcar_msgs.srv import *
from Rosmaster_Lib import Rosmaster
from geometry_msgs.msg import Twist
from dynamic_reconfigure.server import Server
from yahboomcar_bringup.cfg import PIDparamConfig
from std_msgs.msg import String, Float32, Int32, Bool
from sensor_msgs.msg import Imu, MagneticField, JointState


class yahboomcar_driver:
    def __init__(self):
        rospy.on_shutdown(self.cancel)
        # 弧度转角度
        # Radians turn angle
        self.RA2DE = 180 / pi
        self.car = Rosmaster()
        self.car.set_car_type(2)
        self.last_update_time = 1
        self.pos = [0, 0, 0, 0]
        self.imu_link = rospy.get_param("~imu_link", "imu_link")
        self.Prefix = rospy.get_param("~prefix", "")
        self.xlinear_limit = rospy.get_param('~xlinear_speed_limit', 1.0)
        self.ylinear_limit = rospy.get_param('~ylinear_speed_limit', 1.0)
        self.angular_limit = rospy.get_param('~angular_speed_limit', 5.0)
        self.sub_cmd_vel = rospy.Subscriber('cmd_vel', Twist, self.cmd_vel_callback, queue_size=100)
        self.sub_RGBLight = rospy.Subscriber("RGBLight", Int32, self.RGBLightcallback, queue_size=100)
        self.sub_Buzzer = rospy.Subscriber("Buzzer", Bool, self.Buzzercallback, queue_size=100)
        self.sub_Arm = rospy.Subscriber("TargetAngle", ArmJoint, self.Armcallback, queue_size=1000)
        self.ArmPubUpdate = rospy.Publisher("ArmAngleUpdate", ArmJoint, queue_size=1000)
        self.EdiPublisher = rospy.Publisher('edition', Float32, queue_size=100)
        self.volPublisher = rospy.Publisher('voltage', Float32, queue_size=100)
        self.staPublisher = rospy.Publisher('joint_states', JointState, queue_size=100)
        self.velPublisher = rospy.Publisher("/pub_vel", Twist, queue_size=100)
        self.imuPublisher = rospy.Publisher("/pub_imu", Imu, queue_size=100)
        self.magPublisher = rospy.Publisher("/pub_mag", MagneticField, queue_size=100)
        self.srv_armAngle = rospy.Service("CurrentAngle", RobotArmArray, self.srv_Armcallback)
        self.dyn_server = Server(PIDparamConfig, self.dynamic_reconfigure_callback)
        self.car.create_receive_threading()
        self.car.set_car_motion(0, 0, 0)
        #self.joints = [90, 2.0, 60.0, 40.0, 90]
        self.joints = [90, 145, 0, 45, 90, 30]
        self.car.set_uart_servo_angle_array(self.joints, 1000)
        '''sleep(5)
        self.joints = [90, 2.0, 60.0, 40.0, 90]
        self.car.set_uart_servo_angle_array(self.joints, 1000) '''       

    def pub_data(self):
        # 发布小车运动速度、陀螺仪数据、电池电压
        ## Publish the speed of the car, gyroscope data, and battery voltage
        while not rospy.is_shutdown():
            sleep(0.05)
            imu = Imu()
            twist = Twist()
            battery = Float32()
            edition = Float32()
            mag = MagneticField()
            edition.data = self.car.get_version()
            battery.data = self.car.get_battery_voltage()
            ax, ay, az = self.car.get_accelerometer_data()
            gx, gy, gz = self.car.get_gyroscope_data()
            mx, my, mz = self.car.get_magnetometer_data()
            vx, vy, angular = self.car.get_motion_data()
            # 发布陀螺仪的数据
            # Publish gyroscope data
            imu.header.stamp = rospy.Time.now()
            imu.header.frame_id = self.imu_link
            imu.linear_acceleration.x = ax
            imu.linear_acceleration.y = ay
            imu.linear_acceleration.z = az
            imu.angular_velocity.x = gx
            imu.angular_velocity.y = gy
            imu.angular_velocity.z = gz
            mag.header.stamp = rospy.Time.now()
            mag.header.frame_id = self.imu_link
            mag.magnetic_field.x = mx
            mag.magnetic_field.y = my
            mag.magnetic_field.z = mz
            # 将小车当前的线速度和角速度发布出去
            # Publish the current linear vel and angular vel of the car
            twist.linear.x = vx
            twist.linear.y = vy
            twist.angular.z = angular
            self.velPublisher.publish(twist)
            # print("ax: %.5f, ay: %.5f, az: %.5f" % (ax, ay, az))
            # print("gx: %.5f, gy: %.5f, gz: %.5f" % (gx, gy, gz))
            # print("mx: %.5f, my: %.5f, mz: %.5f" % (mx, my, mz))
            # rospy.loginfo("battery: {}".format(battery))
            # rospy.loginfo("vx: {}, vy: {}, angular: {}".format(twist.linear.x, twist.linear.y, twist.angular.z))
            self.imuPublisher.publish(imu)
            self.magPublisher.publish(mag)
            self.volPublisher.publish(battery)
            self.EdiPublisher.publish(edition)
            self.joints_states_update()

    def Armcallback(self, msg):
        if not isinstance(msg, ArmJoint): return
        arm_joint = ArmJoint()
        if len(msg.joints) != 0:
            arm_joint.joints = self.joints
            for i in range(2):
                self.car.set_uart_servo_angle_array(msg.joints, msg.run_time)
                self.joints = list(msg.joints)
                self.ArmPubUpdate.publish(arm_joint)
                sleep(0.01)
        else:
            arm_joint.id = msg.id
            arm_joint.angle = msg.angle
            for i in range(2):
                self.car.set_uart_servo_angle(msg.id, msg.angle, msg.run_time)
                self.joints[msg.id - 1] = msg.angle
                self.ArmPubUpdate.publish(arm_joint)
                sleep(0.01)
        self.joints_states_update()
        # rospy.loginfo("id: {},angle: {},joints: {},run_time: {}".format(msg.id, msg.angle, msg.joints, msg.run_time))
        sleep(0.001)

    def srv_Armcallback(self, request):
        # 服务端，机械臂当前关节角度
        # Server, the current joint angle of the robotic arm
        if not isinstance(request, RobotArmArrayRequest): return
        # print ("request: ",request)
        response = RobotArmArrayResponse()
        joints = self.car.get_uart_servo_angle_array()
        response.angles = joints
        # print ("Arm joints: ", joints)
        return response

    def RGBLightcallback(self, msg):
        # 流水灯控制，服务端回调函数 RGBLight control
        '''
        effect=[0, 6]，0：停止灯效，1：流水灯，2：跑马灯，3：呼吸灯，4：渐变灯，5：星光点点，6：电量显示
        speed=[1, 10]，数值越小速度变化越快。
        '''
        if not isinstance(msg, Int32): return
        # print ("RGBLight: ", msg.data)
        for i in range(3):
            self.car.set_colorful_effect(msg.data, 6, parm=1)
            sleep(0.01)

    def Buzzercallback(self, msg):
        # 蜂鸣器控制  Buzzer control
        if not isinstance(msg, Bool): return
        # print ("Buzzer: ", msg.data)
        if msg.data:
            for i in range(3):
                self.car.set_beep(1)
                sleep(0.01)
        else:
            for i in range(3):
                self.car.set_beep(0)
                sleep(0.01)

    def cmd_vel_callback(self, msg):
        # 小车运动控制，订阅者回调函数
        # Car motion control, subscriber callback function
        if not isinstance(msg, Twist): return
        # 下发线速度和角速度
        # Issue linear vel and angular vel
        vx = msg.linear.x
        vy = msg.linear.y
        angular = msg.angular.z
        # 小车运动控制,vel: ±1, angular: ±5
        # Trolley motion control,vel=[-1, 1], angular=[-5, 5]
        # rospy.loginfo("cmd_velx: {}, cmd_vely: {}, cmd_ang: {}".format(vx, vy, angular))
        self.car.set_car_motion(vx, vy, angular)

    def cancel(self):
        self.car.set_car_motion(0, 0, 0)
        self.velPublisher.unregister()
        self.imuPublisher.unregister()
        self.EdiPublisher.unregister()
        self.volPublisher.unregister()
        self.staPublisher.unregister()
        self.magPublisher.unregister()
        self.sub_cmd_vel.unregister()
        self.sub_RGBLight.unregister()
        self.sub_Buzzer.unregister()
        # Always stop the robot when shutting down the node
        rospy.loginfo("Close the robot...")
        rospy.sleep(1)

    def joints_states_update(self):
        state = JointState()
        state.header.stamp = rospy.Time.now()
        state.header.frame_id = "joint_states"
        if len(self.Prefix) == 0:
            state.name = ["arm_joint1", "arm_joint2", "arm_joint3", "arm_joint4", "arm_joint5", "grip_joint"]
        else:
            state.name = [self.Prefix + "/arm_joint1", self.Prefix + "/arm_joint2",
                          self.Prefix + "/arm_joint3", self.Prefix + "/arm_joint4",
                          self.Prefix + "/arm_joint5", self.Prefix + "/grip_joint"]
        joints = self.joints[:]
        joints[5] = np.interp(joints[5], [30, 180], [0, 90])
        mid = np.array([90, 90, 90, 90, 90, 90])
        array = np.array(np.array(joints) - mid)
        DEG2RAD = np.array([pi / 180])
        position_src = list(np.dot(array.reshape(-1, 1), DEG2RAD))
        state.position = position_src
        self.staPublisher.publish(state)

    def dynamic_reconfigure_callback(self, config, level):
        # self.car.set_pid_param(config['Kp'], config['Ki'], config['Kd'])
        # print("PID: ", config['Kp'], config['Ki'], config['Kd'])
        self.linear_max = config['linear_max']
        self.linear_min = config['linear_min']
        self.angular_max = config['angular_max']
        self.angular_min = config['angular_min']
        if config['SetArmjoint']:
            self.car.set_uart_servo_angle_array(
                [config['joint1'], config['joint2'], config['joint3'],
                 config['joint4'], config['joint5'], config['joint6']], run_time=1000)
        return config

if __name__ == '__main__':
    rospy.init_node("driver_node", anonymous=False)             	
    try:
        driver = yahboomcar_driver()
        sleep(2)
        #driver.joints = [90, 2.0, 60.0, 40.0, 90]
        #driver.car.set_uart_servo_angle_array(driver.joints, 1000)
        
        driver.pub_data()
        rospy.spin()
    except:
        rospy.loginfo("Final!!!")

