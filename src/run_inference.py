# Standard library imports
import json
import os
import sys
import traceback
import tempfile
import argparse

# Third party imports
import numpy as np
import cv2

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
        
        if img is None:
            # If decoding fails, try the temporary file approach
            print("Direct decoding failed, using temp file approach")
            temp_file_path = create_temp_file_from_bytes(image_bytes)
            try:
                fm = variance_of_laplacian_from_path(temp_file_path)
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            return fm
        
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
        output.update(
            {
                "file_bytes": file_bytes,
            }
        )

    except Exception as error:
        print("❌ Error during processing:", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        output["error"] = str(error)

    os.makedirs("/outputs", exist_ok=True)
    output_path = "/outputs/result.json"

    try:
        with open(output_path, "w") as file:
            json.dump({"output": output, "file_bytes": file_bytes}, file, indent=2)
        print(
            f"✅ Successfully wrote output to {output_path}",
        )
    except Exception as error:
        print(f"❌ Error writing output file: {error}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    args = parser.parse_args()
    input_bytes = args.input
    main(input_bytes)
