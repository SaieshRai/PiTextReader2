import RPi.GPIO as GPIO
import os, sys
import logging
import subprocess
import threading
import time
import cv2
import pytesseract

##### USER VARIABLES
DEBUG   = 0  # Debug 0/1 off/on (writes to debug.log)
SPEED   = 1.0  # Speech speed, 0.5 - 2.0
VOLUME  = 90  # Audio volume

# OTHER SETTINGS
SOUNDS  = "/home/pi/PiTextReader/sounds/"  # Directory for sound effect(s)

# GPIO BUTTONS
BTN1    = 24  # The button!
LED     = 18  # The button's LED!

### FUNCTIONS
# Thread controls for background processing
class RaspberryThread(threading.Thread):
    def __init__(self, function):
        self.running = False
        self.function = function
        super(RaspberryThread, self).__init__()

    def start(self):
        self.running = True
        super(RaspberryThread, self).start()

    def run(self):
        while self.running:
            self.function()

    def stop(self):
        self.running = False

# LED ON/OFF
def led(val):  
    logger.info('led('+str(val)+')')
    if val:
        GPIO.output(LED,GPIO.HIGH)
    else:
        GPIO.output(LED,GPIO.LOW)
   
# PLAY SOUND
def sound(val):  # Play a sound
    logger.info('sound()')
    time.sleep(0.2)
    cmd = "/usr/bin/aplay -q "+str(val)
    logger.info(cmd)
    os.system(cmd)
    return
 
# SPEAK STATUS
def speak(val):  # TTS Speak
    logger.info('speak()')
    cmd = "/usr/bin/flite -voice awb --setf duration_stretch="+str(SPEED)+" -t \""+str(val)+"\""
    logger.info(cmd)
    os.system(cmd)
    return

# SET VOLUME
def volume(val):  # Set Volume for Launch
    logger.info('volume('+str(val)+')')
    vol = int(val)
    cmd = "sudo amixer -q sset PCM,0 "+str(vol)+"%"
    logger.info(cmd)
    os.system(cmd)
    return

# TEXT CLEANUP
def cleanText():
    logger.info('cleanText()')
    cmd = "sed -e 's/\([0-9]\)/& /g' -e 's/[[:punct:]]/ /g' -e 'G' -i /tmp/text.txt"
    logger.info(cmd)
    os.system(cmd)
    return
   
# Play TTS (Allow Interrupt)
def playTTS():
    logger.info('playTTS()')
    global current_tts
    current_tts=subprocess.Popen(['/usr/bin/flite','-voice','awb','-f', '/tmp/text.txt'],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,close_fds=True)
    rt.start()  # Kick off stop audio thread
    current_tts.communicate()  # Wait until finished speaking (unless interrupted)
    return

# Stop TTS (with Interrupt)
def stopTTS():
    global current_tts
    if GPIO.input(BTN1) == GPIO.LOW:
        logger.info('stopTTS()')
        current_tts.kill()  # Stop audio if button pressed
        time.sleep(0.5)
    return

# Capture Image with OpenCV and process it
def capture_image():
    logger.info('capture_image()')
    # OpenCV capture from camera (0 for default camera)
    cap = cv2.VideoCapture(0)
    
    # Check if camera opened successfully
    if not cap.isOpened():
        logger.error("Error: Could not open camera.")
        return
    
    # Capture a single frame
    ret, frame = cap.read()
    
    # Release the camera
    cap.release()
    
    if ret:
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Save the processed image temporarily
        cv2.imwrite('/tmp/image.jpg', thresh)
        return '/tmp/image.jpg'
    else:
        logger.error("Error: Could not capture image.")
        return None

# Perform OCR on captured image
def getData():
    image_path = capture_image()  # Capture image and get its path
    if image_path:
        logger.info('Performing OCR on image...')
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(image_path)
        
        # Save extracted text to a file
        with open('/tmp/text.txt', 'w') as f:
            f.write(text)
        
        logger.info(f"Extracted Text: {text}")
        
        # Clean up the text file for better speech output
        cleanText()
        playTTS()  # Play the text as speech
    else:
        speak("Error capturing image")

######
# MAIN
######
try:
    global rt
    # Setup Logging
    logger = logging.getLogger()
    handler = logging.FileHandler('debug.log')
    if DEBUG:
        logger.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)
        handler.setLevel(logging.ERROR)
    log_format = '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(handler)
    logger.info('Starting')
   
    # Setup GPIO buttons
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
     
    GPIO.setup(BTN1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED, GPIO.OUT)
   
    # Threaded audio player
    rt = RaspberryThread(function=stopTTS)  # Stop Speaking text
   
    volume(VOLUME)
    speak("OK, ready")
    led(1)
   
    while True:
        if GPIO.input(BTN1) == GPIO.LOW:
            # Btn 1 Pressed
            getData()
            rt.stop()
            rt = RaspberryThread(function=stopTTS)  # Stop Speaking text
            led(1)
            time.sleep(0.5)
            speak("OK, ready")
        time.sleep(0.2)
   
except KeyboardInterrupt:
    logger.info("exiting")

GPIO.cleanup()  # Reset GPIOs
sys.exit(0)
