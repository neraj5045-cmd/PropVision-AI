# PropVision AI — Cinematic Real Estate Property Film Generator

PropVision AI turns property details and 4–8 home photos into a branded MP4 property showcase.

## Video style
The generated film follows a premium real-estate showcase style:
1. PropVision AI campaign opening artwork.
2. Full-screen property photographs with subtle cinematic zoom.
3. Dark translucent lower-third information panels, gold accent lines, scene labels and clear headings.
4. Smooth fades between each property scene.
5. Branded enquiry end card with property name, location, price and call to action.
6. Optional Indian-English neural voice-over.

## Features
- Streamlit interface for listing name, location, price, property type, features, contact text and brand.
- Four built-in luxury demo home photographs, plus support for uploading 4–8 JPG/PNG photos.
- Template-based narration script grounded in the listing details entered by the user.
- Indian English neural female voice (Neerja) or male voice (Prabhat).
- MP4 preview and download.

## Technology
- Python 3.10+
- Streamlit — application interface
- Pillow — image processing, typography and overlays
- imageio-ffmpeg / FFmpeg — MP4 encoding and audio/video muxing
- edge-tts — neural text-to-speech (internet required)

## Setup on Windows PowerShell
Open the `propvision_ai` project folder in VS Code, then run:
```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Open the local URL shown in the terminal (usually http://localhost:8501).

## Demo details
The built-in demo defaults are illustrative: Emerald Heights Penthouse, Prime Location, ₹2.85 Cr. Update these values before using the application for a real property. The supplied photos are demonstration visuals and should not be represented as verified images of a specific property.

## Project structure
```text
propvision_ai/
├── app.py
├── requirements.txt
├── README.md
├── sample_data.json
├── .gitignore
├── sample_assets/
│   ├── propvision_premium_intro.png
│   ├── property_1.jpg
│   ├── property_2.jpg
│   ├── property_3.jpg
│   └── property_4.jpg
└── sample_output/
```

## Notes
- Neural narration requires an internet connection.
- Script generation is template-based; no LLM API key is required.
- Use only photos and other media that you have permission to use.
