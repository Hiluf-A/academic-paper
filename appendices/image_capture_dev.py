import cv2
import numpy as np
import easyocr
import time
from datetime import datetime
import os
import json
from database.db_manager import DatabaseManager
from notification.email_sender import EmailSender

class SpeedMonitorDev:
    def __init__(self):
        # Initialize camera (using webcam for development)
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("Could not open camera")
        
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
        """Capture image from webcam"""
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Failed to capture image")
        return frame

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
        print("Starting speed monitoring system (Development Mode)...")
        print("Press 'q' to quit")
        
        try:
            while True:
                # Capture image
                image = self.capture_image()
                
                # Display the image
                cv2.imshow('Speed Monitor', image)
                
                # Process license plate
                license_plate = self.process_license_plate(image)
                
                if license_plate:
                    print(f"Detected license plate: {license_plate}")
                    # For development, simulate speed detection
                    speed = 10.0  # Simulated speed
                    
                    if speed > self.speed_threshold:
                        self.save_violation(speed, license_plate, image)
                
                # Check for quit command
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                time.sleep(0.1)  # Small delay to prevent CPU overload
                
        except KeyboardInterrupt:
            print("\nStopping speed monitoring system...")
        finally:
            self.cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    monitor = SpeedMonitorDev()
    monitor.run() 