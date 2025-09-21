import argparse
import cv2
from database.db_manager import DatabaseManager
from notification.email_sender import EmailSender
import easyocr
import os
from datetime import datetime

SPEED_THRESHOLD = 7.0  # m/s


def process_license_plate(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not read image: {image_path}")
        return None
    reader = easyocr.Reader(['en'])
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)
        if 2.0 < aspect_ratio < 5.0:
            plate_region = image[y:y+h, x:x+w]
            results = reader.readtext(plate_region)
            if results:
                return results[0][1]
    return None

def main():
    parser = argparse.ArgumentParser(description="Process demo image and speed.")
    parser.add_argument('--image', required=True, help='Path to the image file')
    parser.add_argument('--speed', type=float, required=True, help='Speed value (m/s)')
    args = parser.parse_args()

    print(f"Received speed: {args.speed} m/s")
    if args.speed > SPEED_THRESHOLD:
        print(f"Speed exceeds threshold ({SPEED_THRESHOLD} m/s). Processing image...")
        license_plate = process_license_plate(args.image)
        if license_plate:
            print(f"Detected license plate: {license_plate}")
            # Save violation
            db = DatabaseManager()
            email_sender = EmailSender()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_dir = "captured_images"
            os.makedirs(image_dir, exist_ok=True)
            image_path = os.path.join(image_dir, f"violation_{timestamp}.jpg")
            cv2.imwrite(image_path, cv2.imread(args.image))
            violation_data = {
                "timestamp": timestamp,
                "speed": args.speed,
                "license_plate": license_plate,
                "image_path": image_path
            }
            db.add_violation(violation_data)
            driver_info = db.get_driver_info(license_plate)
            if driver_info:
                email_sender.send_violation_notification(
                    driver_info["email"],
                    args.speed,
                    timestamp,
                    image_path
                )
                print(f"Violation logged and email sent to {driver_info['email']}")
            else:
                print("Driver not found in database. No email sent.")
        else:
            print("No license plate detected.")
    else:
        print(f"Speed is within the limit ({SPEED_THRESHOLD} m/s). No action taken.")

if __name__ == "__main__":
    main() 