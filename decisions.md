22 Sep 2026
: Choosing between MediaPipe and TasksAPI.

Stage 1: Proving MediaPipe can reliably perceive gestures from a live webcam feed
: Went with TasksAPI because it is much newer and can classify named gestures without having to interpret myself. Concepts transfer directly between both.

: Keeping numofHands at 1 for now for the first few stages. Will be changed to 2 when 2 hands start being tracked for inputs.

: Chose LIVE_STREAM mode over IMAGE AND VIDEO because it is specifically used for when a camera is running at the same time as the program

: Stored the latest result in a global variable (latestResult) for simplicity in accessing its data

: Keeping OpenCV preview window open(cv2.imshow) while stage goal only requires console input. Makes it easier to see if its actually tracking hand and understand if any debugging is needed

: Printing every frames result instead of only on changes
: Goal is to see whether the model struggles when dealing with a lot of nouse.
: Smoothing will happen later

7 Oct 2026
: API Gesture recognizer is working well on live-webcam

: Async call back is working as intended.

: tested all current gestures that can be recognized and they are all above .60 in confidence

: Fixed syntax and indentation errors. Also fixed Nonetype crash.

: Added support for two hands early so each hand can be responsible for a different action when doing same gesture.

: 
