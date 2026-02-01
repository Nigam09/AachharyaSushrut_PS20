# PostureGuard AI 🛡️
> *An AI-powered real-time ergonomic assistant built for the modern workspace.*

## 💡 The Problem
Remote work and long desk hours have led to a "Posture Pandemic." Poor spinal health reduces productivity and causes long-term injury. Wearable solutions are expensive and intrusive.

## 🚀 The Solution
**PostureGuard AI** is a computer-vision based SaaS prototype that turns any webcam into a private ergonomic coach.
* **Zero Wearables:** Uses standard laptop cameras.
* **Real-Time Feedback:** Detects Slouching, Leaning, and Neck Strain instantly.
* **Gamified Health:** Tracks "Spine HP" in real-time to encourage better habits.

## 🛠️ Tech Stack
* **Python 3.10** (Core Logic)
* **MediaPipe Holistic** (SOTA Pose Estimation)
* **OpenCV** (Image Processing)
* **Flask** (Web Framework)
* **Chart.js & Bootstrap** (Frontend Dashboard)

## ⚙️ How to Run
1.  **Clone the repository**
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the App:**
    ```bash
    python web_app.py
    run: .\hack_env\Scripts\python web_app.py
    ```
4.  **Open Dashboard:**
    Visit `http://localhost:5000` in your browser.

## 🎯 Features
* [x] **Strict Mode Detection:** Catches micro-slouches and neck tilts.
* [x] **Visual Alerts:** Skeleton turns RED on bad posture.
* [x] **Audio Feedback:** Gentle beep alerts for immediate correction.
* [x] **Live Analytics:** Real-time graph of posture stability.

---
*Built for the Hackathon 2026.*
