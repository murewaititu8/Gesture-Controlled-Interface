import mediapipe as mp
from mediapipe.tasks.python import vision
import time
# Used to generate timestamps
import cv2
# OpenCV


pathofModel = "gesture_recognizer.task"
# String pointing at model file.
# Gesture_recognizer is the trained thought process thats needed for recognizing gestures.

numofHands = 1
# Amount of hands being tracked at a single time.

latestResult = None
# Stored Nonetype that stores async most recent callback.
# Main loop checks while async processes.

def on_result(result, outputImage, timestamp_ms):
    # Function called when MediaPipe finishes processing a frame sent to it.
    # result is gesture data.
    global latestResult
    # Global finds info in a variable outside the function.
    latestResult = result

baseOptions = mp.tasks.BaseOptions(model_asset_path = pathofModel)
# Loading the model file from pathofModel into baseOptions

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
# Puts together all recognizer's settings

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
