from flask import Flask, Response, jsonify
import cv2
import mediapipe as mp
import numpy as np
import time
import winsound

app = Flask(__name__)

# --- GLOBAL VARIABLES ---
current_status = "WAITING"
current_score = 100
posture_quality = "Good"
last_beep_time = 0
BEEP_COOLDOWN = 2.0  # Beep every 2 seconds if bad

# --- CONFIGURATION ---
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

def calculate_angle(a, b):
    a = np.array(a) 
    b = np.array(b) 
    radians = np.arctan2(b[1] - a[1], b[0] - a[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

def gen_frames():
    global current_status, current_score, posture_quality, last_beep_time
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)

    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while True:
            success, frame = cap.read()
            if not success:
                break
            
            # 1. Processing
            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = holistic.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            height, width, _ = image.shape
            color = (0, 255, 255) # Default Yellow
            
            # 2. Logic
            try:
                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    
                    l_shoulder = [landmarks[11].x * width, landmarks[11].y * height]
                    r_shoulder = [landmarks[12].x * width, landmarks[12].y * height]
                    l_ear = [landmarks[7].x * width, landmarks[7].y * height]

                    # Metrics
                    vertical_angle = calculate_angle(l_shoulder, l_ear)
                    shoulder_width = abs(l_shoulder[0] - r_shoulder[0])
                    shoulder_tilt = abs(l_shoulder[1] - r_shoulder[1])
                    
                    # Strict Limits
                    LIMIT_ANGLE_LOW = 75
                    LIMIT_ANGLE_HIGH = 135
                    LIMIT_LEAN = 0.08 * shoulder_width

                    is_bad = False
                    reasons = []

                    if vertical_angle < LIMIT_ANGLE_LOW: 
                        reasons.append("LOOKING UP")
                        is_bad = True
                    if vertical_angle > LIMIT_ANGLE_HIGH: 
                        reasons.append("SLOUCHING")
                        is_bad = True
                    if shoulder_tilt > LIMIT_LEAN: 
                        reasons.append("LEANING")
                        is_bad = True

                    # --- SCORING & AUDIO ---
                    if is_bad:
                        current_status = "WARNING: " + ", ".join(reasons)
                        current_score = max(0, current_score - 2)
                        posture_quality = "Poor"
                        color = (0, 0, 255) # RED
                        
                        # BEEP!
                        current_time = time.time()
                        if current_time - last_beep_time > BEEP_COOLDOWN:
                            winsound.Beep(1000, 200) 
                            last_beep_time = current_time
                            
                    else:
                        current_status = "PERFECT FORM"
                        current_score = min(100, current_score + 1)
                        posture_quality = "Good"
                        color = (0, 255, 0) # GREEN

                    # --- VISUALS ---
                    
                    # 1. Red/Green Skeleton
                    mp_drawing.draw_landmarks(
                        image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2)
                    )

                    # 2. Overlay
                    overlay = image.copy()
                    cv2.rectangle(overlay, (0, 0), (width, 90), (0, 0, 0), -1)
                    image = cv2.addWeighted(overlay, 0.7, image, 0.3, 0)
                    
                    # Text
                    cv2.putText(image, current_status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
                    cv2.putText(image, f"Angle: {int(vertical_angle)} | Lean: {int(shoulder_tilt)}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

                    # 3. Health Bar
                    cv2.rectangle(image, (50, height - 40), (width - 50, height - 20), (50, 50, 50), -1)
                    bar_fill_width = int((current_score / 100) * (width - 100))
                    cv2.rectangle(image, (50, height - 40), (50 + bar_fill_width, height - 20), color, -1)
                    cv2.putText(image, f"SPINE HP: {int(current_score)}%", (50, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            except:
                pass

            ret, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/stats')
def stats():
    return jsonify({
        'score': int(current_score),
        'quality': posture_quality,
        'status': current_status
    })

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>PostureGuard AI Enterprise</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { background-color: #0b0c10; color: #c5c6c7; font-family: 'Roboto', sans-serif; overflow-x: hidden; }
            .sidebar { height: 100vh; background: #1f2833; border-right: 1px solid #45a29e; padding: 20px; }
            .brand { color: #66fcf1; font-weight: bold; letter-spacing: 2px; margin-bottom: 40px; }
            .video-box { width: 100%; border: 3px solid #45a29e; border-radius: 8px; overflow: hidden; box-shadow: 0 0 20px rgba(69, 162, 158, 0.2); }
            .video-box img { width: 100%; display: block; }
            .stat-box { background: #1f2833; padding: 20px; border-radius: 8px; border-left: 4px solid #66fcf1; margin-bottom: 20px; }
            .score-val { font-size: 3rem; font-weight: bold; color: #fff; }
            .live-dot { height: 12px; width: 12px; background-color: #f00; border-radius: 50%; display: inline-block; animation: blink 1s infinite; }
            @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-3 sidebar">
                    <h2 class="brand">POSTURE<span style="color:#fff">GUARD</span></h2>
                    
                    <div class="stat-box">
                        <small>SPINE HEALTH SCORE</small>
                        <div id="scoreDisplay" class="score-val">100%</div>
                    </div>

                    <div class="stat-box" style="border-left-color: #f00;">
                        <small>CURRENT STATUS</small>
                        <div id="statusText" class="fw-bold text-white mt-1">CALIBRATING...</div>
                    </div>

                    <div class="mt-4">
                        <small class="text-muted">REAL-TIME ANALYTICS</small>
                        <canvas id="postureChart" height="150"></canvas>
                    </div>
                    
                    <div class="mt-5 alert alert-dark border-secondary">
                        <small><strong>AUDIO ACTIVE:</strong><br>System will beep when posture is poor.</small>
                    </div>
                </div>

                <div class="col-md-9 p-5">
                    <div class="d-flex justify-content-between mb-3">
                        <h4><span class="live-dot"></span> LIVE FEED</h4>
                        <div class="text-muted">AI Model: MediaPipe Holistic v0.10</div>
                    </div>

                    <div class="video-box">
                        <img src="/video_feed">
                    </div>
                </div>
            </div>
        </div>

        <script>
            const ctx = document.getElementById('postureChart').getContext('2d');
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: Array(20).fill(''),
                    datasets: [{
                        label: 'Posture Stability',
                        data: Array(20).fill(100),
                        borderColor: '#66fcf1',
                        tension: 0.4,
                        pointRadius: 0
                    }]
                },
                options: {
                    animation: false,
                    scales: { y: { min: 0, max: 100, display: false }, x: { display: false } },
                    plugins: { legend: { display: false } }
                }
            });

            setInterval(() => {
                fetch('/stats')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('scoreDisplay').innerText = data.score + "%";
                        document.getElementById('statusText').innerText = data.status;
                        
                        let color = data.score > 80 ? '#66fcf1' : '#f00';
                        document.getElementById('scoreDisplay').style.color = color;

                        chart.data.datasets[0].data.push(data.score);
                        chart.data.datasets[0].data.shift();
                        chart.update();
                    });
            }, 500);
        </script>
    </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)