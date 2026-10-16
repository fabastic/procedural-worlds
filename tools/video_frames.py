"""Contact sheet of frames from a rendered MP4, decoded with Blender's sequencer (no ffmpeg needed).
    blender -b --factory-startup -P tools/video_frames.py -- VIDEO.mp4 OUT.png [f1,f2,...]"""
import sys, os
import bpy
import numpy as np
args = sys.argv[sys.argv.index("--") + 1:]
mp4, out = args[0], args[1]
frames = [int(x) for x in (args[2] if len(args) > 2 else "1,2,3,24,48").split(",")]
s = bpy.context.scene
s.sequence_editor_create()
strip = s.sequence_editor.strips.new_movie("v", mp4, channel=1, frame_start=1)
clip = bpy.data.movieclips.load(mp4)
w, h = clip.size[:]
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = w, h, 100
s.render.image_settings.media_type = "IMAGE"
s.render.image_settings.file_format = "PNG"
s.view_settings.view_transform = "Standard"
tmp = os.path.join(os.path.dirname(out), "_vf.png")
cols = min(3, len(frames))
rows = (len(frames) + cols - 1) // cols
sheet = np.ones((h * rows, w * cols, 4), dtype=np.float32)
for i, f in enumerate(frames):
    s.frame_set(f)
    s.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(tmp)
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    r, c = divmod(i, cols)
    y0 = (rows - 1 - r) * h
    sheet[y0:y0 + h, c * w:(c + 1) * w] = px
    bpy.data.images.remove(im)
os.remove(tmp)
img = bpy.data.images.new("sheet", sheet.shape[1], sheet.shape[0])
img.pixels = sheet.ravel()
img.filepath_raw, img.file_format = out, "PNG"
img.save()
print("FRAMES", out, strip.frame_final_duration)
