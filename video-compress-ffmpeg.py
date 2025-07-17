import subprocess
import os
import re
from tqdm import tqdm

def get_video_duration(input_path):
    """
    Gets the duration of a video file using ffprobe.

    Args:
        input_path (str): The full path to the video file.

    Returns:
        float: The duration of the video in seconds, or None if an error occurs.
    """
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return float(result.stdout)
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        # Return None if ffprobe is not found or if there's an error getting duration
        return None

def compress_video(input_path, output_path, crf=28):
    """
    Compresses a video using ffmpeg and displays a progress bar.

    This function requires that ffmpeg is installed and accessible in the system's PATH.
    You can download it from https://ffmpeg.org/download.html

    It also requires the 'tqdm' library. Install it with:
    pip install tqdm

    Args:
        input_path (str): The full path to the input video file.
        output_path (str): The full path where the compressed video will be saved.
        crf (int): The Constant Rate Factor. A lower value means higher quality
                     and a larger file size. A typical range is 18-28.
                     The default is 28.
    """
    # --- Input Validation ---
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at '{input_path}'")
        return

    # --- Get Video Duration for Progress Bar ---
    total_duration = get_video_duration(input_path)
    if total_duration is None:
        print("Warning: Could not get video duration. Progress bar will not be shown.")

    # --- FFmpeg Command Construction ---
    command = [
        'ffmpeg',
        '-y',  # Overwrite output file if it exists
        '-i', input_path,
        '-c:v', 'libx264',
        '-crf', str(crf),
        '-preset', 'slow',
        '-c:a', 'copy',
        output_path
    ]

    # --- Execute the Command with Progress Bar ---
    print(f"Starting compression for '{input_path}'...")
    print(f"FFmpeg command: {' '.join(command)}")

    try:
        # Use Popen to start the process and capture stderr
        process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True)

        with tqdm(total=total_duration, unit='s', desc="Compressing", dynamic_ncols=True) if total_duration else open(os.devnull, 'w') as pbar:
            previous_time = 0
            for line in process.stderr:
                # Look for the time in ffmpeg's output
                time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
                if time_match and isinstance(pbar, tqdm):
                    hours = int(time_match.group(1))
                    minutes = int(time_match.group(2))
                    seconds = int(time_match.group(3))
                    centiseconds = int(time_match.group(4))
                    current_time = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
                    
                    # Calculate progress and update the bar
                    pbar.update(current_time - previous_time)
                    previous_time = current_time

        process.wait() # Wait for the process to finish
        if process.returncode != 0:
            print(f"\nAn error occurred during compression. FFmpeg returned code {process.returncode}")
        else:
            print("\nVideo compressed successfully!")

    except FileNotFoundError:
        print("Error: 'ffmpeg' or 'ffprobe' not found. Please ensure it is installed and in your system's PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    # --- How to use the function ---

    # Make sure to replace these paths with your actual file paths.
    input_video_path = 'kellogs 1.0.mov'
    compressed_video_path = 'compressed_output.mp4'

    # Create a dummy input file for testing if it doesn't exist.
    if not os.path.exists(input_video_path):
        print(f"Creating a dummy input file: '{input_video_path}'")
        dummy_command = [
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=10:size=1280x720:rate=30',
            '-c:v', 'libx264', '-t', '10', input_video_path
        ]
        try:
            subprocess.run(dummy_command, check=True, capture_output=True, text=True)
            print("Dummy file created.")
        except (Exception):
            print("Could not create a dummy file. Please provide your own 'input.mp4'.")
            print("This usually means ffmpeg is not installed.")

    # Call the compression function with a CRF value of 28
    if os.path.exists(input_video_path):
        compress_video(input_video_path, compressed_video_path, crf=28)
