#!/usr/bin/env python3
"""Bo & Bloop — free YouTube publisher (copied from SkoutStudio/curious-engine) (runs inside GitHub Actions).

Modes
  check_auth                 Exchange the refresh token, print the channel it belongs to,
                             fail if it is not the expected channel.
  upload <queue_dir> [...]   Upload every video listed in <queue_dir>/manifest.json,
                             then write <queue_dir>/done.json with the new video IDs.

Environment
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN   (from GitHub Secrets)
  YT_EXPECTED_CHANNEL_ID                              (optional; manifest channel_id wins)

manifest.json
{
  "channel_id": "UCgzl9soaKTl3XNG_8ZDnVwQ",
  "videos": [
    {
      "file": "how_is_a_circuit_board_made.mp4",      # or split into .part000, .part001, ...
      "title": "...", "description": "...", "tags": ["..."],
      "publish_at": "2026-11-12T17:00:00+02:00",       # omitted -> stays private (never public)
      "thumbnail": "thumbnail.png",                    # optional
      "category_id": "27", "language": "en",
      "made_for_kids": true, "synthetic_media": true
    }
  ]
}
"""
import datetime as dt
import glob
import json
import os
import sys
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

def _exit(msg):
    # In GitHub Actions, also surface the message as an annotation on the run page.
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::error::{msg}")
    raise SystemExit(msg)


def _notice(msg):
    print(f"::notice::{msg}" if os.environ.get("GITHUB_ACTIONS") else msg)


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def youtube():
    missing = [k for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN") if not os.environ.get(k)]
    if missing:
        _exit(f"ERROR: missing GitHub secret(s): {', '.join(missing)}")
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def my_channel(yt):
    res = yt.channels().list(part="id,snippet,contentDetails", mine=True).execute()
    items = res.get("items", [])
    if not items:
        _exit("ERROR: this Google account has no YouTube channel selected. Redo step B and pick the channel.")
    return items[0]


def assert_channel(ch, expected):
    print(f"Authorized channel: {ch['snippet']['title']} ({ch['id']})")
    if expected and ch["id"] != expected:
        _exit(f"ERROR: token belongs to {ch['id']}, expected {expected}. "
                 "Redo step B and choose the correct channel.")


def check_auth():
    yt = youtube()
    ch = my_channel(yt)
    assert_channel(ch, os.environ.get("YT_EXPECTED_CHANNEL_ID"))
    _notice(f"check_auth OK: {ch['snippet']['title']} ({ch['id']})")


def existing_titles(yt, ch):
    """Titles already on the channel (incl. private/scheduled), to avoid duplicate uploads on re-runs."""
    titles, token = set(), None
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    for _ in range(10):  # last ~500 uploads is plenty
        try:
            res = yt.playlistItems().list(part="snippet", playlistId=uploads, maxResults=50, pageToken=token).execute()
        except HttpError as e:
            if e.resp.status == 404:  # empty channel: uploads playlist doesn't exist yet
                return titles
            raise
        titles.update(i["snippet"]["title"] for i in res.get("items", []))
        token = res.get("nextPageToken")
        if not token:
            break
    return titles


def assemble(queue_dir, name):
    path = os.path.join(queue_dir, name)
    if os.path.exists(path):
        return path
    parts = sorted(glob.glob(path + ".part*"))
    if not parts:
        _exit(f"ERROR: {name} not found in {queue_dir}")
    out = os.path.join("/tmp", os.path.basename(name))
    with open(out, "wb") as w:
        for p in parts:
            with open(p, "rb") as r:
                w.write(r.read())
    print(f"  assembled {name} from {len(parts)} parts ({os.path.getsize(out) / 1e6:.1f} MB)")
    return out


def to_utc(s):
    t = dt.datetime.fromisoformat(s)
    if t.tzinfo is None:
        _exit(f"ERROR: publish_at '{s}' needs a timezone, e.g. 2026-11-12T17:00:00+02:00")
    t = t.astimezone(dt.timezone.utc)
    if t <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=15):
        _exit(f"ERROR: publish_at {s} is in the past or too soon.")
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def upload_one(yt, queue_dir, v):
    status = {
        "privacyStatus": "private",
        "selfDeclaredMadeForKids": bool(v.get("made_for_kids", False)),
        "containsSyntheticMedia": bool(v.get("synthetic_media", True)),
        "embeddable": True,
    }
    if v.get("publish_at"):
        status["publishAt"] = to_utc(v["publish_at"])
    body = {
        "snippet": {
            "title": v["title"][:100],
            "description": v.get("description", "")[:5000],
            "tags": v.get("tags", []),
            "categoryId": str(v.get("category_id", "28")),
            "defaultLanguage": v.get("language", "en"),
            "defaultAudioLanguage": v.get("language", "en"),
        },
        "status": status,
    }
    path = assemble(queue_dir, v["file"])
    media = MediaFileUpload(path, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media, notifySubscribers=True)
    resp, retries = None, 0
    while resp is None:
        try:
            st, resp = req.next_chunk()
            if st:
                print(f"  {int(st.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and retries < 5:
                retries += 1
                time.sleep(2 ** retries)
                continue
            raise
    vid = resp["id"]
    print(f"  uploaded -> https://youtu.be/{vid}  (publishAt {status.get('publishAt', 'none, stays private')})")

    thumb_ok = None
    if v.get("thumbnail"):
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(os.path.join(queue_dir, v["thumbnail"]))).execute()
            thumb_ok = True
            print("  thumbnail set")
        except HttpError as e:
            thumb_ok = False
            print(f"  WARNING: thumbnail not set ({e.resp.status}). Custom thumbnails need a phone-verified channel.")
    return {"file": v["file"], "title": v["title"], "video_id": vid, "url": f"https://youtu.be/{vid}",
            "publish_at": status.get("publishAt"), "thumbnail_set": thumb_ok}


def upload(queue_dirs):
    yt = youtube()
    ch = my_channel(yt)
    for qd in queue_dirs:
        man_path = os.path.join(qd, "manifest.json")
        if not os.path.exists(man_path):
            continue
        if os.path.exists(os.path.join(qd, "done.json")):
            print(f"{qd}: already done, skipping")
            continue
        man = json.load(open(man_path, encoding="utf-8"))
        assert_channel(ch, man.get("channel_id") or os.environ.get("YT_EXPECTED_CHANNEL_ID"))
        have = existing_titles(yt, ch)
        results = []
        for v in man["videos"]:
            print(f"- {v['title']}")
            if v["title"][:100] in have:
                print("  already on the channel, skipping")
                results.append({"file": v["file"], "title": v["title"], "skipped": "duplicate title"})
                continue
            results.append(upload_one(yt, qd, v))
        json.dump({"uploaded_at": dt.datetime.now(dt.timezone.utc).isoformat(), "channel_id": ch["id"],
                   "results": results}, open(os.path.join(qd, "done.json"), "w", encoding="utf-8"), indent=2)
        print(f"{qd}: done")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("check_auth", "upload"):
        sys.exit(__doc__)
    try:
        if sys.argv[1] == "check_auth":
            check_auth()
        else:
            upload(sys.argv[2:])
    except HttpError as e:
        _exit(f"YouTube API error {e.resp.status}: {e.content.decode(errors='ignore')[:800]}")
    except Exception as e:  # refresh-token problems surface here (RefreshError)
        if "invalid_grant" in str(e):
            _exit("ERROR: refresh token rejected (invalid_grant). If the OAuth app is still in 'Testing', "
                     "publish it (step A4) and create a new token (step B).")
        raise
