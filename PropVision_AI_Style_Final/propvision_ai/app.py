import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io, os, tempfile, subprocess, asyncio, shutil
import imageio_ffmpeg
import edge_tts

st.set_page_config(page_title="PropVision AI", page_icon="🏡", layout="wide")

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(ROOT, "sample_assets")
INTRO_PATH = os.path.join(ASSET_DIR, "propvision_premium_intro.png")

# ---------- Listing copy: use only facts entered in the form ----------
def build_copy(name, location, price, ptype, features, contact):
    name = name.strip() or "Your New Property"
    location = location.strip() or "a prime location"
    price = price.strip() or "Price on request"
    ptype = ptype or "residence"
    clean_features = [x.strip() for x in features if x.strip()]
    feature_text = ", ".join(clean_features[:4]) if clean_features else "thoughtfully planned living spaces"
    contact = contact.strip() or "contact our team to arrange a private viewing"
    script = (
        f"Welcome to {name}, an exceptional {ptype.lower()} in {location}. "
        f"Offered at {price}, this property brings together comfort, thoughtful design and elegant spaces. "
        f"Highlights include {feature_text}. "
        f"Discover a home designed around the way you want to live. "
        f"For more information or to arrange a private viewing, {contact}."
    )
    return script

# ---------- Fonts and image helpers ----------
def load_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/georgiab.ttf" if bold else "C:/Windows/Fonts/georgia.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def cover_crop(image, size):
    image = image.convert("RGB")
    tw, th = size
    ratio = max(tw / image.width, th / image.height)
    nw, nh = int(image.width * ratio), int(image.height * ratio)
    image = image.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return image.crop((left, top, left + tw, top + th))

