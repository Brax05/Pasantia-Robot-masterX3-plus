#!/usr/bin/env python3
# coding: utf-8

import Speech_Lib
import time
import rospy
from geometry_msgs.msg import PointStamped, PoseStamped, PoseWithCovarianceStamped
from geometry_msgs.msg import Twist

spe = Speech_Lib.Speech()
pub_goal = rospy.Publisher('move_base_simple/goal', PoseStamped, queue_size=1)
pub_cmdVel = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
def voice_pub_goal():
    rospy.init_node('voice_pub_goal_publisher', anonymous=True) # ROS节点初始化
    pub_goal = rospy.Publisher('move_base_simple/goal', PoseStamped, queue_size=1)
    rate = rospy.Rate(10)
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = rospy.Time.now()
    # The location of the target point

    # The posture of the target point. z=sin(angle/2) w=cos(angle/2)
    
    
    
    while not rospy.is_shutdown():  
        speech_r = spe.speech_read()

        if speech_r == 19 : 
            print("goal to one")
            spe.void_write(speech_r)
            pose.pose.position.x = 1.3779444694519043
            pose.pose.position.y =  0.4531565010547638
            pose.pose.orientation.z = -0.05267291418135136
            pose.pose.orientation.w = 0.9986118185319278
            pub_goal.publish(pose)

        elif speech_r == 20 :
            print("goal to tow")
            spe.void_write(speech_r)
            pose.pose.position.x = 5.145505428314209
            pose.pose.position.y = 0.05567790940403938
            pose.pose.orientation.z = -0.18282021589262698
            pose.pose.orientation.w = 0.9831463617696875
            pub_goal.publish(pose)
            
        elif speech_r == 21 :
            print("goal to three")
            spe.void_write(speech_r)
            pose.pose.position.x =  1.186618447303772
            pose.pose.position.y = -0.09907293319702148
            pose.pose.orientation.z =  -0.0717449248915873
            pose.pose.orientation.w =  0.9974230124437177
            pub_goal.publish(pose)

        elif speech_r == 32 :
            print("goal to four")
            spe.void_write(speech_r)
            pose.pose.position.x =  0.741197705269
            pose.pose.position.y = -2.30312108994
            pose.pose.orientation.z =  0.406148383793
            pose.pose.orientation.w =  0.913807140671
            pub_goal.publish(pose)

        elif speech_r == 33 :
            print("goal to Origin")
            spe.void_write(speech_r)
            pose.pose.position.x =  2.1265463829040527
            pose.pose.position.y = -0.4949168562889099
            pose.pose.orientation.z =  -0.03126186694637504
            pose.pose.orientation.w =  0.9995112283886696
            pub_goal.publish(pose)
        elif speech_r == 0 :
            pub_cmdVel.publish(Twist())
        rate.sleep()
if __name__ == '__main__':
    try:
        voice_pub_goal()
    except rospy.ROSInterruptException:
        pass
    
            
            
