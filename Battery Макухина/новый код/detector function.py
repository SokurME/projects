import cv2
import numpy as np
import time
from collections import deque

class BatteryDetector:
    """DETECTOR FUNCTION - returns "AA", "9V", "CAP" or None (ONLY ONCE)"""
    
    def __init__(self):
        # Central region
        self.roi_size = 0.6
        
        # ========== AUTO CAPTURE FIRST FRAME ==========
        self.reference_background = None
        self.reference_captured = False
        self.frame_counter = 0
        self.capture_delay = 30
        
        # Detection
        self.detection_triggered = False
        self.detected_item = None
        self.detected_area = 0
        self.detection_time = 0
        self.result_returned = False
        
        # ========== STABILIZATION ==========
        self.change_history = deque(maxlen=10)
        self.stable_counter = 0
        self.required_stable_frames = 5
        self.change_area = 0
        self.change_percent = 0
        self.ignore_threshold = 5
        self.has_change = False
        
        # Area thresholds
        self.KRONA_MIN_AREA = 11000  # 9V battery
        self.AA_MAX_AREA = 10000     # AA battery
        
        # Red color for CAP
        self.lower_red1 = np.array([0, 70, 50])
        self.upper_red1 = np.array([10, 255, 255])
        self.lower_red2 = np.array([170, 70, 50])
        self.upper_red2 = np.array([180, 255, 255])
        
        self.roi_total_pixels = 0
    
    def get_center_roi(self, frame):
        h, w = frame.shape[:2]
        roi_w = int(w * self.roi_size)
        roi_h = int(h * self.roi_size)
        roi_x = (w - roi_w) // 2
        roi_y = (h - roi_h) // 2
        self.roi_total_pixels = roi_w * roi_h
        return frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w], (roi_x, roi_y, roi_w, roi_h)
    
    def auto_capture_first_frame(self, frame):
        self.frame_counter += 1
        if not self.reference_captured and self.frame_counter >= self.capture_delay:
            center_roi, _ = self.get_center_roi(frame)
            self.reference_background = center_roi.copy()
            self.reference_captured = True
            print(f"✅ Auto-captured first frame")
            return True
        return False
    
    def is_red(self, roi_item):
        if roi_item.size == 0:
            return False
        hsv = cv2.cvtColor(roi_item, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        red_pixels = cv2.countNonZero(mask1) + cv2.countNonZero(mask2)
        return red_pixels > roi_item.size * 0.15
    
    def is_stable(self):
        if len(self.change_history) < self.required_stable_frames:
            return False
        recent_changes = list(self.change_history)[-5:]
        max_change = max(recent_changes)
        min_change = min(recent_changes)
        return (max_change - min_change) < 100
    
    def reset_stabilization(self):
        self.change_history.clear()
        self.stable_counter = 0
        self.has_change = False
    
    def detect(self, frame):
        """
        Main detection function
        Returns: "AA", "9V", "CAP" or None if no detection
        ONLY RETURNS ONCE PER DETECTION!
        """
        
        # Get center ROI
        center_roi, (roi_x, roi_y, roi_w, roi_h) = self.get_center_roi(frame)
        
        # Auto capture first frame
        self.auto_capture_first_frame(frame)
        
        # No reference yet
        if not self.reference_captured:
            return None
        
        # Check if we already returned the result
        if self.detection_triggered:
            if not self.result_returned:
                self.result_returned = True
                return self.detected_item
            else:
                return None
        
        # Background subtraction
        center_gray = cv2.cvtColor(center_roi, cv2.COLOR_BGR2GRAY)
        ref_gray = cv2.cvtColor(self.reference_background, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(center_gray, ref_gray)
        _, diff_thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        diff_thresh = cv2.morphologyEx(diff_thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        diff_thresh = cv2.morphologyEx(diff_thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        self.change_area = cv2.countNonZero(diff_thresh)
        self.change_percent = (self.change_area / self.roi_total_pixels) * 100
        
        contours, _ = cv2.findContours(diff_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Check if there's a significant change
        significant_change = self.change_percent >= self.ignore_threshold and contours
        
        # Reset history when change disappears
        if not significant_change:
            if self.has_change:
                self.reset_stabilization()
                # Also reset detection when item is removed
                if self.detection_triggered:
                    self.detection_triggered = False
                    self.detected_item = None
                    self.result_returned = False
                    print("🔄 Item removed - ready for new detection")
            return None
        
        # We have a change!
        if not self.has_change:
            self.has_change = True
        
        # Add to history
        self.change_history.append(self.change_area)
        history_count = len(self.change_history)
        
        # Check stability
        if history_count >= self.required_stable_frames and self.is_stable():
            self.stable_counter += 1
            
            # Detection!
            if self.stable_counter >= self.required_stable_frames:
                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    area = cv2.contourArea(largest)
                    
                    if area > 500:
                        x, y, w, h = cv2.boundingRect(largest)
                        roi_item = center_roi[y:y+h, x:x+w]
                        
                        # DETERMINE TYPE
                        if self.is_red(roi_item):
                            item_type = "CAP"
                        elif area > self.KRONA_MIN_AREA:
                            item_type = "9V"
                        elif area < self.AA_MAX_AREA:
                            item_type = "AA"
                        else:
                            item_type = None
                        
                        if item_type:
                            # Save detection
                            self.detection_triggered = True
                            self.detected_item = item_type
                            self.detected_area = int(area)
                            self.detection_time = time.time()
                            self.result_returned = False
                            
                            print(f"✅ DETECTED: {item_type} - {int(area)}px")
                            return item_type
        else:
            self.stable_counter = 0
        
        return None
    
    def reset(self):
        """Reset detector state completely"""
        self.detection_triggered = False
        self.detected_item = None
        self.detected_area = 0
        self.result_returned = False
        self.reset_stabilization()
        self.reference_captured = False
        self.frame_counter = 0
        print("🔄 Detector fully reset")


# ========== CORRECT USAGE EXAMPLE ==========

def main():
    """Example of how to use the detector function"""
    
    # Initialize detector
    detector = BatteryDetector()
    
    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("\n" + "="*60)
    print("BATTERY DETECTOR FUNCTION - CORRECT USAGE")
    print("="*60)
    print("\n📌 Returns:")
    print("   • 'AA'  - AA battery")
    print("   • '9V'  - 9V battery (Krona)")
    print("   • 'CAP' - Red cap")
    print("   • None  - No detection")
    print("\n⏳ Auto-capturing first frame at frame 30...")
    print("="*60 + "\n")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # CALL DETECT ON EACH FRAME - THIS IS THE ONLY PLACE!
        result = detector.detect(frame)
        
        # USE THE RESULT - prints ONLY ONCE per detection
        if result:
            print(f"🎯 DETECTED: {result}")
        
        # Show frame (optional)
        cv2.imshow("Detector", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            detector.reset()
    
    cap.release()
    cv2.destroyAllWindows()


# ========== THIS IS THE ONLY CODE THAT RUNS ==========
if __name__ == "__main__":
    # ONLY call main() - don't put extra code here!
    main()
    
