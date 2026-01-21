import cv2
import mediapipe as mp
import serial
import time
import pyttsx3

# ========== SERIAL ==========
PORT = "COM7"   # change if needed
BAUD = 115200
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

# ========== VOICE ==========
engine = pyttsx3.init()
engine.setProperty('rate', 165)

def speak(text):
    print("EVE:", text)
    engine.say(text)
    engine.runAndWait()

# ========== MEDIAPIPE TASKS ==========
BaseOptions = mp.tasks.BaseOptions
FaceDetector = mp.tasks.vision.FaceDetector
FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceDetectorOptions(
    base_options=BaseOptions(model_asset_path="blaze_face_short_range.tflite"),
    running_mode=VisionRunningMode.VIDEO,
)

detector = FaceDetector.create_from_options(options)

# ========== CAMERA ==========
cap = cv2.VideoCapture(0)

# ========== STATES ==========
mood = "NEUTRAL"
prev_human = False

happy_until = 0

last_human_time = time.time()
last_active_time = time.time()
last_voice_time = 0
last_touch_event = 0

startup_time = time.time()

# ========== SENSOR DATA ==========
soil_raw = 1000
tL = 0
tR = 0
sound = 0

# ========== THRESHOLDS ==========
SOIL_DRY_RAW = 2350
SOIL_WET_RAW = 800

LOUD_SOUND = 900
LONELY_TIME = 30
FOCUS_TIME = 90

HEAD_DOWN_Y = 0.65

# ========== HELPERS ==========
def soil_percent(raw):
    pct = (SOIL_DRY_RAW - raw) * 100 / (SOIL_DRY_RAW - SOIL_WET_RAW)
    return max(0, min(100, int(pct)))

print("🌱 EVE Plant Pet Brain Online")

# ========== INTRO ==========
ser.write(b"MOOD:NEUTRAL\n")
time.sleep(1)
speak("Hi. My name is Eve. Nice to meet you.")

# ========== MAIN LOOP ==========
while True:

    now = time.time()

    # ---- SERIAL READ ----
    if ser.in_waiting:
        line = ser.readline().decode(errors="ignore").strip()
        if line.startswith("TEMP"):
            try:
                parts = line.split(",")

                soil_raw = int(parts[2].split(":")[1])
                tL = int(parts[3].split(":")[1])
                tR = int(parts[4].split(":")[1])
                sound = int(parts[5].split(":")[1])

                if (tL == 1 or tR == 1) or sound > LOUD_SOUND:
                    last_active_time = now

                # ---- TOUCH EVENT ----
                if (tL == 1 or tR == 1) and (now - last_touch_event > 1.5):

                    ser.write(b"MOOD:HAPPY\n")
                    ser.write(b"EVENT:LAUGH\n")

                    happy_until = now + 5
                    last_touch_event = now

            except:
                pass

    # ---- CAMERA ----
    ret, frame = cap.read()
    if not ret:
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    timestamp = int(time.time() * 1000)
    result = detector.detect_for_video(mp_image, timestamp)

    human_present = False
    head_down = False

    if result.detections:
        human_present = True
        last_human_time = now

        h, w, _ = frame.shape

        for det in result.detections:
            box = det.bounding_box
            x1 = box.origin_x
            y1 = box.origin_y
            x2 = x1 + box.width
            y2 = y1 + box.height

            y_center = (y1 + y2) / (2 * h)
            if y_center > HEAD_DOWN_Y:
                head_down = True

            cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)

    # ---- HUMAN TRANSITIONS (AFTER STARTUP) ----
    if now - startup_time > 4:

        if human_present and not prev_human:
            ser.write(b"MOOD:HAPPY\n")
            happy_until = now + 5

        if not human_present and prev_human:
            ser.write(b"EVENT:SAD\n")
            ser.write(b"MOOD:TIRED\n")

    prev_human = human_present

    # ---- DECISION ENGINE ----
    new_mood = mood
    human_absent = now - last_human_time

    if sound > LOUD_SOUND:
        new_mood = "ANGRY"

    elif human_present and head_down and (now - last_active_time > FOCUS_TIME):
        new_mood = "ANGRY"
        if now - last_voice_time > 12:
            speak("Padhle bhai, placement nahi hogi!")
            last_voice_time = now

    elif human_absent > LONELY_TIME:
        new_mood = "TIRED"
        if now - last_voice_time > 20:
            speak("I miss you... where did you go?")
            last_voice_time = now

    else:
        new_mood = "NEUTRAL"

    if new_mood != mood:
        ser.write(f"MOOD:{new_mood}\n".encode())
        mood = new_mood

    # ---- HAPPY AUTO RESET ----
    if mood == "HAPPY" and now > happy_until:
        ser.write(b"MOOD:NEUTRAL\n")
        mood = "NEUTRAL"

    # ---- DISPLAY ----
    cv2.putText(frame, f"Mood: {mood}", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    status = "Suraj Present" if human_present else "Suraj is Absent :()"
    cv2.putText(frame, status, (10,65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.imshow("EVE - Plant Pet Vision", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
