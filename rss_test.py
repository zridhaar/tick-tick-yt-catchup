import os
import yt_dlp
import feedparser
import requests
from datetime import datetime, timezone

# ------------------------------------------------------------------
# TickTick Access Token
# ------------------------------------------------------------------

ACCESS_TOKEN = os.getenv(
    "TICKTICK_ACCESS_TOKEN",
    "7b9e56f4-3dcb-4792-8489-345d5f8ce7ee"
)

# ------------------------------------------------------------------
# yt-dlp Options
# ------------------------------------------------------------------

YDL_OPTS = {
    "quiet": True,
    "extract_flat": True,
    "skip_download": True
}

# ------------------------------------------------------------------
# TickTick
# ------------------------------------------------------------------

def create_ticktick_task(videos):

    if not videos:
        print("No videos today.")
        return

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    due = datetime.now().astimezone().replace(
        hour=23,
        minute=59,
        second=0,
        microsecond=0
    ).isoformat()

    created = 0

    for video in videos:

        payload = {
            "title": f"📺 {video['title']}",
            "content": (
                f"Channel: {video['channel']}\n\n"
                f"Watch:\n{video['link']}"
            ),
            "dueDate": due,
            "priority": 5
        }

        response = requests.post(
            "https://api.ticktick.com/open/v1/task",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            created += 1
            print(f"✅ Created: {video['title']}")
        else:
            print(f"❌ Failed: {video['title']}")
            print(response.text)

    print(f"\nCreated {created} task(s).")

# ------------------------------------------------------------------
# YouTube
# ------------------------------------------------------------------

def get_channel_id(channel_url):

    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:

        info = ydl.extract_info(channel_url, download=False)

        channel_id = info.get("channel_id")

        if not channel_id:
            raise Exception(
                f"Unable to get Channel ID for\n{channel_url}"
            )

        return channel_id


def get_rss_url(channel_url):

    channel_id = get_channel_id(channel_url)

    return (
        f"https://www.youtube.com/feeds/videos.xml"
        f"?channel_id={channel_id}"
    )


def get_today_videos(channel_url):

    rss_url = get_rss_url(channel_url)

    feed = feedparser.parse(rss_url)

    today = datetime.now(timezone.utc).date()

    videos = []

    for entry in feed.entries:

        published = datetime(
            *entry.published_parsed[:6],
            tzinfo=timezone.utc
        )

        if published.date() == today:

            videos.append({
                "channel": feed.feed.title,
                "title": entry.title,
                "link": entry.link,
                "published": published
            })

    return videos


# ------------------------------------------------------------------
# Read Channels
# ------------------------------------------------------------------

def load_channels():

    with open(
        "youtube_channels.txt",
        encoding="utf8"
    ) as f:

        return [
            line.strip()
            for line in f
            if line.strip()
        ]


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():

    channels = load_channels()

    all_videos = []

    print()

    print("=" * 80)
    print("Checking Channels")
    print("=" * 80)

    for channel in channels:

        print(channel)

        try:

            videos = get_today_videos(channel)

            all_videos.extend(videos)

        except Exception as e:

            print(e)

    print()

    print("=" * 80)
    print("TODAY'S VIDEOS")
    print("=" * 80)

    if len(all_videos) == 0:

        print("No uploads today.")

        return

    for video in all_videos:

        print()

        print(video["channel"])
        print(video["title"])
        print(video["link"])
        print(video["published"])

        print("-" * 80)

    create_ticktick_task(all_videos)


# ------------------------------------------------------------------

if __name__ == "__main__":
    main()