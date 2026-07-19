import  cv2
import os
import glob
import natsort

#----config----------
#path to dataset
image_folder = '/home/harshit/MOT20Det/train/MOT20-05/img1'
#output folder
output_folder = '/home/harshit/cctv_tracking_system/sample_videos'
os.makedirs(output_folder, exist_ok = True)
# output filename
video_name = 'mot20-05sample.mp4'
output_video_path = os.path.join(output_folder, video_name)
#fps for the mot datadet
fps = 25
#---------------------------

images = glob.glob(os.path.join(image_folder, '*.jpg'))
if not images:
    print(f"No .jpg images found in folder: {image_folder}")
    exit()

#using natsort to seq the frames
images = natsort.natsorted(images)

#snippet to read dimensions of the frame jpg
frame = cv2.imread(images[0])
height, width, layers = frame.shape
frame_size = (width, height)

# Init the videoWriter object
#using 'mp4v' fourcc for MP$ files
fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
out = cv2.VideoWriter(video_name, fourcc, fps, frame_size)

print(f"Starting video creation...")
print(f"Total frames to process: {len(images)}")


# Loop through all the images and write them to the video file
for i, image_path in enumerate(images):
    frame = cv2.imread(image_path)
    out.write(frame)
    # Optional: Print progress
    if (i + 1) % 100 == 0:
        print(f"Processed {i+1}/{len(images)} frames")

# Release the VideoWriter and clean up
out.release()
print(f"\nVideo creation complete! File saved as: {video_name}")
