#!/usr/bin/python

import RPi.GPIO as GPIO
import os, sys
import logging
import subprocess
import threading
import time
import cv2
import numpy as np

DEBUG   = 1
SPEED   = 1.0
VOLUME  = 100
SOUNDS  = "/home/pi/PiTextReader/sounds/"
BTN1    = 24
LED     = 18

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

def led(val):   
    logger.info('led('+str(val)+')') 
    if val:
        GPIO.output(LED, GPIO.HIGH)
    else:
        GPIO.output(LED, GPIO.LOW)
    
def sound(val):
    logger.info('sound()') 
    time.sleep(0.2)
    cmd = "/usr/bin/aplay -q "+str(val)
    logger.info(cmd) 
    os.system(cmd)
    return
 
def speak(val):
    logger.info('speak()') 
    cmd = "/usr/bin/flite -voice awb --setf duration_stretch="+str(SPEED)+" -t \""+str(val)+"\""
    logger.info(cmd) 
    os.system(cmd)
    return 

def volume(val):
    logger.info('volume('+str(val)+')') 
    vol = int(val)
    cmd = "sudo amixer -q sset PCM,0 "+str(vol)+"%"
    logger.info(cmd) 
    os.system(cmd)
    return 

def cleanText():
    logger.info('cleanText()')
    cmd = "sed -e 's/\([0-9]\)/& /g' -e 's/[[:punct:]]/ /g' -e 'G' -i /tmp/text.txt"
    logger.info(cmd) 
    os.system(cmd)
    return
    
def playTTS():
    logger.info('playTTS()') 
    global current_tts
    if not os.path.exists('/tmp/text.txt'):
        logger.error("Text file does not exist!")
        speak("Sorry, I could not read the text.")
        return
    with open('/tmp/text.txt', 'r') as f:
        text = f.read().strip()
    if len(text) == 0:
        logger.error("No text found in OCR result!")
        speak("Sorry, no readable text was found.")
        return
    current_tts = subprocess.Popen(['/usr/bin/flite', '-voice', 'awb', '-f', '/tmp/text.txt'],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, close_fds=True)
    rt.start()
    current_tts.communicate()
    return

def stopTTS():
    global current_tts
    if GPIO.input(BTN1) == GPIO.LOW:
        logger.info('stopTTS()') 
        current_tts.kill()
        time.sleep(0.5)
    return 

def correct_orientation(image_path):
    logger.info('correct_orientation()')
    orientation_cmd = f"/usr/bin/tesseract {image_path} stdout --psm 0 -c min_characters_to_try=5"
    logger.info(f"Running orientation command: {orientation_cmd}")
    process = subprocess.Popen(orientation_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        logger.error(f"Error detecting orientation: {stderr.decode('utf-8')}")
        return image_path
    output = stdout.decode('utf-8')
    logger.info(f"Tesseract orientation output: {output}")
    if "Rotate: 90" in output:
        angle = 90
    elif "Rotate: 180" in output:
        angle = 180
    elif "Rotate: 270" in output:
        angle = 270
    else:
        angle = 0
    img = cv2.imread(image_path)
    if angle != 0:
        (h, w) = img.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        rotated_img = cv2.warpAffine(img, M, (w, h))
        corrected_image_path = '/tmp/corrected_image.jpg'
        cv2.imwrite(corrected_image_path, rotated_img)
        logger.info(f"Image rotated by {angle} degrees.")
        return corrected_image_path
    else:
        logger.info("No rotation needed.")
        return image_path

def getData():
    logger.info('getData()') 
    led(0)
    sound(SOUNDS + "camera-shutter.wav")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    ret, frame = cap.read()
    if ret:
        image_path = '/tmp/image.jpg'
        cv2.imwrite(image_path, frame)
    cap.release()
    logger.info("Image captured and saved.")
    corrected_image_path = correct_orientation(image_path)
    speak("Now working. Please wait.")
    cmd = f"/usr/bin/tesseract {corrected_image_path} /tmp/text"
    logger.info(f"Running OCR command: {cmd}")
    os.system(cmd)
    if not os.path.exists("/tmp/text.txt"):
        logger.error("OCR failed, text file not found!")
        speak("Sorry, I could not read the text.")
        return
    cleanText()
    playTTS()
    return

try:
    global rt
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
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BTN1, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
    GPIO.setup(LED, GPIO.OUT) 
    rt = RaspberryThread(function=stopTTS)
    volume(VOLUME)
    speak("OK, ready")
    led(1)
    while True:
        if GPIO.input(BTN1) == GPIO.LOW:
            getData()
            rt.stop()
            rt = RaspberryThread(function=stopTTS)
            led(1)
            time.sleep(0.5)  
            speak("OK, ready")
        time.sleep(0.2)  
    
except KeyboardInterrupt:
    logger.info("Exiting.")

GPIO.cleanup()
sys.exit(0)
