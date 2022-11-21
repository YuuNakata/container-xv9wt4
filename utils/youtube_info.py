import traceback

import yt_dlp


async def get_search_urls(search_string):
    import re
    import urllib

    import httpx

    query = urllib.parse.quote(search_string)
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.youtube.com/results?search_query=" + query)
        response = response.text
    ids = re.findall(r'\/watch\?v=([^:]+?)"', response)
    ids = list(set([id if len(id) == 11 else id[:11] for id in ids]))
    return ["https://www.youtube.com/watch?v=" + id for id in ids]


def get_youtube_info(url):
    yt_opt = {"no_warnings": True, "ignoreerrors": True, "restrict_filenames": True, "dumpsinglejson": True, "quiet": True}
    ydl = yt_dlp.YoutubeDL(yt_opt)
    with ydl:
        result = ydl.extract_info(url, download=False)  # We just want to extract the info

    return result


def filter_formats(formats):
    filter = []
    for f in formats:
        try:
            if "(DASH video)" in f["format"]:
                continue
            if f["format_id"] == "136" or f["format_id"] == "135" or f["format_id"] == "134":
                if f["filesize"]:
                    filter.append(f)
        except:
            pass
    return filter


def getVideoData(url):
    try:
        videoinfo = get_youtube_info(url)
        if "playlist" in url:
            format_sample = videoinfo["entries"][0]["formats"]
            format_list = []
            for video in videoinfo["entries"]:
                format_list.append("https://www.youtube.com/watch?v=" + video["id"])
                for i in range(len(video["formats"])):
                    if ("filesize" in video["formats"][i].keys()) and i > 0:
                        if format_sample[i]["filesize"] and video["formats"][i]["filesize"]:
                            format_sample[i]["filesize"] += video["formats"][i]["filesize"]
            return {"name": videoinfo["title"], "formats": format_sample, "videos": format_list}
        return {"name": videoinfo["title"], "formats": videoinfo["formats"]}
    except:
        traceback.print_exc()
    return None


def getVideoInfo(url):
    try:
        videoinfo = get_youtube_info(url)
        return {
            "title": videoinfo["title"],
            "thumbnail": videoinfo["thumbnails"][-2]["url"],
            "channel": videoinfo["channel"],
            "description": videoinfo["description"],
            "duration": videoinfo["duration"],
            "thumbnail_sd": videoinfo["thumbnails"][-6]["url"],
        }
    except:
        traceback.print_exc()
    return None


def yutu_preview(url, index, total):
    videoinfo = getVideoInfo(url)
    duration = int(videoinfo["duration"])
    message = """
<b>Titulo:</b> {}
<b>Canal:</b> {}

<b>Descripcion:</b> {}...

<b>Duracion:</b> {}

            Resultado <b>{}</b> de <b>{}</b>
    """.format(
        videoinfo["title"],
        videoinfo["channel"],
        videoinfo["description"][: 300 if len(videoinfo["description"]) > 300 else len(videoinfo["description"])],
        "{:02d}:{:02d}:{:02d}".format(duration // 3600, (duration % 3600) // 60, int(duration % 60)),
        index + 1,
        total,
    )
    return {"thumbnail": videoinfo["thumbnail"], "thumbnail_sd": videoinfo["thumbnail_sd"], "message": message}
