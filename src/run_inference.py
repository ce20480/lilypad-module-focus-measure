# Standard library imports
import json
import os
import sys
import traceback
import base64

# Third party imports
import numpy as np
import cv2

def variance_of_laplacian_from_bytes(image_bytes):
    try: 
        # Convert bytes to a numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Process the image
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        fm = cv2.Laplacian(gray, cv2.CV_64F).var()
        return fm
        
    except Exception as e:
        print(f"Error processing image: {e}")
        raise ValueError(f"Failed to process image bytes: {str(e)}")

def run_job(image_bytes):
    """
    Run the job
    """
    """Combine input file with working directory to get the full path"""
    try:
        focus_measure = variance_of_laplacian_from_bytes(image_bytes)

        # Check if focus measure meets threshold
        is_blurry = focus_measure < 100
        
        if is_blurry:
            return {
                "success": False,
                "message": "Image is too blurry",
                "focus_measure": focus_measure,
                "threshold": 100
            }
        
        # Calculate normalized score (higher is better)
        # Scale between 0-1 with 1 being perfect focus
        normalized_score = min(1.0, focus_measure / (100 * 2))
        
        output = {
            "success": True,
            "message": "Image has acceptable focus",
            "focus_measure": focus_measure,
            "score": normalized_score,
            "threshold": 100
        }

        return output

    except Exception as error:
        print(
            f"❌ Error running job: {error}",
            file=sys.stderr,
            flush=True,
        )
        traceback.print_exc(file=sys.stderr)
        raise


def main():
    print("Starting inference...")

    file_bytes = os.environ.get("INPUT")


    if file_bytes is None:
        raise ValueError("INPUT environment variable is not set")
    
    # check if file bytes is actually bytes
    if not isinstance(file_bytes, str):
        try:
            file_bytes = base64.b64decode(file_bytes)
        except Exception as e:
            raise ValueError(f"Failed to decode base64 image: {str(e)}")

    output = {"input": file_bytes, "status": "error"}

    try:
        output = run_job(file_bytes)

    except Exception as error:
        print("❌ Error during processing:", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        output["error"] = str(error)

    os.makedirs("/outputs", exist_ok=True)
    output_path = "/outputs/result.json"

    try:
        with open(output_path, "w") as file:
            json.dump({"output": output}, file, indent=2)
        print(
            f"✅ Successfully wrote output to {output_path}",
        )
    except Exception as error:
        print(f"❌ Error writing output file: {error}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()
