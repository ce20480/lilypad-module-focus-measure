import base64
import cv2
import numpy as np
import os
import tempfile

def create_temp_file_from_bytes(image_bytes):
    # Convert bytes to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_file.write(image_bytes)
        temp_file_path = temp_file.name
    return temp_file_path

def variance_of_laplacian_from_path(image_path):
    # Check if file exists
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file {image_path} not found")
    
    # Load the image and check if it was loaded successfully
    cv2_image = cv2.imread(image_path)
    if cv2_image is None:
        raise ValueError(f"Failed to load image {image_path}. Check if it's a valid image format.")
        
    # compute the Laplacian of the image and then return the focus measure
    gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
    fm = cv2.Laplacian(gray, cv2.CV_64F).var()
    return fm

def variance_of_laplacian_from_bytes(image_bytes):
    try: 
        # Convert bytes to a numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # if img is None:
        #     # If decoding fails, try the temporary file approach
        #     print("Direct decoding failed, using temp file approach")
        #     temp_file_path = create_temp_file_from_bytes(image_bytes)
        #     try:
        #         fm = variance_of_laplacian_from_path(temp_file_path)
        #     finally:
        #         # Clean up the temporary file
        #         if os.path.exists(temp_file_path):
        #             os.unlink(temp_file_path)
        #     return fm
        
        # Process the image
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        fm = cv2.Laplacian(gray, cv2.CV_64F).var()
        return fm
        
    except Exception as e:
        print(f"Error processing image: {e}")
        raise ValueError(f"Failed to process image bytes: {str(e)}")

if __name__ == "__main__":
    # Load image as bytes
    with open("A.jpg", "rb") as img_file:
        image_bytes = img_file.read()
        # encoded = base64.b64encode(image_bytes).decode("utf-8")

    # Print base64 string (optional)
    # print(encoded)

    # Decode and test blur detection
    # decoded_bytes = base64.b64decode(encoded)
    print(variance_of_laplacian_from_bytes(image_bytes))
