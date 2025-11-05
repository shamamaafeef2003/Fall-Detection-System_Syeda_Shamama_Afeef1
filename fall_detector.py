import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime
import json

class FallDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Fall detection parameters
        self.fall_threshold = 0.6  # Ratio threshold for fall detection
        self.fall_frames_threshold = 5  # Consecutive frames to confirm fall
        self.fall_counter = 0
        self.fall_detected = False
        self.fall_events = []
        
    def calculate_body_ratio(self, landmarks, frame_height, frame_width):
        """Calculate body aspect ratio to detect falls"""
        try:
            # Get key landmarks
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
            right_ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value]
            
            # Calculate vertical and horizontal distances
            shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
            hip_mid_y = (left_hip.y + right_hip.y) / 2
            ankle_mid_y = (left_ankle.y + right_ankle.y) / 2
            
            shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
            hip_mid_x = (left_hip.x + right_hip.x) / 2
            
            # Vertical distance (head to ankle)
            vertical_distance = abs(ankle_mid_y - shoulder_mid_y)
            
            # Horizontal spread
            horizontal_spread = abs(
                max(left_shoulder.x, right_shoulder.x, left_hip.x, right_hip.x) -
                min(left_shoulder.x, right_shoulder.x, left_hip.x, right_hip.x)
            )
            
            # Calculate aspect ratio
            if vertical_distance > 0:
                aspect_ratio = horizontal_spread / vertical_distance
            else:
                aspect_ratio = 0
                
            # Check if person is horizontal (fallen)
            body_angle = self.calculate_body_angle(
                shoulder_mid_x, shoulder_mid_y,
                hip_mid_x, hip_mid_y
            )
            
            return aspect_ratio, body_angle, ankle_mid_y
            
        except Exception as e:
            return 0, 0, 0
    
    def calculate_body_angle(self, x1, y1, x2, y2):
        """Calculate angle of body relative to vertical"""
        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        return min(angle, 180 - angle)
    
    def detect_fall(self, frame, frame_count, fps):
        """Main fall detection logic"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        fall_confidence = 0
        status = "Standing"
        
        if results.pose_landmarks:
            # Draw pose landmarks
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS
            )
            
            # Calculate fall indicators
            landmarks = results.pose_landmarks.landmark
            aspect_ratio, body_angle, ankle_y = self.calculate_body_ratio(
                landmarks, frame.shape[0], frame.shape[1]
            )
            
            # Fall detection logic
            # Person is likely fallen if:
            # 1. Aspect ratio is high (body is horizontal)
            # 2. Body angle is close to horizontal (>60 degrees)
            # 3. Ankle position is low (close to ground)
            
            is_horizontal = aspect_ratio > self.fall_threshold
            is_low = ankle_y > 0.7  # Lower part of frame
            angle_horizontal = body_angle > 60
            
            if is_horizontal and (is_low or angle_horizontal):
                self.fall_counter += 1
                fall_confidence = min(100, (self.fall_counter / self.fall_frames_threshold) * 100)
                
                if self.fall_counter >= self.fall_frames_threshold and not self.fall_detected:
                    self.fall_detected = True
                    timestamp = frame_count / fps
                    self.fall_events.append({
                        'timestamp': timestamp,
                        'frame': frame_count,
                        'confidence': fall_confidence,
                        'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    status = "FALL DETECTED!"
                elif self.fall_counter >= self.fall_frames_threshold:
                    status = "FALL DETECTED!"
                else:
                    status = "Potential Fall"
            else:
                # Reset counter if person stands up
                if self.fall_counter > 0:
                    self.fall_counter = max(0, self.fall_counter - 2)
                if self.fall_counter == 0:
                    self.fall_detected = False
                    status = "Standing"
            
            # Add metrics to frame
            cv2.putText(frame, f"Ratio: {aspect_ratio:.2f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Angle: {body_angle:.1f}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Confidence: {fall_confidence:.1f}%", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display status
        color = (0, 0, 255) if status == "FALL DETECTED!" else (0, 255, 0)
        cv2.putText(frame, status, (10, frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        
        return frame, self.fall_detected, fall_confidence
    
    def process_video(self, video_path, output_path=None):
        """Process entire video for fall detection"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return None
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Processing video: {video_path}")
        print(f"Resolution: {width}x{height}, FPS: {fps}, Total frames: {total_frames}")
        
        # Video writer for output
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        alert_sent = False
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            processed_frame, fall_detected, confidence = self.detect_fall(
                frame, frame_count, fps
            )
            
            # Write processed frame
            if output_path:
                out.write(processed_frame)
            
            # Display progress
            if frame_count % 30 == 0:
                print(f"Processed {frame_count}/{total_frames} frames", end='\r')
            
            # Check if alert should be sent
            if fall_detected and not alert_sent:
                print(f"\n⚠️  FALL DETECTED at frame {frame_count} ({frame_count/fps:.2f}s)")
                alert_sent = True
        
        cap.release()
        if output_path:
            out.release()
        
        print(f"\nProcessing complete!")
        print(f"Total falls detected: {len(self.fall_events)}")
        
        return {
            'total_frames': total_frames,
            'fps': fps,
            'fall_events': self.fall_events,
            'total_falls': len(self.fall_events)
        }
    
    def save_results(self, results, output_file='output/detection_results.json'):
        """Save detection results to JSON"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"Results saved to {output_file}")
    
    def __del__(self):
        self.pose.close()