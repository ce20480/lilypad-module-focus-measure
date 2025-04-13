import subprocess
import base64
import os
import json
import re
import sys
import argparse

def read_and_encode_image(image_path: str) -> str:
    """Read an image file and return its base64-encoded string."""
    with open(image_path, "rb") as f:
        file_bytes = f.read()
    return base64.b64encode(file_bytes).decode("utf-8")

def extract_result_path(stdout: str) -> str:
    """Extracts the Lilypad result path from CLI output."""
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

def run_lilypad_focus_module(image_path: str, mode: str):
    """
    Run the focus measure module either in:
      - 'local' mode, using Docker
      - 'lilypad' mode, using the Lilypad CLI
    """
    encoded = read_and_encode_image(image_path)

    env = os.environ.copy()
    # Typically, you'd set your WEB3_PRIVATE_KEY here if using Lilypad
    # env["WEB3_PRIVATE_KEY"] = os.getenv("WEB3_PRIVATE_KEY", "")
    
    # The module code expects INPUT in the environment for both modes,
    # but how it's passed to the container differs in 'docker run' vs. Lilypad.
    env["INPUT"] = encoded

    if mode == "local":
        # Example: run Docker image directly
        # NOTE: This is a placeholder; see caveats below.
        command = [
            "docker", "run",
            "-e", f"INPUT={encoded}",              # pass environment var
            "--rm",                     # remove container on exit
            "-v", f"{os.getcwd()}:/outputs",  # mount current dir if needed
            "aviini/lilypad-module-focus-measure:latest",
        ]
    elif mode == "lilypad":
        # Run via Lilypad CLI
        if not env.get("WEB3_PRIVATE_KEY"):
            print("⚠️  WEB3_PRIVATE_KEY is not set. If required, this may fail.")
        command = [
            "lilypad",
            "run",
            "github.com/ce20480/lilypad-module-focus-measure:2e036e9a915df37ab40a7e981e1c4f12854f5a95",
        ]
    else:
        raise ValueError(f"Invalid mode: {mode}")

    print(f"🚀 Running focus measure module in '{mode}' mode...")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            env=env,
            shell=False  # safer than True
        )
        print("✅ Module completed.")
        print("---- CLI STDOUT ----")
        print(result.stdout)
        print("--------------------")

        # For the Lilypad run, we'll parse the local result path from stdout
        # If you're doing local Docker, see "Caveats" below
        if mode == "local":
            # If your local Docker container writes to /outputs/result.json
            # we can read it from the host's ./result.json after the container exits
            result_path = os.path.join(os.getcwd(), "result.json")
        else:
            # For Lilypad
            result_path = extract_result_path(result.stdout)

        # Load the result JSON
        if not os.path.exists(result_path):
            raise FileNotFoundError(f"Result file not found: {result_path}")

        with open(result_path, "r") as f:
            data = json.load(f)

        print("✅ Focus measure output:")
        print(json.dumps(data, indent=2))

    except subprocess.CalledProcessError as e:
        print("❌ Module job failed.")
        print("---- STDERR ----")
        print(e.stderr)
        print("---- STDOUT ----")
        print(e.stdout)
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Test focus measure module.")
    parser.add_argument("--image", required=True, help="Path to the image file")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--local", action="store_true", help="Run the module locally via Docker")
    group.add_argument("--lilypad", action="store_true", help="Run the module on Lilypad")

    args = parser.parse_args()

    if args.local:
        run_lilypad_focus_module(args.image, "local")
    elif args.lilypad:
        run_lilypad_focus_module(args.image, "lilypad")

if __name__ == "__main__":
    main()