def wrap_lines(draw, text, font, max_width):
    words = str(text).split()
    lines, line = [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def draw_wrapped(draw, xy, text, font, fill, max_width, max_lines=2, gap=5):
    x, y = xy
    lines = wrap_lines(draw, text, font, max_width)[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + gap
    return y

def ken_burns(image, progress, size=(1280, 720)):
    base = cover_crop(image, size)
    zoom = 1.0 + 0.045 * progress
    nw, nh = int(size[0] * zoom), int(size[1] * zoom)
    enlarged = base.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw-size[0])//2, (nh-size[1])//2
    return enlarged.crop((left, top, left+size[0], top+size[1]))

# ---------- Cinematic property-film scenes ----------
def make_scene_frame(photo, title, subtitle, brand, scene_no, total, progress, size=(1280,720)):
    img = ken_burns(photo, progress, size).convert("RGBA")
    w, h = size
    # Gentle full-frame tint plus cinematic lower gradient.
    tint = Image.new("RGBA", size, (5, 12, 22, 18))
    img = Image.alpha_composite(img, tint)
    gradient = Image.new("RGBA", size, (0,0,0,0))
    gd = ImageDraw.Draw(gradient)
    for y in range(350, h):
        a = int(18 + 120 * ((y-350)/(h-350))**1.35)
        gd.line((0,y,w,y), fill=(4,9,17,a))
    img = Image.alpha_composite(img, gradient)
    d = ImageDraw.Draw(img)

    # Small restrained brand mark in the upper-left.
    d.rounded_rectangle((48,36,365,88), radius=9, fill=(7,15,28,188), outline=(211,174,99,150), width=1)
    d.text((68,51), str(brand).upper()[:26], font=load_font(19, True), fill=(250,248,241,255))
    d.text((1050,54), f"PROPERTY FILM   {scene_no:02d} / {total:02d}",
           font=load_font(14, True), fill=(255,250,238,230))

    # Reference-inspired lower-third: gold hairline, translucent navy panel, label and title.
    panel_top = 490
    d.rounded_rectangle((62,panel_top,1218,676), radius=15, fill=(7,13,25,218),
                        outline=(206,169,98,155), width=1)
    d.rectangle((62,panel_top,1218,panel_top+5), fill=(215,178,104,255))
    d.rounded_rectangle((88,516,240,550), radius=5, fill=(214,174,73,255))
    d.text((101,524), "PROPERTY DETAIL", font=load_font(13, True), fill=(22,25,30,255))
    draw_wrapped(d, (88,565), title, load_font(34, True), (255,255,255,255), 1060, 1, 2)
    draw_wrapped(d, (90,615), subtitle, load_font(19), (222,228,236,255), 1060, 1, 2)

    # Fine progress line at the very bottom.
    d.rounded_rectangle((62,696,1218,702), radius=3, fill=(255,255,255,75))
    d.rounded_rectangle((62,696,62+int(1156*progress),702), radius=3, fill=(222,184,104,255))
    return img.convert("RGB")

def make_intro_frames(poster, fps=24, seconds=3):
    poster_frame = cover_crop(poster, (1280,720))
    count = max(1, int(fps*seconds))
    frames = []
    for i in range(count):
        # Very gentle push-in on the campaign artwork.
        frames.append(ken_burns(poster_frame, (i+1)/count*0.35, (1280,720)))
    return frames

def make_outro_frame(name, location, price, brand, progress):
    w, h = 1280, 720
    img = Image.new("RGB", (w,h), (7,15,28))
    d = ImageDraw.Draw(img)
    for y in range(h):
        shade = int(7 + 10*y/h)
        d.line((0,y,w,y), fill=(shade, 17+shade//2, 31+shade//2))
    d.rectangle((30,30,w-30,h-30), outline=(207,171,101), width=3)
    d.text((78,72), str(brand).upper()[:30], font=load_font(24,True), fill=(235,205,145))
    d.text((80,185), "BOOK A PRIVATE VIEWING", font=load_font(18,True), fill=(219,180,105))
    draw_wrapped(d, (76,245), name, load_font(49,True), (255,255,255), 1080, 2, 5)
    d.text((82,385), location[:75], font=load_font(25), fill=(220,226,235))
    d.text((82,445), f"Offered at {price}", font=load_font(32,True), fill=(239,205,132))
    d.rounded_rectangle((82,535,520,605), radius=12, fill=(213,174,91))
    d.text((111,555), "ENQUIRE NOW  ›", font=load_font(24,True), fill=(14,22,34))
    d.text((82,650), "LUXURY HOMES  |  PRIME LOCATIONS  |  SMART LIVING",
           font=load_font(15,True), fill=(185,194,205))
    d.rounded_rectangle((62,690,1218,697), radius=3, fill=(255,255,255,65))
    d.rounded_rectangle((62,690,62+int(1156*progress),697), radius=3, fill=(222,184,104))
    return img

def render_video(images, scene_texts, brand, output_path, intro_image=None,
                 property_name="", location="", price="", seconds_per_scene=5.0, fps=15):
    w, h = 1280, 720
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg, "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-s", f"{w}x{h}",
           "-pix_fmt", "rgb24", "-r", str(fps), "-i", "-", "-an", "-vcodec", "libx264",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", output_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    previous = None
    fade_frames = max(1, int(0.45*fps))

    def write_segment(frame_iter):
        nonlocal previous
        first = True
        for frame in frame_iter:
            if first and previous is not None:
                # Fade from the outgoing shot into the incoming shot.
                for k in range(fade_frames):
                    alpha = (k+1)/(fade_frames+1)
                    proc.stdin.write(Image.blend(previous, frame, alpha).tobytes())
                first = False
                proc.stdin.write(frame.tobytes())
            else:
                first = False
                proc.stdin.write(frame.tobytes())
            previous = frame

    try:
        if intro_image is not None:
            n = int(3.0*fps)
            write_segment(ken_burns(intro_image, (i+1)/n*0.35, (w,h)) for i in range(n))

        scene_n = max(1, int(seconds_per_scene*fps))
        total = len(images)
        for i, (image, pair) in enumerate(zip(images, scene_texts)):
            title, subtitle = pair
            def scene_frames():
                for f in range(scene_n):
                    progress = (i + (f+1)/scene_n) / max(1,total)
                    yield make_scene_frame(image, title, subtitle, brand, i+1, total,
                                           progress, (w,h))
            write_segment(scene_frames())

        outro_n = int(3.5*fps)
        write_segment(make_outro_frame(property_name, location, price, brand, (i+1)/outro_n)
                      for i in range(outro_n))

        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", errors="ignore")
        code = proc.wait()
        if code != 0:
            raise RuntimeError(err[-1800:])
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
        raise

def add_voiceover(video_path, audio_path, final_path):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg, "-y", "-i", video_path, "-i", audio_path,
           "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
           "-c:a", "aac", "-b:a", "192k", "-af", "apad",
           "-shortest", "-movflags", "+faststart", final_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("Audio/video merge failed: " + result.stderr[-1600:])

# ---------- Streamlit interface ----------
st.markdown("""
<style>
.stApp {background:#0b1019;color:#f5f6f8;}
.block-container {padding-top:1.6rem;max-width:1320px;}
.hero {padding:26px 32px;border-radius:18px;background:linear-gradient(110deg,#081323,#17334a);border:1px solid #b9924c;color:white;margin-bottom:20px;}
.hero h1 {font-size:2.25rem;margin:0 0 7px 0;}
.hero p {color:#d6deea;margin:0;font-size:1rem;}
div[data-testid="stButton"] button {background:#cda65f;color:#111827;border:0;font-weight:700;}
.small-note {color:#aeb8c7;font-size:.9rem;}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🏡 PropVision AI</h1><p>Luxury property films with cinematic visuals, editorial titles and professional narration.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Create a property film")
    st.markdown("1. Enter verified listing details\n2. Use the demo home gallery or upload 4–8 photos\n3. Choose a neural voice\n4. Generate and download your MP4")
    st.caption("Demo photos are illustrative. Enter only verified facts for a real listing.")

left, right = st.columns([1.05, .95], gap="large")
with left:
    st.subheader("1 · Property information")
    with st.form("property_form"):
        name = st.text_input("Property name", "Emerald Heights Penthouse")
        location = st.text_input("Location", "Prime Location")
        price = st.text_input("Price", "₹2.85 Cr")
        ptype = st.selectbox("Property type", ["Luxury Villa", "Penthouse", "Apartment", "Independent House", "Studio", "Commercial"])
        feature_text = st.text_area("Key features (one per line)",
                                    "4 BHK luxury residence\nPrivate swimming pool\nSpacious living room\nModern kitchen and terrace")
        contact = st.text_input("Call to action / contact", "Enquire now to schedule a private viewing")
        brand = st.text_input("Brand / agent name", "PROPvision REALTY")
        submitted = st.form_submit_button("Generate script & preview", type="primary", use_container_width=True)
    features = [x.strip() for x in feature_text.splitlines() if x.strip()]
    script = build_copy(name, location, price, ptype, features, contact)
    if submitted:
        st.session_state["copy_ready"] = True
    if st.session_state.get("copy_ready"):
        st.success("Promotional narration is ready.")
        st.markdown("**Suggested voice-over script**")
        st.write(script)

with right:
    st.subheader("2 · Property photos")
    uploads = st.file_uploader("Upload 4–8 property images", type=["jpg","jpeg","png"], accept_multiple_files=True)
    demo = st.checkbox("Use built-in luxury demo photos", value=(not uploads))
    if demo:
        images = []
        for i in range(1,5):
            p = os.path.join(ASSET_DIR, f"property_{i}.jpg")
            if os.path.exists(p):
                images.append(Image.open(p).convert("RGB"))
        poster = Image.open(INTRO_PATH).convert("RGB") if os.path.exists(INTRO_PATH) else None
        st.caption("Film order: PropVision campaign opening → four luxury property scenes → enquiry end card.")
        if poster is not None:
            st.image(poster, caption="Opening campaign artwork", use_container_width=True)
    else:
        images, poster = [], None
        for file in uploads or []:
            try:
                images.append(Image.open(io.BytesIO(file.getvalue())).convert("RGB"))
            except Exception:
                st.warning(f"Could not read {file.name}; please upload JPG or PNG.")
    if images:
        cols = st.columns(2)
        for i, im in enumerate(images[:8]):
            cols[i%2].image(im, caption=f"Property scene {i+1}", use_container_width=True)

st.divider()
st.subheader("3 · Voice and video")
voiceover = st.checkbox("Add professional neural voice-over", value=True)
voice_choice = st.selectbox("Narration voice",
    ["Indian English · Female (Neerja)", "Indian English · Male (Prabhat)"])
voice_name = "en-IN-NeerjaNeural" if voice_choice.startswith("Indian English · Female") else "en-IN-PrabhatNeural"
pace = st.select_slider("Speaking pace", options=["Slow","Natural","Confident"], value="Natural")
rate = {"Slow":"-8%","Natural":"+0%","Confident":"+5%"}[pace]
st.caption("Neural narration requires an internet connection.")
if st.button("✨ Create professional property film", type="primary", use_container_width=True):
    if not name.strip() or not location.strip():
        st.error("Please enter a property name and location.")
    elif len(images) < 4:
        st.error("Please add at least four property images.")
    else:
        # Purpose-written scene headings, following the visual sequence in the reference video.
        fallback_titles = [
            "Contemporary Luxury Exterior",
            "Modern Villa Architecture",
            "Spacious Living with Natural Light",
            "Private Pool and Outdoor Living",
            "Elegant Property Details",
            "Designed for Modern Living",
            "A Refined Place to Call Home",
            "Discover Your Next Address"
        ]
        scene_texts = []
        for i in range(len(images[:8])):
            title = fallback_titles[i] if i < len(fallback_titles) else "A Place to Call Home"
            subtitle = f"{location}  |  {price}"
            scene_texts.append((title, subtitle))
        # Use real feature text in the scene subtitles where available.
        for i, feature in enumerate(features[:len(scene_texts)]):
            if i < len(scene_texts):
                scene_texts[i] = (scene_texts[i][0], feature)
        with st.spinner("Rendering cinematic scenes and preparing narration…"):
            try:
                silent = os.path.join(tempfile.gettempdir(), "propvision_film_silent.mp4")
                final = os.path.join(tempfile.gettempdir(), "propvision_property_film.mp4")
                render_video(images[:8], scene_texts, brand or "PROPvision REALTY", silent,
                             intro_image=poster, property_name=name, location=location, price=price,
                             seconds_per_scene=5.0, fps=15)
                if voiceover:
                    audio = os.path.join(tempfile.gettempdir(), "propvision_neural_voice.mp3")
                    async def make_voice():
                        tts = edge_tts.Communicate(script, voice_name, rate=rate, pitch="+0Hz")
                        await tts.save(audio)
                    asyncio.run(make_voice())
                    add_voiceover(silent, audio, final)
                else:
                    shutil.copyfile(silent, final)
                with open(final,"rb") as f:
                    st.session_state["video_bytes"] = f.read()
                st.session_state["video_name"] = (name.strip().replace(" ","_") or "property") + "_property_film.mp4"
            except Exception as e:
                st.error(f"Video generation failed: {e}")
if st.session_state.get("video_bytes"):
    st.success("Your property film is ready.")
    st.video(st.session_state["video_bytes"])
    st.download_button("⬇ Download MP4", st.session_state["video_bytes"],
                       file_name=st.session_state["video_name"], mime="video/mp4",
                       use_container_width=True)

st.caption("Visuals are illustrative demo images; property information and pricing come from the form. Neural voice-over requires internet.")
