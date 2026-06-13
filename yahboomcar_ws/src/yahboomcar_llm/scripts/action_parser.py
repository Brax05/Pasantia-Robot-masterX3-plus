#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import json
import re
from geometry_msgs.msg import Twist
from std_msgs.msg import String

class ActionParserNode:
    def __init__(self):
        rospy.loginfo("Initializing Action Parser Node...")

        # ROS Parameters for speed limits (Safety)
        self.max_linear_speed = rospy.get_param('~max_linear_speed', 0.45) # m/s
        self.max_angular_speed = rospy.get_param('~max_angular_speed', 1.2) # rad/s

        # Publishers & Subscribers
        self.cmd_pub = rospy.Publisher('llm_cmd', Twist, queue_size=10)
        self.raw_sub = rospy.Subscriber('llm_raw_json', String, self.raw_callback)

        rospy.loginfo("Action Parser Node initialized and ready.")

    def clean_json_string(self, raw_str):
        # Extract the content inside the first curly braces { ... } in case the LLM wrapped it in markdown or text
        match = re.search(r'\{.*\}', raw_str, re.DOTALL)
        if match:
            return match.group(0)
        return raw_str

    def raw_callback(self, msg):
        raw_text = msg.data.strip()
        cleaned_text = self.clean_json_string(raw_text)

        twist_msg = Twist()
        success = False
        reason = "Falló el parsing de la respuesta del LLM"

        try:
            # Parse the JSON string
            data = json.loads(cleaned_text)
            
            # Extract velocities
            linear_x = float(data.get("velocidad_lineal", 0.0))
            angular_z = float(data.get("velocidad_angular", 0.0))
            action = data.get("accion", "stop").lower()
            reason = data.get("razon", "Sin razón provista")

            # Apply safety limits
            linear_x = max(min(linear_x, self.max_linear_speed), -self.max_linear_speed)
            angular_z = max(min(angular_z, self.max_angular_speed), -self.max_angular_speed)

            # Map to Twist message
            # X3Plus is a Mecanum car, but standard diff drive Twist values are published.
            # If action is stop, force velocities to 0
            if action == "stop":
                twist_msg.linear.x = 0.0
                twist_msg.angular.z = 0.0
            else:
                twist_msg.linear.x = linear_x
                twist_msg.angular.z = angular_z

            success = True
            rospy.loginfo("Acción: %s | Lineal: %.2f | Angular: %.2f | Razón: %s", 
                          action.upper(), twist_msg.linear.x, twist_msg.angular.z, reason)

        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            rospy.logerr("Error parsing LLM action JSON: %s. Raw input: %s", str(e), raw_text)
            # Safe Fallback: Publish Stop command
            twist_msg.linear.x = 0.0
            twist_msg.angular.z = 0.0

        # Publish the final velocity message
        self.cmd_pub.publish(twist_msg)

if __name__ == '__main__':
    rospy.init_node('action_parser')
    try:
        node = ActionParserNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
