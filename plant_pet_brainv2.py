import cv2
import serial
import time
import pyttsx3
import imutils


# ========== SERIAL ==========
PORT = "COM7"   # change
BAUD = 115200
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

from collections import deque
human_history = deque(maxlen=10)


# ========== VOICE ==========
engine = pyttsx3.init()
engine.setProperty('rate', 165)

def speak(text):
    print("PLANT:", text)
    engine.say(text)
    engine.runAndWait()

# ========== CAMERA ==========
cap = cv2.VideoCapture(0)

# Face detector (for sitting close)
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Person detector (for standing / far)
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# ========== STATES ==========
mood = "NEUTRAL"

last_human_time = time.time()
last_active_time = time.time()
last_voice_time = 0
last_lonely_voice = 0

# ========== SENSOR DATA ==========
soil_raw = 1000
tL = 1
tR = 1
sound = 0

# ========== THRESHOLDS ==========
SOIL_DRY_RAW = 2350
SOIL_WET_RAW = 800

LOUD_SOUND = 900

LONELY_TIME = 30
FOCUS_TIME = 120

VOICE_COOLDOWN = 10
LONELY_REPEAT = 30

# ========== HELPERS ==========
def soil_percent(raw):
    pct = (SOIL_DRY_RAW - raw) * 100 / (SOIL_DRY_RAW - SOIL_WET_RAW)
    return max(0, min(100, int(pct)))

print("🌱 Plant Pet Brain v4 Online")

# ========== MAIN LOOP ==========
while True:

    now = time.time()

    # ---------- READ SERIAL ----------
    if ser.in_waiting:
        line = ser.readline().decode(errors="ignore").strip()
        if line.startswith("TEMP"):
            try:
                parts = line.split(",")

                soil_raw = int(parts[2].split(":")[1])
                tL = int(parts[3].split(":")[1])
                tR = int(parts[4].split(":")[1])
                sound = int(parts[5].split(":")[1])

                if (tL == 0) or (tR == 0) or sound > LOUD_SOUND:
                    last_active_time = now

            except Exception as e:
                print("SERIAL ERR:", e)

    soil_pct = soil_percent(soil_raw)

    # ---------- CAMERA ----------
    ret, frame = cap.read()
    if not ret:
        continue

    frame = imutils.resize(frame, width=700)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    rects, _ = hog.detectMultiScale(frame, winStride=(8,8))

    detected = (len(faces) > 0) or (len(rects) > 0)
    human_history.append(1 if detected else 0)

    human_present = sum(human_history) >= 5


    if human_present:
        last_human_time = now
    human_absent_time = now - last_human_time

    for (x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)

    for (x,y,w,h) in rects:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)

    # ---------- DECISION ENGINE ----------
    new_mood = mood
    touched = (tL == 1 or tR == 1)

    if sound > LOUD_SOUND:
        new_mood = "ANGRY"
        last_active_time = now

    elif soil_pct < 35:
        new_mood = "THIRSTY"

    elif touched:
        new_mood = "HAPPY"
        last_active_time = now

    elif human_present and not touched and sound < LOUD_SOUND and (now - last_active_time > FOCUS_TIME):
        new_mood = "FOCUS"

    elif human_absent_time> LONELY_TIME:
        new_mood = "LONELY"

    else:
        new_mood = "NEUTRAL"

    # ---------- VOICE ----------
    if new_mood != mood and (now - last_voice_time > VOICE_COOLDOWN):

        if new_mood == "ANGRY":
            speak("Bhai aaram se chalao!")

        elif new_mood == "THIRSTY":
            speak("Are you cheating on me with another plant? I need water!")

        elif new_mood == "HAPPY":
            speak("Hehe that feels nice!")

        elif new_mood == "FOCUS":
            speak("Padhle bhai, nhi to  placement nahi hogi!")

        mood = new_mood
        last_voice_time = now

    if mood == "LONELY" and (now - last_lonely_voice > LONELY_REPEAT):
        speak("I miss you... where did you go?")
        last_lonely_voice = now

    # ---------- DISPLAY ----------
    cv2.putText(frame, f"Mood: {mood}", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    cv2.putText(frame, f"Soil: {soil_pct}%", (10,65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2)

    status = "Human Detected" if human_present else "No Human"
    cv2.putText(frame, status, (10,100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.imshow("Plant Pet Vision", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
