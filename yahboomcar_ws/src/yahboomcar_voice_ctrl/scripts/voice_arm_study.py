import time
import sys
import threading
from time import sleep
from Speech_Lib import Speech
from Rosmaster_Lib import Rosmaster
spe = Speech()
class amr_study:
    def __init__(self):
        self.car = Rosmaster()
        self.car.set_car_type(2)
        self.car.create_receive_threading()
        self.car.set_car_motion(0, 0, 0)
        self.joints = [90, 145, 0, 0, 90, 30]
        self.car.set_uart_servo_angle_array(self.joints, 1000)
        self.study_joints =[]

    def ready_to_study(self):
        self.car.set_beep(1)
        sleep(1)
        self.car.set_beep(0)
        self.car.set_colorful_effect(2, 6, parm=1)


if __name__ == '__main__':
    driver = amr_study()
    sleep(2)
    driver.ready_to_study()
    spe.void_write(29)
    study_flag = True
    study_cnt = 0
    current_joints =[]
    error_joint = False
    try:
         while True:
             if study_flag == True:
                 driver.car.set_uart_servo_torque(0)
                 speech_r = spe.speech_read()					
                 if speech_r == 55:
                     study_cnt = study_cnt + 1
                     if study_cnt >20 :
                         spe.void_write(56)
                         study_flag = False
                     else:		
                         current_joints = driver.car.get_uart_servo_angle_array()
                         for i in range(1,6):
                             if current_joints[i]<0:
                                driver.car.set_beep(1)
                                sleep(1)
                                driver.car.set_beep(0)
                                print(i)
                                print(current_joints[i])
                                error_joint = True
                         if   error_joint == False:
                            driver.study_joints.append(current_joints)
                            spe.void_write(55)
                         error_joint = False
                         print(driver.study_joints)
                 if speech_r == 56:
                         spe.void_write(57)
                         study_flag = False
             else :
                 driver.car.set_uart_servo_torque(1)
                 speech_r = spe.speech_read()
                 if speech_r == 57:
                     spe.void_write(58)
                     for i in range(len(driver.study_joints)):
                         driver.car.set_uart_servo_angle_array(driver.study_joints[i], 1000)
                         sleep(1)
                 if speech_r == 58:
                     spe.void_write(59)
                     driver.study_joints.clear()
                     print(driver.study_joints)
                     driver.car.set_beep(1)
                     sleep(1)
                     driver.car.set_beep(0)
                     driver.car.set_uart_servo_angle_array(driver.joints, 1000)
                     sleep(3)
                     print(driver.car.get_uart_servo_angle_array())
                     driver.car.set_beep(1)
                     sleep(1)
                     driver.car.set_beep(0)
                     sleep(1)
                     spe.void_write(29)	
                     study_flag = True
                     study_cnt = 0
                         	
    except KeyboardInterrupt:
        print("Close!")
