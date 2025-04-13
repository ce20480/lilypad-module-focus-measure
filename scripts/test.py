import subprocess
import base64
import os
import json
import re
import sys

def read_and_encode_image(image_path: str) -> str:
    """Read an image file and return its base64-encoded string"""
    with open(image_path, "rb") as f:
        file_bytes = f.read()
    return base64.b64encode(file_bytes).decode("utf-8")

def extract_result_path(stdout: str) -> str:
    """Extracts the Lilypad result path from CLI output"""
    lines = stdout.strip().split("\n")
    for line in reversed(lines):
        if "open /tmp/lilypad/data/downloaded-files" in line:
            result_dir = line.replace("open ", "").strip()
            return os.path.join(result_dir, "outputs", "result.json")
    
    # Fallback to regex
    match = re.search(r"open\s+(/tmp/lilypad/data/downloaded-files/\S+)", stdout)
    if match:
        result_dir = match.group(1)
        return os.path.join(result_dir, "outputs", "result.json")
    
    raise ValueError("Could not find result.json path in Lilypad output")

def run_lilypad_focus_module(image_path: str):
    encoded = read_and_encode_image(image_path)
    
    env = os.environ.copy()
    env["WEB3_PRIVATE_KEY"] = os.getenv("WEB3_PRIVATE_KEY", "")
    env["INPUT"] = encoded

    # Run the Lilypad command
    command = [
        "lilypad",
        "run",
        "github.com/ce20480/lilypad-module-focus-measure:74541ee759a92d8dd19d7fdf8a835eae57168e76",
    ]

    print("🚀 Running Lilypad focus measure module...")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        print("✅ Lilypad module completed.")
        print("---- CLI STDOUT ----")
        print(result.stdout)
        print("--------------------")

        # Extract the result path
        result_path = extract_result_path(result.stdout)

        # Load the result JSON
        if not os.path.exists(result_path):
            raise FileNotFoundError(f"Result file not found: {result_path}")

        with open(result_path, "r") as f:
            data = json.load(f)

        print("✅ Focus measure output:")
        print(json.dumps(data, indent=2))

    except subprocess.CalledProcessError as e:
        print("❌ Lilypad job failed.")
        print("---- STDERR ----")
        print(e.stderr)
        print("---- STDOUT ----")
        print(e.stdout)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_focus_module.py path/to/image.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    run_lilypad_focus_module(image_path)
