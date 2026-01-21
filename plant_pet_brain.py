import cv2
import serial
import time
import pyttsx3

# -------- SERIAL --------
PORT = "COM7"  
BAUD = 115200
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

# -------- VOICE --------
engine = pyttsx3.init()
engine.setProperty('rate', 165)

def speak(text):
    print("PLANT:", text)
    engine.say(text)
    engine.runAndWait()

# -------- CAMERA --------
cap = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# -------- MOOD SYSTEM --------
last_seen_time = time.time()
mood = "NEUTRAL"

LONELY_TIME = 25   # seconds without human

print("🌱 Plant Pet Brain Online")

while True:

    # -------- READ SERIAL --------
    if ser.in_waiting:
        line = ser.readline().decode(errors="ignore").strip()
        if line.startswith("TEMP"):
            print("SENSORS:", line)

    # -------- CAMERA FRAME --------
    ret, frame = cap.read()
    if not ret:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    human_present = len(faces) > 0

    # draw face boxes
    for (x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)

    # -------- LONELINESS LOGIC --------
    if human_present:
        last_seen_time = time.time()
        if mood != "HAPPY":
            mood = "HAPPY"
            speak("Oh hi! I missed you!")
    else:
        lonely_for = time.time() - last_seen_time
        if lonely_for > LONELY_TIME and mood != "LONELY":
            mood = "LONELY"
            speak("You look lonely. I can fix that.")

    # -------- DISPLAY --------
    cv2.putText(frame, f"Mood: {mood}", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    cv2.imshow("Plant Pet Cam", frame)

    if cv2.waitKey(1) & 0xFF == 27:   # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()
