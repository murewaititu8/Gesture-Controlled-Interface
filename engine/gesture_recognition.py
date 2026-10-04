import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions
import time
# Used to generate timestamps
import cv2
# OpenCV
from pathlib import Path

pathofModel = str(Path(__file__).parent / "gesture_recognizer.task")
# __file__ is this script's location, so the model is always found next to it.
# Gesture_recognizer is the trained thought process thats needed for recognizing gestures.

numofHands = 2
# Amount of hands being tracked at a single time.

latestResult = None
# Stored as None because no result has been received.
# It stores async most recent callback later.
# Main loop checks while async processes.

def on_result(result, outputImage, timestamp_ms):
    # Function called when MediaPipe finishes processing a frame sent to it.
    # result is gesture data.
    global latestResult
    # Tells function latestResult is from outside function itself
    latestResult = result

baseOptions = BaseOptions(model_asset_path=pathofModel, delegate=BaseOptions.Delegate.CPU,)
# Loading the model file from pathofModel into baseOptions

options = vision.GestureRecognizerOptions(
    base_options = baseOptions,
    # Which model to use
    running_mode = vision.RunningMode.LIVE_STREAM,
    # Takes live inputs from MediaPipe's vision.
    num_hands = numofHands,
    # How many hands to track
    result_callback = on_result,
    # Which function to call when a result is ready
)
# Puts together all recognizer's settings

recognizer = vision.GestureRecognizer.create_from_options(options)
# Actual recognizer object thats built from all settings from before.

cam = cv2.VideoCapture(0)
# This opens default webcam on device.
# (0) is first camera device that is listed on the device being used.

startTime = time.time()
# Records the start (now) as the reference point for timestamps.

while cam.isOpened():
    # Main loop that continues while the camera is open.
    # isOpened() is a method that comes from VideoCapture object.
    success, frame = cam.read()
    # This grabs a frame from the camera. Success is a bool, depending on whether it was successful.
    # Frame is the actual image, as a numpy array(Good for different calculations and other functions)
    if not success:
        continue
    # If there is an error in the frame arriving the loop is skipped instead of app crashing.
    rgbFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # This reorders colors.
    # OpenCV stores colors in Blue Green Red. MediaPipe expects Red Green Blue

    mpImage = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgbFrame)
    # Wraps the numpy frame in MediaPipe's own image type.

    timestampMs = int((time.time() - startTime) * 1000)
    # Milliseconds since start. LIVE_STREAM requires timestamps that always increase.

    recognizer.recognize_async(mpImage, timestampMs)
    # Sends the frame off. The answer arrives later in on_result.

    result = latestResult
    # Local snapshot. The callback can overwrite latestResult mid-frame, but not this.

    if result is not None and result.gestures:
        h, w, _ = frame.shape
        for i, gestureList in enumerate(result.gestures):
            top = gestureList[0]
            # Best gesture guess for hand number i.
            side = result.handedness[i][0].category_name
            # "Left" or "Right" for hand number i.
            text = f"{side}: {top.category_name} ({top.score:.2f})"
            print(text)
            # Still printing every frame's result to the terminal.

            landmarks = result.hand_landmarks[i]
            for lm in landmarks:
                cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 4, (0, 255, 0), -1)
            # Dots on this hand's 21 landmarks.

            wrist = landmarks[0]
            cv2.putText(frame, text, (int(wrist.x * w), int(wrist.y * h) + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            # Label sits next to each hand's wrist, so you can tell them apart.
    else:
        print("No hand detected")
        cv2.putText(frame, "No hand detected", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Gesture Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    # Press q in the preview window to quit.

cam.release()
cv2.destroyAllWindows()
recognizer.close()
# Cleanup after the loop ends.
