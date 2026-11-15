#!/usr/bin/env python3
"""Put finished videos into the YouTube publish queue (branch `publish-queue`).

Usage:
  python tools/queue_for_youtube.py <slug> <manifest.json> [--push]

<manifest.json> follows the format in tools/youtube_publish.py; every "file" and
"thumbnail" path in it is resolved relative to the manifest's own folder.
Videos are split into 45 MB parts (GitHub rejects files > 100 MB).
With --push it clones/updates publish-queue in /tmp/bo-bloop-publish-queue, commits and pushes;
the push starts the "YouTube publish" workflow, which writes queue/<slug>/done.json.
"""
import json
import os
import shutil
import subprocess
import sys

PART = 45 * 1024 * 1024
REPO = "https://github.com/SkoutStudio/bo-bloop"
WORK = "/tmp/bo-bloop-publish-queue"


def sh(*a, cwd=None):
    print("+", " ".join(a))
    subprocess.run(a, cwd=cwd, check=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    slug, man_path = args
    src = os.path.dirname(os.path.abspath(man_path))
    man = json.load(open(man_path, encoding="utf-8"))

    if not os.path.isdir(os.path.join(WORK, ".git")):
        sh("git", "clone", "--depth", "1", "--branch", "publish-queue", REPO, WORK)
    else:
        sh("git", "fetch", "--depth", "1", "origin", "publish-queue", cwd=WORK)
        sh("git", "reset", "--hard", "origin/publish-queue", cwd=WORK)

    dst = os.path.join(WORK, "queue", slug)
    if os.path.exists(os.path.join(dst, "done.json")):
        sys.exit(f"queue/{slug} was already uploaded (done.json exists). Use a new slug.")
    os.makedirs(dst, exist_ok=True)

    for v in man["videos"]:
        f = os.path.join(src, v["file"])
        name = os.path.basename(f)
        v["file"] = name
        with open(f, "rb") as r:
            i = 0
            while chunk := r.read(PART):
                open(os.path.join(dst, f"{name}.part{i:03d}"), "wb").write(chunk)
                i += 1
        print(f"{name}: {os.path.getsize(f) / 1e6:.1f} MB -> {i} part(s)")
        if v.get("thumbnail"):
            t = os.path.join(src, v["thumbnail"])
            shutil.copy(t, dst)
            v["thumbnail"] = os.path.basename(t)

    json.dump(man, open(os.path.join(dst, "manifest.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    if "--push" in sys.argv:
        sh("git", "add", "-f", f"queue/{slug}", cwd=WORK)
        sh("git", "commit", "-m", f"Queue {slug} for YouTube", cwd=WORK)
        sh("git", "push", "origin", "publish-queue", cwd=WORK)
        print(f"Pushed. Results will appear in queue/{slug}/done.json on branch publish-queue.")
    else:
        print(f"Prepared in {dst} (not pushed; add --push).")


if __name__ == "__main__":
    main()
