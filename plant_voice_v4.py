import cv2
import mediapipe as mp
import serial
import time
import pygame

# ================= AUDIO =================
pygame.mixer.init()

def play(sound):
    try:
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(sound)
            pygame.mixer.music.play()
    except Exception as e:
        print("AUDIO ERROR:", e)

# ================= SERIAL =================
PORT = "COM7"
BAUD = 115200
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

# ================= MEDIAPIPE =================
BaseOptions = mp.tasks.BaseOptions
FaceDetector = mp.tasks.vision.FaceDetector
FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceDetectorOptions(
    base_options=BaseOptions(model_asset_path="blaze_face_short_range.tflite"),
    running_mode=VisionRunningMode.VIDEO,
)

detector = FaceDetector.create_from_options(options)

# ================= CAMERA =================
cap = cv2.VideoCapture(0)

# ================= STATE =================
mood = "NEUTRAL"
prev_human = True

override_mood = None
override_until = 0

last_human_time = time.time()
last_active_time = time.time()

touch_played = False

focus_start_time = None
focus_voice_played = False

lonely_voice_count = 0
last_lonely_voice = 0
lonely_active = False

last_loud_voice = 0

startup_time = time.time()

# ---- ABSENCE FILTERING ----
absence_start_time = None
ABSENCE_CONFIRM_TIME = 2.0     # 👈 fast for demo
human_confirmed_absent = False

# ================= SENSOR =================
tL = 0
tR = 0
sound = 0

# ================= THRESHOLDS (DEMO SPEED) =================
LOUD_SOUND = 900

LONELY_TIME = 6               # seconds before scooby voice
FOCUS_TIME = 4                # seconds before focus triggers
HEAD_DOWN_Y = 0.32

HAPPY_DURATION = 4            # happy eyes duration
FOCUS_VOICE_DELAY = 3         # seconds after angry before voice



print("🌱 EVE Voice Brain Online")

# ================= INTRO =================
ser.write(b"INTRO\n")
play("hello.wav")
time.sleep(2)

ser.write(b"MOOD:NEUTRAL\n")
time.sleep(1)

# ================= MAIN LOOP =================
while True:

    now = time.time()

    # ---------- SERIAL ----------
    if ser.in_waiting:
        line = ser.readline().decode(errors="ignore").strip()
        if line.startswith("TEMP"):
            try:
                parts = line.split(",")

                tL = int(parts[3].split(":")[1])
                tR = int(parts[4].split(":")[1])
                sound = int(parts[5].split(":")[1])

                # ----- TOUCH -----
                if (tL == 1 or tR == 1):
                    last_active_time = now

                    if not touch_played:
                        ser.write(b"EVENT:LAUGH\n")
                        ser.write(b"MOOD:HAPPY\n")

                        override_mood = "HAPPY"
                        override_until = now + HAPPY_DURATION

                        play("care.wav")
                        touch_played = True
                else:
                    touch_played = False

            except:
                pass

    # ---------- CAMERA ----------
    human_present = False
    head_down = False

    ret, frame = cap.read()
    if not ret:
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    timestamp = int(time.time() * 1000)
    result = detector.detect_for_video(mp_image, timestamp)

    if result.detections:
        human_present = True
        last_human_time = now

        h, w, _ = frame.shape

        for det in result.detections:
            box = det.bounding_box
            face_ratio = box.height / h

            # Debug print (optional)
            print("Face ratio:", round(face_ratio, 2))

            if face_ratio >0.35:     # 👈 adjust between 0.28 – 0.38 if needed
                head_down = True

            x1 = box.origin_x
            y1 = box.origin_y
            x2 = x1 + box.width
            y2 = y1 + box.height
            cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)

    # ---------- HUMAN ABSENCE FILTER ----------
    if not human_present:
        if absence_start_time is None:
            absence_start_time = now
        elif now - absence_start_time > ABSENCE_CONFIRM_TIME:
            human_confirmed_absent = True
    else:
        absence_start_time = None
        human_confirmed_absent = False

    # ---------- HUMAN TRANSITIONS ----------
    if now - startup_time > 3:

        # ---- Human Reappeared ----
        if human_present and lonely_active and prev_human is False:

            play("ariana_grande_miss_u.mp3")

            ser.write(b"MOOD:HAPPY\n")
            override_mood = "HAPPY"
            override_until = now + HAPPY_DURATION

            lonely_active = False
            lonely_voice_count = 0
            focus_start_time = None
            focus_voice_played = False

        # ---- Human Confirmed Absent ----
        if human_confirmed_absent and not lonely_active:
            ser.write(b"EVENT:SAD\n")
            ser.write(b"MOOD:TIRED\n")
            lonely_active = True

    prev_human = human_present

    # ---------- OVERRIDE ----------
    if override_mood and now < override_until:
        mood = override_mood

    else:
        override_mood = None

        # ---------- LOUD SOUND ----------
        if sound > LOUD_SOUND and now - last_loud_voice > 6:
            mood = "ANGRY"
            play("system_phar_denge.wav")
            last_loud_voice = now

        # ---------- LONELY ----------
        elif lonely_active:
            mood = "TIRED"

            if (now - last_human_time > LONELY_TIME and
                lonely_voice_count < 3 and
                now - last_lonely_voice > 6):

                play("scooby_doo_where_r_u.wav")
                lonely_voice_count += 1
                last_lonely_voice = now

        # ---------- FOCUS ----------
        elif human_present and head_down and (now - last_active_time > FOCUS_TIME):
            mood = "ANGRY"

            if focus_start_time is None:
                focus_start_time = now

            if not focus_voice_played and now - focus_start_time > FOCUS_VOICE_DELAY:
                play("placement_voice.wav")
                focus_voice_played = True

        else:
            focus_start_time = None
            focus_voice_played = False
            mood = "NEUTRAL"

        ser.write(f"MOOD:{mood}\n".encode())

    # ---------- DISPLAY ----------
    cv2.putText(frame, f"Mood: {mood}", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    status = "Human Present" if human_present else "Human Absent"
    cv2.putText(frame, status, (10,65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.imshow("EVE Vision", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
