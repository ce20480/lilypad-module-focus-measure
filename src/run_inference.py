# Standard library imports
import json
import os
import sys
import traceback
import base64

# Third party imports
import numpy as np
import cv2

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

def run_job(image_path):
    """
    Run the job
    """
    """Combine input file with working directory to get the full path"""
    try:
        focus_measure = variance_of_laplacian_from_path(image_path)

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

    file_path = os.environ.get("INPUT")


    if file_path is None:
        raise ValueError("INPUT environment variable is not set")
    
    output = {"input": file_path, "status": "error"}

    try:
        output = run_job(file_path)

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
