# SentinelMind
### Adaptive Behavioral Threat Detection System

SentinelMind is an AI-powered cybersecurity system that detects abnormal user behavior in real time using behavior profiling and anomaly detection.

The system learns normal activity patterns and identifies suspicious actions such as unusual login times, unknown devices, abnormal session durations, and excessive activity to help prevent insider threats and zero-day attacks.

---

## Features

- User behavior tracking
- Real-time anomaly detection
- Risk score generation
- Adaptive behavior profiling
- Security incident logging
- Interactive monitoring dashboard
- Simulated attack detection

---

## Tracked Parameters

- Login Time
- Device / Browser
- Location / IP (Simulated)
- Session Duration
- Actions Count
- Action Type

---

## Tech Stack

### Frontend
- HTML5 / CSS3 / JavaScript

### Backend
- Python - FastAPI

### Machine Learning
- Scikit-learn - Isolation Forest

### Database
- MongoDB / CSV Logging

---

## System Workflow

```text
User Action
     ↓
Behavior Logging
     ↓
Feature Extraction
     ↓
Isolation Forest Model
     ↓
Risk Score Generation
     ↓
Alert / Block / Logout
```

---

## Machine Learning Model

SentinelMind uses the **Isolation Forest Algorithm** for anomaly detection.

The model:
- Learns normal user behavior
- Detects suspicious deviations
- Works without requiring attack datasets

---

## Security Responses

Depending on the risk score, the system can:

- Allow activity
- Trigger alerts
- Flag suspicious users
- Force logout sessions

---

## Example Logged Data

```json
{
  "user_id": "U101",
  "login_time": "14",
  "device": "Chrome",
  "location": "India",
  "actions_count": 8,
  "session_duration": 320
}
```

---

## Future Improvements

- Real IP-based geolocation
- Continuous learning model
- Deep learning-based profiling
- Multi-factor authentication integration
- Cloud deployment and scalability

---

## Project Objective

To build an adaptive cybersecurity solution capable of detecting insider threats and zero-day attacks through intelligent behavior analysis.

---

## License

This project is developed for academic and hackathon purposes.
