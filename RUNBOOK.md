# Bo & Bloop — weekly automated run

This repo is the whole production system for the YouTube channel **Bo & Bloop** (English, kids 4-7, "Made for kids").
Owner: Johnny (Skout Studio). A scheduled task runs this **Monday, Wednesday and Friday around 03:00 (Europe/Athens)**.
Each run makes **1 episode + 3 Shorts** (so 3 episodes + 9 Shorts a week), schedules them in Metricool, and notifies Johnny.

## Calendar (Europe/Athens). D = the day the run starts (after midnight)
| Run day | Episode (15:00) | Short 1 | Short 2 | Short 3 |
| --- | --- | --- | --- | --- |
| Monday | Tuesday | Wednesday 12:00 | Thursday 19:00 | Friday 12:00 |
| Wednesday | Thursday | Friday 19:00 | Saturday 12:00 | Sunday 19:00 |
| Friday | Saturday | Sunday 12:00 | Monday 19:00 | Tuesday 12:00 |

The 9 Shorts slots never collide. Example: run on Fri 13 Nov 2026 -> episode Sat 14 Nov 15:00, Shorts Sun 15 12:00,
Mon 16 19:00, Tue 17 12:00. Before scheduling, `getScheduledPosts` for those days: if a Bo & Bloop YouTube post already
sits in a slot (e.g. a manual run happened), do NOT double-book: stop and tell Johnny.
If a run was missed, the next run only does its own slots (never schedule in the past).

## Steps for the run
1. **Setup**: `bash setup.sh` (installs piper-tts, cairosvg, numpy, pillow; downloads voices into `voices/`). ffmpeg must exist.
2. **Pick the episode**: first line with status `next` in `plan/episodes.md`. Its end card teases the following `queued` line.
   If none is `next`, take the first `queued`. Write 6-9 new `queued` ideas when fewer than 6 remain (rotate the 5 series; never repeat a lesson already in the table).
3. **Make the folder**: copy the closest previous episode folder (`episodes/epNN`) to the new number. Counting episodes start
   from ep02 (starfish + coral bed), others from the nearest match.
4. **Script** (`script.py`): same 7-part structure (hook question -> jingle -> problem/mistake by Bo -> trying together with
   pauses for kids -> solution + lesson said 2-3 times -> song -> outro "Bye-bye from Bubble Bay!").
   Target 2:20-3:30. ONE clear lesson. Every episode must be genuinely new (new story, new lesson, new props) — never
   re-skin a previous script with different numbers. Gentle, kind, no scary content, no brands, no real people.
5. **Visuals** (`render.py`): adapt props/scenes to the story (e.g. shapes, shells, fish). Keep Bo and Bloop exactly as in
   `chars.py` (see `characters/`). Update title text (`scene_title`), lesson banner, end card "NEXT TIME" + its icons.
6. **Build audio**: `python3 build.py` (voices + music + mix + timeline). Fix anything that errors.
7. **Preview**: `python3 render.py preview build/p <10-15 times across the timeline>` then
   `python3 ../../tools_contact_sheet.py build/p build/c.png` and LOOK at it. Fix overlaps, cut-off text, wrong props.
   Validate every frame parses (escape `&` as `&amp;` and `<` as `&lt;` in SVG text).
8. **Render**: `python3 render.py full out/<slug>.mp4` (~30 min, run in background and wait).
9. **Shorts + thumbnail**: edit `SHORTS` (3 clips 15-30 s: the mistake, the trick/lesson, the song) and `thumbnail()` in
   `shorts_thumb.py`; run `python3 shorts_thumb.py thumb` and `python3 shorts_thumb.py shorts`. Look at the thumbnail.
10. **Check**: grab 6-8 frames from the final mp4 + one per Short, look at them; loudness about -15 LUFS.
11. **Publish media**: copy the mp4s + thumbnail png to `media/epNN/`, update `plan/episodes.md` (status `done`, dates),
    commit and push to `main` of SkoutStudio/bo-bloop. Public URLs:
    `https://raw.githubusercontent.com/SkoutStudio/bo-bloop/main/media/epNN/<file>`
    Before scheduling, `curl -sI` each URL and make sure it answers 200.
    If Metricool rejects the raw URL, use the jsDelivr mirror instead (files under 20 MB):
    `https://cdn.jsdelivr.net/gh/SkoutStudio/bo-bloop@main/media/epNN/<file>`
12. **Schedule in Metricool** (connector, brand blogId from getBrandSettings, YouTube only), one post per video:
    - `providers: [{"network":"youtube"}]`, `autoPublish: true`, `publicationDate` in Europe/Athens
    - `youtubeData`: `title`, `type` ("video" or "short"), `privacy: "public"`, `tags`, `category: "EDUCATION"`,
      `madeForKids: true`, `isAiGeneratedContent: true`
    - `text` = description (from `upload.md`), `media` = [raw URL]
    - episode: `videoThumbnailUrl` = thumbnail raw URL; if rejected with VIDEO_THUMBNAIL_NOT_APPLICABLE, retry without it.
    - Then `getScheduledPosts` for that range and confirm all 4 are there.
13. **Notify Johnny** (in Greek, short): what was made, the dates, and send the episode mp4 + thumbnail with SendUserFile.
    He can delete any post from Metricool before it goes live.

## Rules
- Never publish anything that is not a Bo & Bloop episode/Short made in this run. Never touch other brands or channels.
- If a step fails and can't be fixed, do not schedule half a week: tell Johnny what failed.
- Keep the repo small: delete `media/` folders of episodes whose posts are all already published (older than 2 weeks).
