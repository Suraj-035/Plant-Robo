import cv2
import mediapipe as mp

# -------- MediaPipe Tasks Setup --------
BaseOptions = mp.tasks.BaseOptions
FaceDetector = mp.tasks.vision.FaceDetector
FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceDetectorOptions(
    base_options=BaseOptions(
        model_asset_path="blaze_face_short_range.tflite"
    ),
    running_mode=VisionRunningMode.IMAGE,
)

detector = FaceDetector.create_from_options(options)

# -------- OpenCV Camera --------
cap = cv2.VideoCapture(0)
print("MediaPipe Face Detection running...")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    result = detector.detect(mp_image)

    if result.detections:
        for det in result.detections:
            box = det.bounding_box
            x1 = box.origin_x
            y1 = box.origin_y
            x2 = x1 + box.width
            y2 = y1 + box.height
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

    cv2.imshow("MediaPipe Face", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
