#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import random
import threading
import time
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

class LLMBridgeNode:
    def __init__(self):
        rospy.loginfo("Initializing LLM Bridge Node...")

        # State Variables
        self.llm_mode_active = True
        self.last_llm_cmd_time = rospy.Time.now()
        self.watchdog_triggered = False

        # Publishers
        self.cmd_vel_pub = rospy.Publisher('cmd_vel', Twist, queue_size=10)
        self.buzzer_pub = rospy.Publisher('Buzzer', Bool, queue_size=10)

        # Subscribers
        self.manual_sub = rospy.Subscriber('cmd_vel_manual', Twist, self.manual_callback)
        self.llm_sub = rospy.Subscriber('llm_cmd', Twist, self.llm_callback)
        self.mode_sub = rospy.Subscriber('llm_mode', Bool, self.mode_callback)

        # Timer for safety watchdog (runs at 10Hz)
        self.timer = rospy.Timer(rospy.Duration(0.1), self.watchdog_check)

        # Background thread for random robot beep sound effects (chirping)
        self.chirp_thread = threading.Thread(target=self.random_chirp_loop)
        self.chirp_thread.daemon = True
        self.chirp_thread.start()

        rospy.loginfo("LLM Bridge Node successfully initialized in MANUAL mode.")

    def random_chirp_loop(self):
        while not rospy.is_shutdown():
            # Wait random time between 20 and 50 seconds
            sleep_time = random.randint(20, 50)
            # Sleep in small steps to react quickly to rospy shutdown
            for _ in range(sleep_time * 2):
                if rospy.is_shutdown():
                    return
                time.sleep(0.5)

            # Trigger a short beep to feel alive
            if not rospy.is_shutdown():
                rospy.loginfo("Chirping: Sending random robot beep sound.")
                self.trigger_beep(0.08)

    def trigger_beep(self, duration=0.1):
        try:
            self.buzzer_pub.publish(Bool(True))
            time.sleep(duration)
            self.buzzer_pub.publish(Bool(False))
        except Exception as e:
            rospy.logwarn("Failed to publish to Buzzer: %s", str(e))

    def mode_callback(self, msg):
        self.llm_mode_active = msg.data
        mode_str = "LLM" if self.llm_mode_active else "MANUAL"
        rospy.loginfo("Mode changed to: %s", mode_str)

        # Beep twice on mode switch
        self.trigger_beep(0.05)
        time.sleep(0.08)
        self.trigger_beep(0.05)

        # Safety reset: stop the car when switching modes
        self.send_stop()
        if self.llm_mode_active:
            self.last_llm_cmd_time = rospy.Time.now()
            self.watchdog_triggered = False

    def manual_callback(self, msg):
        # Forward manual command only if LLM mode is NOT active
        if not self.llm_mode_active:
            self.cmd_vel_pub.publish(msg)

    def llm_callback(self, msg):
        # Forward LLM command only if LLM mode is active
        if self.llm_mode_active:
            self.last_llm_cmd_time = rospy.Time.now()
            self.watchdog_triggered = False
            self.cmd_vel_pub.publish(msg)

    def watchdog_check(self, event):
        # Watchdog is only active in LLM mode
        if self.llm_mode_active and not self.watchdog_triggered:
            time_since_last_cmd = (rospy.Time.now() - self.last_llm_cmd_time).to_sec()
            if time_since_last_cmd > 5.0:
                rospy.logwarn("LLM command timeout (5s). Triggering watchdog stop!")
                self.send_stop()
                self.watchdog_triggered = True
                # Trigger a long warning beep
                self.trigger_beep(0.5)

    def send_stop(self):
        stop_msg = Twist()
        stop_msg.linear.x = 0.0
        stop_msg.linear.y = 0.0
        stop_msg.linear.z = 0.0
        stop_msg.angular.x = 0.0
        stop_msg.angular.y = 0.0
        stop_msg.angular.z = 0.0
        self.cmd_vel_pub.publish(stop_msg)

if __name__ == '__main__':
    rospy.init_node('llm_bridge_node')
    try:
        node = LLMBridgeNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
