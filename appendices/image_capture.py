import sys
import platform

if platform.system() == "Linux" and ("arm" in platform.machine() or "aarch64" in platform.machine()):
    import cv2
    import numpy as np
    import easyocr
    import RPi.GPIO as GPIO
    import time
    from picamera2 import Picamera2
    from datetime import datetime
    import os
    import json
    from database.db_manager import DatabaseManager
    from notification.email_sender import EmailSender

    class SpeedMonitor:
        def __init__(self):
            # Initialize GPIO
            GPIO.setmode(GPIO.BCM)
            self.speed_pin = 17  # GPIO pin for speed data
            GPIO.setup(self.speed_pin, GPIO.IN)
            
            # Initialize camera
            self.picam2 = Picamera2()
            self.picam2.configure(self.picam2.create_preview_configuration(
                main={"format": 'XRGB8888', "size": (640, 480)}))
            self.picam2.start()
            
            # Initialize OCR
            self.reader = easyocr.Reader(['en'])
            
            # Initialize database and email sender
            self.db = DatabaseManager()
            self.email_sender = EmailSender()
            
            # Create directory for captured images
            self.image_dir = "captured_images"
            os.makedirs(self.image_dir, exist_ok=True)
            
            # Speed threshold (m/s)
            self.speed_threshold = 7.0

        def capture_image(self):
            """Capture image from PiCamera"""
            frame = self.picam2.capture_array()
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        def process_license_plate(self, image):
            """Process image to detect and read license plate"""
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blur, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find potential license plate regions
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / float(h)
                
                # License plates typically have aspect ratios between 2.0 and 5.0
                if 2.0 < aspect_ratio < 5.0:
                    plate_region = image[y:y+h, x:x+w]
                    # Perform OCR on the region
                    results = self.reader.readtext(plate_region)
                    
                    if results:
                        return results[0][1]  # Return the detected text
            
            return None

        def save_violation(self, speed, license_plate, image):
            """Save violation details and image"""
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(self.image_dir, f"violation_{timestamp}.jpg")
            
            # Save image
            cv2.imwrite(image_path, image)
            
            # Save to database
            violation_data = {
                "timestamp": timestamp,
                "speed": speed,
                "license_plate": license_plate,
                "image_path": image_path
            }
            
            self.db.add_violation(violation_data)
            
            # Get driver info and send email
            driver_info = self.db.get_driver_info(license_plate)
            if driver_info:
                self.email_sender.send_violation_notification(
                    driver_info["email"],
                    speed,
                    timestamp,
                    image_path
                )

        def run(self):
            """Main monitoring loop"""
            print("Starting speed monitoring system...")
            
            try:
                while True:
                    # Check if speed exceeds threshold
                    if GPIO.input(self.speed_pin):
                        # Capture image
                        image = self.capture_image()
                        
                        # Process license plate
                        license_plate = self.process_license_plate(image)
                        
                        if license_plate:
                            # Get speed from Arduino (implement serial communication)
                            speed = 0  # TODO: Implement serial communication
                            
                            if speed > self.speed_threshold:
                                self.save_violation(speed, license_plate, image)
                    
                    time.sleep(0.1)  # Small delay to prevent CPU overload
                    
            except KeyboardInterrupt:
                print("\nStopping speed monitoring system...")
                GPIO.cleanup()
                self.picam2.stop()

    if __name__ == "__main__":
        monitor = SpeedMonitor()
        monitor.run()
else:
    # Dummy class for non-Raspberry Pi systems to avoid import errors
    class SpeedMonitor:
        def __init__(self):
            print("SpeedMonitor is only supported on Raspberry Pi (Linux, ARM). This is a dummy class.")
        def run(self):
            print("SpeedMonitor cannot run on this platform.") 