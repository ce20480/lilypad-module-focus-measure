import argparse
import os
import subprocess
import sys
import uuid

IMAGE_DEFAULT = "aviini/lilypad-module-focus-measure:v1"

def run_local_docker(image_path: str):
    """
    Example 'local' flow: Mount the local file at runtime.
    This WILL NOT work on Lilypad, only on your local Docker engine.
    """
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        sys.exit(1)
    
    print(f"🔨 Running container locally with a file mount for {image_path}...")

    # The container must be coded to read from /input/image.jpg
    # i.e., in run_inference.py, you'd do:
    #   file_path = os.environ.get("INPUT_FILE", "/input/image.jpg")
    #   with open(file_path, "rb") as f: ...

    cmd = [
        "docker", "run",
        "--rm",
        "-v", f"{os.path.abspath(image_path)}:/input/image.jpg:ro",
        "-e", "INPUT_FILE=/input/image.jpg", 
        IMAGE_DEFAULT
    ]
    print("Running:", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    if result.returncode == 0:
        print("✅ Local Docker run completed successfully.")
    else:
        print("❌ Local Docker run failed.")
        sys.exit(result.returncode)


def build_and_push_image(embed_file: bool = False, file_path: str = "") -> str:
    """
    Dynamically build a Docker image from the local Dockerfile.
    Optionally embed a specific file into the image.
    
    This approach is typically not used for frequent, dynamic files,
    but here it is for demonstration.
    """
    unique_tag = str(uuid.uuid4())[:8]
    image_name = f"your-dockerhub-username/focus-measure:{unique_tag}"

    # We'll create a minimal Dockerfile “on the fly” if embed_file is True
    # Or you could just reuse an existing Dockerfile.
    # For demonstration, let's copy your existing Dockerfile but add a line for the file.

    # 1. If not embedding a file, just build from your local Dockerfile
    if not embed_file:
        cmd = ["docker", "build", "-t", image_name, "."]
        print("🔨 Building Docker image from existing Dockerfile (no file embed).")
    else:
        if not os.path.exists(file_path):
            print(f"❌ File not found for embedding: {file_path}")
            sys.exit(1)

        # Create a Dockerfile snippet that copies the file into /app/target_file
        # Then we’ll use a separate Dockerfile so we don’t overwrite your main Dockerfile
        custom_dockerfile = "Dockerfile.embed"
        base_name = os.path.basename(file_path)
        with open(custom_dockerfile, "w") as df:
            df.write(
f"""FROM python:3.12

RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    libgl1 \\
    libglib2.0-0 \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY models ./models

COPY {base_name} ./scr/images/{base_name.split('.')[0] + '_' + unique_tag + '.' + base_name.split('.')[1]}

ENV HF_HOME=/app/models \\
    TRANSFORMERS_OFFLINE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /outputs && chmod 755 /outputs

ENTRYPOINT ["python", "/app/src/run_inference.py"]
"""
            )
        # Now copy the file into the build context
        # Just ensure the file is physically in the same directory, or pass a build context
        cmd = [
            "cp", file_path, os.path.basename(file_path)
        ]
        subprocess.run(cmd, check=True)

        # 2. Build using the newly created Dockerfile
        cmd = [
            "docker", "build", "-f", custom_dockerfile, "-t", image_name, "."
        ]
        print(f"🔨 Building Docker image with embedded file: {file_path}")

    # 3. Actually run the build
    subprocess.run(cmd, check=True)

    # 4. Push to Docker Hub (so Lilypad can pull it)
    cmd_push = ["docker", "push", image_name]
    print(f"🔨 Pushing image to registry: {image_name}")
    subprocess.run(cmd_push, check=True)

    print(f"✅ Built & pushed image: {image_name}")
    return image_name


def run_lilypad(image_name: str):
    """
    Example: run the freshly built image on Lilypad.
    Typically you also pass -i arguments if needed, or rely on environment in the module.
    """
    print(f"🚀 Running Lilypad job with image: {image_name} ...")

    cmd = [
        "lilypad",
        "run",
        image_name,
        # Optionally pass -i INPUT=someValue, if your run_inference.py expects environment
        # e.g. "-i", 'MYENV="stuff"'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("Lilypad STDOUT:\n", result.stdout)
    print("Lilypad STDERR:\n", result.stderr)

    if result.returncode == 0:
        print("✅ Lilypad job started successfully (note it might run for a while).")
    else:
        print("❌ Lilypad job failed to start.")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Demo script for local Docker vs. Lilypad runs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand 1: local test with volume mount
    local_parser = subparsers.add_parser("local", help="Run container locally with a file mount")
    local_parser.add_argument("--image-file", required=True, help="Path to local image file to mount")

    # Subcommand 2: build, push, run
    build_parser = subparsers.add_parser("build_lilypad", help="Build Docker image (optionally embed file) and run on Lilypad")
    build_parser.add_argument("--embed-file", help="Path of file to embed into the image (optional). If not set, no file is embedded.")

    args = parser.parse_args()

    if args.command == "local":
        run_local_docker(args.image_file)
    elif args.command == "build_lilypad":
        if args.embed_file:
            # embed the file into the container
            new_image = build_and_push_image(embed_file=True, file_path=args.embed_file)
        else:
            new_image = build_and_push_image(embed_file=False)
        run_lilypad(new_image)


if __name__ == "__main__":
    main()
