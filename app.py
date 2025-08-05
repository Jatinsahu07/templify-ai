import streamlit as st
import os
import json
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx, CompositeVideoClip
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
import tempfile
import shutil
import urllib.parse
import random

# Helper: Scene detection using scenedetect
def detect_scenes(video_path):
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector())
    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list()
    scenes = [(start.get_seconds(), end.get_seconds()) for start, end in scene_list]
    return scenes

# Enhanced Filters/Effects/Transitions
FILTERS = ['Sepia', 'B&W', 'Vibrance', 'Cool Tone', 'Warm Glow', 'Retro', 'Cinematic', 'HDR', 'Polaroid', 'Sketch', 'Neon', 'Grayscale', 'Invert']
EFFECTS = ['Zoom', 'Shake', 'Glow', 'Blur', 'Tilt', 'Spin', 'Mirror', 'Strobe', 'Ripple', 'Distort', 'Bounce']
TRANSITIONS = ['Fade', 'Slide', 'Wipe', 'Zoom Out', 'Crossfade', 'Flash', 'Split Reveal', 'Flip', 'Zoom In', 'Roll']

def generate_template(scenes):
    template = []
    for i, (start, end) in enumerate(scenes):
        template.append({
            'segment': i + 1,
            'start': start,
            'end': end,
            'filter': random.choice(FILTERS),
            'effect': random.choice(EFFECTS),
            'transition': random.choice(TRANSITIONS)
        })
    return template

# Converter: Generic -> CapCut JSON Format
def convert_to_capcut(template):
    capcut = {
        "tracks": [
            {
                "type": "video",
                "segments": [
                    {
                        "start_time": t["start"],
                        "end_time": t["end"],
                        "filters": [t["filter"].lower()],
                        "effects": [t["effect"].lower()],
                        "transitions": [t["transition"].lower()]
                    } for t in template
                ]
            }
        ]
    }
    return capcut

# Converter: Generic -> VN Project Format
def convert_to_vn(template):
    vn = {
        "project": {
            "scenes": [
                {
                    "start_time": t["start"],
                    "end_time": t["end"],
                    "filter": t["filter"],
                    "effect": t["effect"],
                    "transition": t["transition"]
                } for t in template
            ]
        }
    }
    return vn

# Generate CapCut QR-style Template Link (for visual demo)
def generate_capcut_link(template):
    encoded_json = urllib.parse.quote(json.dumps(template))
    return f"https://www.capcut.com/template-share?data={encoded_json}"

# Apply visual effects (basic simulation)
def apply_filter(clip, filter_name):
    if filter_name == 'B&W':
        return clip.fx(vfx.blackwhite)
    elif filter_name == 'Sepia':
        return clip.fx(vfx.colorx, 1.3)
    elif filter_name == 'Vibrance':
        return clip.fx(vfx.colorx, 1.5)
    elif filter_name == 'Cool Tone':
        return clip.fx(vfx.lum_contrast, 0, 30, 0)
    elif filter_name == 'Warm Glow':
        return clip.fx(vfx.lum_contrast, 0, -30, 0)
    elif filter_name == 'Retro':
        return clip.fx(vfx.colorx, 0.8)
    elif filter_name == 'HDR':
        return clip.fx(vfx.lum_contrast, 20, 50, 10)
    elif filter_name == 'Polaroid':
        return clip.fx(vfx.colorx, 1.1)
    elif filter_name == 'Sketch':
        return clip.fx(vfx.lum_contrast, 40, 60, 20)
    elif filter_name == 'Neon':
        return clip.fx(vfx.lum_contrast, 60, 20, 30)
    elif filter_name == 'Grayscale':
        return clip.fx(vfx.blackwhite)
    elif filter_name == 'Invert':
        try:
            return clip.fx(vfx.invert_colors)
        except AttributeError:
            return clip  # Fallback if invert not available
    else:
        return clip

# Apply transition between two clips (visual simulation)
def apply_transition(clip1, clip2, transition_type, duration=1):
    if transition_type == 'Crossfade':
        return clip1.crossfadeout(duration).set_end(clip1.duration).fx(lambda c: c.set_opacity(0.8)).set_start(0).crossfadein(duration).set_end(clip1.duration + duration) + clip2.crossfadein(duration)
    elif transition_type == 'Fade':
        return concatenate_videoclips([clip1.fadeout(duration), clip2.fadein(duration)])
    else:
        return concatenate_videoclips([clip1, clip2])

# Streamlit App

