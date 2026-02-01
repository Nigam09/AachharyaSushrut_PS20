import cv2
import mediapipe as mp
import numpy as np
import time
import winsound  # <--- NEW: Windows Sound Library

# --- CONFIGURATION ---
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

GREEN = (0, 255, 0)
RED = (0, 0, 255)
YELLOW = (0, 255, 255)

# Variables to control beeping
last_beep_time = 0
beep_cooldown = 2.0  # Seconds to wait between beeps

def calculate_angle(a, b):
    a = np.array(a) 
    b = np.array(b) 
    radians = np.arctan2(b[1] - a[1], b[0] - a[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

print("--- POSTURE GUARD: AUDIO ENABLED ---")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    cap = cv2.VideoCapture(1)

with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = holistic.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        height, width, _ = image.shape

        try:
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                
                shoulder = [landmarks[11].x * width, landmarks[11].y * height]
                ear = [landmarks[7].x * width, landmarks[7].y * height]
                
                angle = calculate_angle(shoulder, ear)
                
                # LIMITS: 70 to 140 is "Good"
                if angle < 70 or angle > 140:
                    status = "SLOUCH DETECTED!"
                    color = RED
                    
                    # --- BEEP LOGIC ---
                    current_time = time.time()
                    if current_time - last_beep_time > beep_cooldown:
                        # Frequency 1000Hz, Duration 500ms
                        winsound.Beep(1000, 500)
                        last_beep_time = current_time
                    # ------------------
                    
                else:
                    status = "GOOD POSTURE"
                    color = GREEN

                cv2.putText(image, status, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3, cv2.LINE_AA)
                cv2.putText(image, f"Angle: {int(angle)}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, YELLOW, 2, cv2.LINE_AA)

        except:
            pass

        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
        cv2.imshow('PostureGuard Final', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()