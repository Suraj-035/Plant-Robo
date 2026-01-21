import cv2
import serial
import time

ser = serial.Serial('COM7', 115200, timeout=1)
time.sleep(2)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cap = cv2.VideoCapture(0)

person_timer = 0
state = "0"

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) > 0:
        person_timer = time.time()
        state = "1"
    else:
        if time.time() - person_timer > 2:   # 2 sec delay
            state = "0"

    ser.write((state + "\n").encode())

    label = "PERSON" if state == "1" else "NO PERSON"
    cv2.putText(frame, label, (20,40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("Plant Vision", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
ser.close()
