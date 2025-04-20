import cv2
import numpy as np
from PIL import Image
import os

def extract_clothing_only(image_path, output_path):
    """
    Extract only the clothing/dress from an image and save with transparent background
    """
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image {image_path}")
        return False
    
    # Convert to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    
    # 1. Create initial mask using GrabCut
    mask = np.zeros(img.shape[:2], np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    
    # Define ROI - focus on center portion where clothing typically is
    roi = (int(w*0.1), int(h*0.1), int(w*0.8), int(h*0.8))
    
    try:
        cv2.grabCut(img, mask, roi, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        mask = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8') * 255
    except:
        print("Using fallback rectangle method")
        mask = np.zeros(img.shape[:2], np.uint8)
        cv2.rectangle(mask, (roi[0], roi[1]), (roi[0]+roi[2], roi[1]+roi[3]), 255, -1)
    
    # 2. Remove skin areas
    # Convert to HSV for skin detection
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_skin = np.array([0, 20, 70], dtype=np.uint8)
    upper_skin = np.array([25, 255, 255], dtype=np.uint8)
    skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(skin_mask))
    
    # 3. Find largest contour (main clothing item)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        final_mask = np.zeros_like(mask)
        cv2.drawContours(final_mask, [largest_contour], -1, 255, -1)
    else:
        final_mask = mask
    
    # 4. Create transparent result
    result = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2RGBA)
    result[:,:,3] = final_mask
    
    # 5. Save just the clothing with transparent background
    Image.fromarray(result).save(output_path)
    return True

# Example usage:
input_image = "another.jpg"  # Change to your image path
output_image = "extracted_dress.png"

if extract_clothing_only(input_image, output_image):
    print(f"Success! Extracted dress saved to {output_image}")
else:
    print("Extraction failed")