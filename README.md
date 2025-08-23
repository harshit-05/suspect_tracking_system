# CCTV based Suspect Tracking System

![License](https://img.shields.io/github/license/harshit-05/suspect_tracking_system)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Issues](https://img.shields.io/github/issues/harshit-05/suspect_tracking_system)

This repository contains a system for real-time object detection and tracking in video feeds, designed for CCTV surveillance applications. It uses the YOLOv8 model for efficient object detection and tracking.

A key feature of this system is its interactive suspect tracking. Users can click on a detected person's bounding box to designate them as a "suspect," which highlights their track and opens a zoomed-in view for enhanced monitoring.

## Features

- **Real-time Object Detection:** Utilizes the powerful YOLOv8 model for fast and accurate detections.
- **Multi-Object Tracking:** Implements trackers like DeepSORT to track multiple objects (specifically persons) seamlessly.
- **Interactive Suspect Selection:** Click on any person's bounding box in the video stream to mark them as a suspect.
- **Picture-in-Picture (PiP) Suspect View:** Automatically displays a zoomed-in window focusing on the selected suspect for enhanced visibility.
- **Customizable:** Easily configure paths, model parameters, confidence thresholds, and other settings in `main.py`.
- **Video Output:** Saves the processed video with all tracking annotations and the PiP view to a file.

## Example Output

![Tracking Output Example](docs/example_tracking.gif)  
*Suspect selected and zoomed-in view in the top-right corner.*

*(If you have a sample output image/gif, place it in `docs/` and update the path above.)*

## Project Structure

```
├── main.py                 # Main script to run the tracking system
├── yolov8m.pt              # Pre-trained YOLOv8 model weights
├── video_generation.py     # Utility script to create video from image sequences
├── detectors/
│   └── yolo_detector.py    # YOLOv8 detector implementation
├── trackers/
│   ├── deepsort_wrapper.py # Wrapper for the DeepSORT tracking algorithm
│   └── bytetrack_wrapper.py  # Wrapper for the ByteTrack tracking algorithm
└── utils/
    ├── draw_utils.py       # Functions for drawing bounding boxes, labels, and the PiP view
    └── video_io.py         # Video input/output helper functions
```

## Setup and Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/harshit-05/suspect_tracking_system.git
    cd suspect_tracking_system
    ```

2. **Install the required dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```
    If a `requirements.txt` is not available, install the packages manually:
    ```bash
    pip install torch ultralytics opencv-python deep_sort_realtime numpy
    ```

3. **Model:**
    The pre-trained `yolov8m.pt` model is included in the repository for convenience and research use. Please check [Ultralytics YOLO license](https://github.com/ultralytics/yolov8) for details.

## Usage

1. **Configure the paths:**
    Open `main.py` and modify the `input_path` and `output_path` variables to point to your source video and desired output location.

    ```python
    # --- Paths ---
    input_path = os.path.join("sample_videos", "your_video.mp4")
    output_path = os.path.join("results","output_tracking.mp4")
    ```

2. **Run the tracker:**
    Execute the main script from the terminal.

    ```bash
    python main.py
    ```

3. **Interactive Controls:**
    - The tracking video will be displayed in a window titled "Live Tracking".
    - **Click** on a person's bounding box to select them as a suspect. They will be highlighted in red, and a PiP view will appear in the top-right corner.
    - **Click** on the same suspect again, or click on the background, to deselect them.
    - Press **'q'** to stop the tracking process and close the window.

## How It Works

The system operates through the following pipeline:
1. A video frame is captured from the source file.
2. The `YOLODetector` processes the frame to detect objects, outputting bounding boxes, confidence scores, and class IDs.
3. Detections are filtered to only include persons.
4. The filtered detections are passed to the `TrackByDetection` module (which wraps DeepSORT). The tracker updates the state of existing tracks and assigns new IDs to new detections based on motion and appearance.
5. The `draw_utils` module visualizes the results by drawing colored bounding boxes and track IDs on the frame. If a suspect is selected, it draws a highlighted box and the PiP zoomed view.
6. The processed frame is written to the output video file and displayed on the screen.
7. This process repeats for every frame in the video.

## Contribution

Contributions, issues, and feature requests are welcome!  
Feel free to check [issues page](https://github.com/harshit-05/suspect_tracking_system/issues) and submit a pull request.

## License

This project is licensed under the GNU General Public License v2.0. See the [LICENSE](LICENSE) file for more details.