st.title("🎬 Templify")
uploaded_file = st.file_uploader("Upload a video", type=["mp4", "mov"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.video(tmp_path)

    with st.spinner("Detecting scenes..."):
        scenes = detect_scenes(tmp_path)
        st.success(f"Detected {len(scenes)} scenes")

    template = generate_template(scenes)
    st.subheader("🧩 Detected Segments + Effects")
    st.json(template)

    # Drag-and-Drop Timeline Editor
    st.subheader("📊 Timeline Editor")
    edited_template = []
    for i, seg in enumerate(template):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            start = st.number_input(f"Start {seg['segment']}", value=float(seg['start']), key=f"start_{i}")
        with col2:
            end = st.number_input(f"End {seg['segment']}", value=float(seg['end']), key=f"end_{i}")
        with col3:
            filter_choice = st.selectbox("Filter", FILTERS, index=FILTERS.index(seg['filter']), key=f"filter_{i}")
        with col4:
            effect_choice = st.selectbox("Effect", EFFECTS, index=EFFECTS.index(seg['effect']), key=f"effect_{i}")
        transition_choice = st.selectbox("Transition", TRANSITIONS, index=TRANSITIONS.index(seg['transition']), key=f"trans_{i}")

        edited_template.append({
            'segment': i + 1,
            'start': start,
            'end': end,
            'filter': filter_choice,
            'effect': effect_choice,
            'transition': transition_choice
        })

    # Visual Previews of Segments
    st.subheader("🎞️ Segment Previews")
    for i, seg in enumerate(edited_template):
        st.markdown(f"**Segment {seg['segment']}** | ⏱️ {seg['start']:.2f}s to {seg['end']:.2f}s | 🎨 {seg['filter']} + ✨ {seg['effect']}")
        with VideoFileClip(tmp_path).subclip(seg['start'], seg['end']) as clip:
            styled_clip = apply_filter(clip, seg['filter'])
            preview_path = os.path.join(tempfile.gettempdir(), f"styled_segment_{i+1}.mp4")
            styled_clip.write_videofile(preview_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            st.video(preview_path)
            styled_clip.close()

    # Export Options
    export_format = st.selectbox("Export Template As", ["Generic JSON", "CapCut JSON", "VN Project"])
    if export_format:
        if export_format == "Generic JSON":
            export_data = edited_template
            file_name = "video_template.json"
        elif export_format == "CapCut JSON":
            export_data = convert_to_capcut(edited_template)
            file_name = "capcut_template.json"
        else:
            export_data = convert_to_vn(edited_template)
            file_name = "vn_template.json"

        json_str = json.dumps(export_data, indent=2)
        st.download_button("📥 Download Template", json_str, file_name=file_name, mime="application/json")

        if export_format == "CapCut JSON":
            capcut_url = generate_capcut_link(export_data)
            st.markdown(f"[🎬 Click to Open in CapCut]({capcut_url})")

    # Export full edited video
    if st.button("📤 Export Full Edited Video"):
        with st.spinner("Rendering final video with transitions..."):
            clips = []
            for seg in edited_template:
                with VideoFileClip(tmp_path).subclip(seg['start'], seg['end']) as clip:
                    styled_clip = apply_filter(clip, seg['filter'])
                    clips.append(styled_clip)

            final_clip = clips[0]
            for i in range(1, len(clips)):
                final_clip = apply_transition(final_clip, clips[i], edited_template[i]['transition'])

            output_path = os.path.join(tempfile.gettempdir(), "final_output.mp4")
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button("📥 Download Full Video", f.read(), file_name="edited_video.mp4", mime="video/mp4")
            final_clip.close()

    # Cleanup
    try:
        uploaded_file.close()
        os.remove(tmp_path)
    except PermissionError:
        st.warning("⚠️ Temporary file is still in use and could not be deleted.")
        
        
        # Divider
st.markdown("---")
st.subheader("🧩 Upload Your Custom Template")

custom_template_file = st.file_uploader("📤 Upload Custom Template (.json)", type=["json"], key="custom_template")

if custom_template_file is not None:
    try:
        custom_template = json.load(custom_template_file)
        st.success(f"✅ Custom template '{custom_template.get('template_name', 'Untitled')}' loaded!")

        # Display Effects
        st.markdown("### 🎯 Effects")
        for e in custom_template.get("effects", []):
            st.write(f"⏱ {e['time']} → ✨ `{e['effect']}`")

        # Display Filters
        st.markdown("### 🎨 Filters")
        for f in custom_template.get("filters", []):
            st.write(f"⏱ {f['time']} → 🎨 `{f['filter']}`")

        # Display Transitions
        st.markdown("### 🔀 Transitions")
        for t in custom_template.get("transitions", []):
            st.write(f"⏱ {t['time']} → 🔀 `{t['transition']}`")

        # Placeholder for future logic
        if st.button("📌 Apply This Template"):
            st.info("🚧 Applying this template to the video will be supported in the next version.")

    except Exception as e:
        st.error(f"❌ Failed to load template: {e}")

