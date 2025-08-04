# bot/replay.py

import os
import bz2
import requests
from subprocess import run
import dropbox  # ✅ Dropbox SDK for upload

DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")

def build_replay_url(match_id: int, cluster: int, salt: int) -> str:
    """
    Construct the Valve CDN URL for a .dem.bz2 replay file.
    """
    return f"http://replay{cluster}.valve.net/570/{match_id}_{salt}.dem.bz2"

def download_replay(url: str, save_path: str) -> bool:
    """
    Download the .dem.bz2 replay file from Valve's servers.
    """
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"❌ Replay download failed: {e}")
        return False

def decompress_bz2(src: str, dest: str):
    """
    Decompress a .bz2 file into raw .dem format.
    """
    try:
        with bz2.open(src, 'rb') as f_in, open(dest, 'wb') as f_out:
            f_out.write(f_in.read())
    except Exception as e:
        print(f"❌ BZ2 decompression failed: {e}")

def extract_clip_segment(dem_path: str, timestamp: int, out_path: str) -> bool:
    """
    Use Clarity to extract a 15s replay segment starting at the given timestamp (in seconds).
    """
    ticks = timestamp * 30  # Approx 30 ticks/sec
    result = run([
        "java", "-jar", "clarity.jar",
        "--in", dem_path,
        "--clip", str(ticks), "15",
        "--out", out_path
    ])
    return result.returncode == 0

def render_clip_to_video(dem_clip_path: str, out_mp4: str) -> bool:
    """
    Convert clipped .dem to an .mp4 video using ffmpeg.
    """
    result = run([
        "ffmpeg", "-i", dem_clip_path,
        "-preset", "ultrafast",
        out_mp4
    ])
    return result.returncode == 0

def upload_clip(path: str) -> str:
    """
    Upload the final .mp4 to Dropbox and return a direct shareable link.
    """
    if not DROPBOX_TOKEN:
        print("❌ No Dropbox token found in environment.")
        return ""

    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    filename = os.path.basename(path)
    dest_path = f"/guildbot-clips/{filename}"

    try:
        with open(path, "rb") as f:
            dbx.files_upload(f.read(), dest_path, mode=dropbox.files.WriteMode.overwrite)

        shared = dbx.sharing_create_shared_link_with_settings(dest_path)
        # Return a direct video streamable link
        return shared.url.replace("?dl=0", "?raw=1")

    except Exception as e:
        print(f"❌ Dropbox upload failed: {e}")
        return ""
