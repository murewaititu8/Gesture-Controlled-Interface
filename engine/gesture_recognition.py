import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions
import time
# Used to generate timestamps
import cv2
# OpenCV
from pathlib import Path
from gesture_mapping import load_config, lookup_action
# Turns a recognized gesture into an action name using gesture_config.json
import pyautogui

pathofModel = str(Path(__file__).parent / "gesture_recognizer.task")
# __file__ is this script's location, so the model is always found next to it.
# Gesture_recognizer is the trained thought process thats needed for recognizing gestures.

numofHands = 2
# Amount of hands being tracked at a single time.

config = load_config()
# Reads and validates gesture_config.json

pyautogui.PAUSE = 0
# Removes PyAutoGUI's default delay after every call, which would add lag.

screenW, screenH = pyautogui.size()
boxMargin = 0.2
# Only the middle 60% of the camera frame maps to the screen, so you never have to reach the edges.
smoothing = 0.3
# Each frame the cursor moves 30% of the way toward the target. Lower = smoother but laggier.
prevX, prevY = None, None
# Last cursor position, used for smoothing.

def move_cursor(landmark):
    global prevX, prevY
    x = (landmark.x - boxMargin) / (1 - 2 * boxMargin)
    y = (landmark.y - boxMargin) / (1 - 2 * boxMargin)
    x = 1 - x
    # The preview is not mirrored, so moving your hand right moves it left in the image. This flips x.
    x = min(max(x, 0), 1)
    y = min(max(y, 0), 1)
    targetX = 2 + x * (screenW - 5)
    targetY = 2 + y * (screenH - 5)
    # Kept 2px from the edges so the cursor never lands in a corner and triggers PyAutoGUI's failsafe.
    if prevX is None:
        prevX, prevY = targetX, targetY
    else:
        prevX += (targetX - prevX) * smoothing
        prevY += (targetY - prevY) * smoothing
    pyautogui.moveTo(prevX, prevY)

holdNeeded = 4
# A gesture must be seen this many frames in a row before it fires. Stops one-frame flickers from clicking.
cooldown = 0.6
# Seconds before the same action can fire again.
heldFrames = {}
# Consecutive frames each discrete action has been seen.
hasFired = {}
# Whether each action already fired during the current hold, so one fist = one click.
lastFireTime = {}

def do_action(name):
    # The place where discrete actions turn into real input.
    if name == "click":
        pyautogui.click()
        # Clicks at the current cursor position.

def run_discrete(name):
    # Called every frame a discrete gesture is visible.
    heldFrames[name] = heldFrames.get(name, 0) + 1
    if heldFrames[name] >= holdNeeded and not hasFired.get(name, False):
        if time.time() - lastFireTime.get(name, 0) >= cooldown:
            do_action(name)
            lastFireTime[name] = time.time()
        hasFired[name] = True

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

    seenActions = set()
    # Discrete actions seen this frame. Used to reset the ones that stopped.

    if result is not None and result.gestures:
        h, w, _ = frame.shape
        for i, gestureList in enumerate(result.gestures):
            top = gestureList[0]
            # Best gesture guess for hand number i.
            side = result.handedness[i][0].category_name
            sideKey = side.lower()
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

            action = lookup_action(config, sideKey, top.category_name, top.score)
            # Checks what hand + gesture + config does

            if action:
                print(f" -> {action[0]} ({action[1]})")
                # Prints action name and kind

                if action[0] == "move_cursor":
                    move_cursor(landmarks[8])
                    # Landmark 8 is the index fingertip.
                if action[1] == "discrete":
                    seenActions.add(action[0])
                    run_discrete(action[0])

    else:
        print("No hand detected")
        cv2.putText(frame, "No hand detected", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)



    for name in list(heldFrames):
        if name not in seenActions:
            heldFrames[name] = 0
            hasFired[name] = False
        # Releasing the gesture resets it, so the next fist can click again.

    cv2.imshow("Gesture Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    # Press q in the preview window to quit.

cam.release()
cv2.destroyAllWindows()
recognizer.close()
# Cleanup after the loop ends.
