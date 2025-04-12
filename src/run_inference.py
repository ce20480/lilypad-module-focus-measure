# Standard library imports
import json
import os
import sys
import traceback

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
        output = {
            "focus_measure": focus_measure,
            "status": "success",
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


def main(input_bytes):
    print("Starting inference...")

    file_bytes = input_bytes
    if input_bytes is None:
        file_bytes = os.environ["INPUT"]


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
    with open("A.jpg", "rb") as img_file:
        image_bytes = img_file.read()

    main(image_bytes)
