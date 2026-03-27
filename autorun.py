import os
import sys
import ast
import subprocess

def extract_scenes(file_path):
    """Parses the Python file to extract all classes that inherit from Scene."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    
    scenes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if it inherits from Scene (or anything ending with 'Scene')
            for base in node.bases:
                if isinstance(base, ast.Name) and "Scene" in base.id:
                    scenes.append(node.name)
                    break
    return scenes

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python autorun.py <manim_script.py>")
        sys.exit(1)

    script_file = sys.argv[1]
    
    if not os.path.exists(script_file):
        print(f"❌ Error: File '{script_file}' not found.")
        sys.exit(1)

    print(f"[*] Parsing '{script_file}' for scenes...")
    scenes = extract_scenes(script_file)
    
    if not scenes:
        print("❌ No Manim scenes found in the file.")
        sys.exit(1)
        
    print(f"[*] Found {len(scenes)} scenes to sequence: {', '.join(scenes)}\n")
    
    # Manim CLI settings
    quality_flag = "-qh" # High quality 1080p60
    resolution_folder = "1080p60" 
    script_base = os.path.splitext(os.path.basename(script_file))[0]
    completed_videos = []
    
    # Process each scene sequentially
    for scene in scenes:
        print(f"==================================================")
        print(f"🎥 RENDERING SCENE: {scene}")
        print(f"==================================================")
        
        cmd = ["manim", quality_flag, script_file, scene]
        result = subprocess.run(cmd)
        
        if result.returncode != 0:
            print(f"[!] Warning: Render failed for {scene}")
            continue
            
        video_path = f"media/videos/{script_base}/{resolution_folder}/{scene}.mp4"
        if os.path.exists(video_path):
            completed_videos.append(video_path)
        else:
            print(f"[!] Warning: Output video missing at expected path: {video_path}")

    if not completed_videos:
        print("\n❌ No videos were successfully generated.")
        sys.exit(1)
        
    print("\n[*] Stitching all scenes together into a final sequence...")
    list_file = "manim_concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for video in completed_videos:
            f.write(f"file '{video}'\n")
            
    # Auto-generate a unique output name in the media folder
    output_dir = "media"
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = f"{script_base}_full_render"
    final_output = os.path.join(output_dir, f"{base_name}.mp4")
    counter = 1
    
    while os.path.exists(final_output):
        final_output = os.path.join(output_dir, f"{base_name}_{counter}.mp4")
        counter += 1
    
    # Fast concatenation of rendered mp4s using FFmpeg copy
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c", "copy", final_output, "-loglevel", "error"
    ]
    
    if subprocess.run(ffmpeg_cmd).returncode == 0:
        print(f"\n✅ SUCCESS! All scenes encoded and merged into: {final_output}")
    else:
        print(f"\n❌ Failed to merge the intermediate videos.")
        
    if os.path.exists(list_file):
        os.remove(list_file)
