#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import cv2
import requests
import json
import base64
import time
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge, CvBridgeError
from ultralytics import YOLO

class VisionPipelineNode:
    def __init__(self):
        rospy.loginfo("Initializing Vision Pipeline Node...")

        # ROS Parameters
        self.camera_topic = rospy.get_param('~camera_topic', '/camera/rgb/image_raw')
        self.yolo_model_path = rospy.get_param('~yolo_model_path', 'yolo11n.pt')
        self.ollama_url = rospy.get_param('~ollama_url', 'http://localhost:11434/api/chat')
        self.ollama_model = rospy.get_param('~ollama_model', 'llama3.2-instruct')
        self.interval = rospy.get_param('~interval', 2.0) # seconds
        self.confidence = rospy.get_param('~confidence', 0.45)

        # Initialize YOLO and OpenCV Bridge
        try:
            rospy.loginfo("Loading YOLO Model: %s", self.yolo_model_path)
            self.model = YOLO(self.yolo_model_path)
        except Exception as e:
            rospy.logerr("Failed to load YOLO model: %s. Using default 'yolo11n.pt'", str(e))
            self.model = YOLO('yolo11n.pt')

        self.bridge = CvBridge()
        self.last_process_time = 0.0

        # ROS Publishers and Subscribers
        self.json_pub = rospy.Publisher('llm_raw_json', String, queue_size=10)
        self.image_sub = rospy.Subscriber(self.camera_topic, Image, self.image_callback)

        rospy.loginfo("Vision Pipeline Node initialized. Listening on topic: %s", self.camera_topic)

    def bbox_position(self, x1, x2, frame_width):
        center_x = (x1 + x2) / 2.0
        if center_x < frame_width * 0.33:
            return "izquierda"
        elif center_x < frame_width * 0.66:
            return "centro"
        return "derecha"

    def build_scene_description(self, result, model_names, frame_width):
        detections = []
        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            return detections

        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            name = model_names[cls_id]
            pos = self.bbox_position(x1, x2, frame_width)
            
            # Estimate width/size of bounding box as fraction of screen width
            width_ratio = round((x2 - x1) / frame_width, 2)

            detections.append({
                "objeto": name,
                "confianza": round(conf, 2),
                "posicion": pos,
                "tamaño_pantalla_ratio": width_ratio
            })

        # Sort by confidence descending and limit to top 8 detections
        detections.sort(key=lambda d: d["confianza"], reverse=True)
        return detections[:8]

    def decide_movement(self, detections):
        # Default: path is clear, move forward
        action = "forward"
        linear_speed = 0.25
        angular_speed = 0.0
        reason = "El camino está despejado, avanzando."

        # Look for obstacles (like person, chair, or anything in the center with screen ratio > 0.2)
        center_obstacles = [d for d in detections if d["posicion"] == "centro" and d["tamaño_pantalla_ratio"] > 0.2]
        
        if center_obstacles:
            # Check if there is a person
            people = [d for d in center_obstacles if d["objeto"] == "person"]
            if people:
                action = "stop"
                linear_speed = 0.0
                angular_speed = 0.0
                reason = "Obstáculo detectado: Persona en el centro. Deteniendo robot por seguridad."
            else:
                # Other obstacle in center, try to turn left/right to avoid it
                left_obstacles = [d for d in detections if d["posicion"] == "izquierda"]
                right_obstacles = [d for d in detections if d["posicion"] == "derecha"]
                
                action = "left" if len(right_obstacles) >= len(left_obstacles) else "right"
                linear_speed = 0.0
                angular_speed = 0.5 if action == "left" else -0.5
                reason = "Obstáculo detectado en el centro. Girando a la {} para esquivarlo.".format(
                    "izquierda" if action == "left" else "derecha"
                )

        decision = {
            "accion": action,
            "velocidad_lineal": linear_speed,
            "velocidad_angular": angular_speed,
            "razon": reason
        }
        import json
        return json.dumps(decision, ensure_ascii=False)

    def image_callback(self, msg):
        current_time = time.time()
        # Throttle processing rate
        if current_time - self.last_process_time < self.interval:
            return

        self.last_process_time = current_time

        try:
            # Convert ROS Image to OpenCV Frame
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as e:
            rospy.logerr("CvBridge Error: %s", str(e))
            return

        frame_height, frame_width = frame.shape[:2]

        # Run YOLO Inference
        results = self.model(frame, conf=self.confidence, verbose=False)
        result = results[0]

        # Extract objects and position details
        detections = self.build_scene_description(result, self.model.names, frame_width)
        rospy.loginfo("YOLO Detections: %s", str([d['objeto'] for d in detections]))

        # Determine movement command directly using YOLO detections
        raw_response = self.decide_movement(detections)
        rospy.loginfo("YOLO movement decision: %s", raw_response.strip())
        self.json_pub.publish(raw_response)

if __name__ == '__main__':
    rospy.init_node('vision_pipeline')
    try:
        node = VisionPipelineNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
