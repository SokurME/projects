import cv2
import numpy as np
import time
from collections import deque

class AutoFirstFrameDetector:
    """FULLY AUTOMATIC DETECTION - WITH DIFFERENCE DISPLAY"""
    
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
        self.detection_frame = None
        self.detection_time = 0
        
        # ========== STABILIZATION ==========
        self.change_history = deque(maxlen=10)
        self.stable_counter = 0
        self.required_stable_frames = 5
        self.change_area = 0
        self.change_percent = 0
        self.ignore_threshold = 5
        self.has_change = False
        
        # Area thresholds
        self.KRONA_MIN_AREA = 11000
        self.AA_MAX_AREA = 10000
        
        # Red color
        self.lower_red1 = np.array([0, 70, 50])
        self.upper_red1 = np.array([10, 255, 255])
        self.lower_red2 = np.array([170, 70, 50])
        self.upper_red2 = np.array([180, 255, 255])
        
        self.roi_total_pixels = 0
        
        # Difference display
        self.diff_display = None
        self.diff_thresh_display = None
    
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
            print(f"\n{'='*60}")
            print(f"✅ AUTO CAPTURED FIRST FRAME!")
            print(f"   Frame: {self.frame_counter}")
            print(f"   ROI Size: {self.roi_total_pixels}px")
            print(f"{'='*60}\n")
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
        """SIMPLE stability check"""
        if len(self.change_history) < self.required_stable_frames:
            return False
        
        recent_changes = list(self.change_history)[-5:]
        max_change = max(recent_changes)
        min_change = min(recent_changes)
        
        return (max_change - min_change) < 100
    
    def reset_stabilization(self):
        """RESET all stabilization data"""
        self.change_history.clear()
        self.stable_counter = 0
        self.has_change = False
    
    def detect(self, frame):
        display = frame.copy()
        
        center_roi, (roi_x, roi_y, roi_w, roi_h) = self.get_center_roi(frame)
        
        # Draw search area
        cv2.rectangle(display, (roi_x, roi_y), (roi_x+roi_w, roi_y+roi_h), (0, 255, 255), 3)
        cv2.putText(display, "SEARCH AREA", (roi_x, roi_y-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Auto capture first frame
        self.auto_capture_first_frame(frame)
        
        # No reference yet
        if not self.reference_captured:
            cv2.putText(display, f"AUTO CAPTURE: {self.frame_counter}/{self.capture_delay}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            return display, "WAITING_FOR_BG"
        
        # Already detected
        if self.detection_triggered:
            cv2.putText(display, f"✅ DETECTED: {self.detected_item}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(display, f"📐 AREA: {self.detected_area}px", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            return display, self.detected_item
        
        # ========== BACKGROUND SUBTRACTION ==========
        center_gray = cv2.cvtColor(center_roi, cv2.COLOR_BGR2GRAY)
        ref_gray = cv2.cvtColor(self.reference_background, cv2.COLOR_BGR2GRAY)
        
        # Calculate difference
        diff = cv2.absdiff(center_gray, ref_gray)
        
        # Thresholded difference
        _, diff_thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        # Morphology
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        diff_thresh = cv2.morphologyEx(diff_thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        diff_thresh = cv2.morphologyEx(diff_thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Colorized difference for display
        diff_color = cv2.cvtColor(diff, cv2.COLOR_GRAY2BGR)
        diff_color[diff > 25] = (0, 0, 255)  # Red for difference
        
        # Threshold display
        diff_thresh_display = cv2.cvtColor(diff_thresh, cv2.COLOR_GRAY2BGR)
        diff_thresh_display[diff_thresh == 255] = (0, 255, 0)  # Green for detected
        
        # Save for external display
        self.diff_display = diff_color
        self.diff_thresh_display = diff_thresh_display
        
        self.change_area = cv2.countNonZero(diff_thresh)
        self.change_percent = (self.change_area / self.roi_total_pixels) * 100
        
        contours, _ = cv2.findContours(diff_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # ========== CHECK IF THERE'S A SIGNIFICANT CHANGE ==========
        significant_change = self.change_percent >= self.ignore_threshold and contours
        
        # ========== RESET HISTORY WHEN CHANGE DISAPPEARS ==========
        if not significant_change:
            if self.has_change:
                print("🔄 Change gone - resetting stabilization")
                self.reset_stabilization()
            cv2.putText(display, "EMPTY", (roi_x, roi_y+roi_h+30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2)
            return display, "EMPTY"
        
        # ========== WE HAVE A CHANGE! ==========
        if not self.has_change:
            print("🎯 New change detected - starting stabilization")
            self.has_change = True
        
        cv2.putText(display, f"⚠️ CHANGE: {self.change_percent:.1f}%", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Add to history
        self.change_history.append(self.change_area)
        
        # Show history count
        history_count = len(self.change_history)
        cv2.putText(display, f"HISTORY: {history_count}/{self.required_stable_frames}", (10, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Check stability
        if history_count >= self.required_stable_frames:
            if self.is_stable():
                self.stable_counter += 1
                cv2.putText(display, f"✅ STABLE: {self.stable_counter}/{self.required_stable_frames}", (10, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Progress bar
                bar_width = 200
                progress = int(bar_width * self.stable_counter / self.required_stable_frames)
                cv2.rectangle(display, (10, 160), (10+bar_width, 180), (50, 50, 50), 1)
                cv2.rectangle(display, (10, 160), (10+progress, 180), (0, 255, 0), -1)
                
                # DETECTION!
                if self.stable_counter >= self.required_stable_frames:
                    if contours:
                        largest = max(contours, key=cv2.contourArea)
                        area = cv2.contourArea(largest)
                        
                        if area > 500:
                            x, y, w, h = cv2.boundingRect(largest)
                            x_global = roi_x + x
                            y_global = roi_y + y
                            roi_item = center_roi[y:y+h, x:x+w]
                            
                            # DETERMINE TYPE
                            if self.is_red(roi_item):
                                item_type = "CAP"
                                color = (0, 0, 255)
                            elif area > self.KRONA_MIN_AREA:
                                item_type = "KRONA"
                                color = (0, 165, 255)
                            elif area < self.AA_MAX_AREA:
                                item_type = "AA"
                                color = (0, 255, 0)
                            else:
                                item_type = "OBJECT"
                                color = (255, 255, 255)
                            
                            # SAVE DETECTION
                            self.detection_triggered = True
                            self.detected_item = item_type
                            self.detected_area = int(area)
                            self.detection_frame = frame.copy()
                            
                            # DRAW RESULT
                            cv2.rectangle(display, (x_global, y_global),
                                        (x_global+w, y_global+h), color, 4)
                            cv2.putText(display, item_type, (x_global, y_global-10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 3)
                            cv2.putText(display, f"AREA: {int(area)}px", (x_global, y_global+h+30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                            
                            print(f"\n{'='*60}")
                            print(f"🚨 DETECTION! FOUND: {item_type}")
                            print(f"   📊 AREA: {int(area)}px")
                            print(f"   📈 CHANGE: {self.change_percent:.1f}%")
                            print(f"{'='*60}\n")
                            
                            return display, item_type
            else:
                self.stable_counter = 0
                cv2.putText(display, "⏳ NOT STABLE YET", (10, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Show current info
        cv2.putText(display, f"CHANGE: {self.change_area}px ({self.change_percent:.1f}%)", (10, 210),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display, f"IGNORE < {self.ignore_threshold}%", (10, 230),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)
        
        return display, "WAITING"


def main():
    # Try different camera indices
    cap = None
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"✅ Camera {i} opened")
            break
    
    if not cap or not cap.isOpened():
        print("❌ Could not open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    detector = AutoFirstFrameDetector()
    
    print("="*80)
    print("🚀 DIFFERENCE DISPLAY - SHOWING BACKGROUND SUBTRACTION")
    print("="*80)
    print("\n📌 WINDOWS:")
    print("   • Main - Detection view")
    print("   • Difference - Raw difference (red = change)")
    print("   • Threshold - Binary mask (green = detected)")
    print("\n🎯 DETECTION RULES:")
    print("   🔴 RED = CAP")
    print("   🟢 AREA < 10000px = AA")
    print("   🟠 AREA > 11000px = KRONA")
    print("\n⌨️  CONTROLS:")
    print("   'q' - quit")
    print("   'r' - reset")
    print("="*80)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        display, status = detector.detect(frame)
        
        # Show difference windows
        if detector.diff_display is not None:
            # Resize difference displays to 320x240
            diff_small = cv2.resize(detector.diff_display, (320, 240))
            thresh_small = cv2.resize(detector.diff_thresh_display, (320, 240))
            
            # Add labels
            cv2.putText(diff_small, "RAW DIFFERENCE", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(thresh_small, "THRESHOLD MASK", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow("Difference", diff_small)
            cv2.imshow("Threshold", thresh_small)
        
        # Center crosshair
        h, w = display.shape[:2]
        cv2.line(display, (w//2, 0), (w//2, h), (0, 0, 255), 1)
        cv2.line(display, (0, h//2), (w, h//2), (0, 0, 255), 1)
        
        cv2.imshow("Main Detector", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            detector.detection_triggered = False
            detector.detected_item = None
            detector.detected_area = 0
            detector.reset_stabilization()
            print("\n🔄 DETECTION RESET\n")
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
