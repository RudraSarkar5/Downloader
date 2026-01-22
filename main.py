from fastapi import FastAPI, HTTPException, Query
from pytube import YouTube
from fastapi.responses import StreamingResponse
import io

app = FastAPI(title="YouTube Stream API")


def normalize_youtube_url(url: str) -> str:
    """
    Converts YouTube Shorts URL to standard watch URL
    """
    if "/shorts/" in url:
        video_id = url.split("/shorts/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "YouTube Stream API"
    }


@app.get("/stream")
def stream_youtube_video(
    url: str = Query(..., description="YouTube video URL")
):
    try:
        url = normalize_youtube_url(url)

        yt = YouTube(url)

        # 🎥 Highest resolution progressive stream (video + audio)
        stream = yt.streams.get_highest_resolution()
        if not stream:
            raise HTTPException(status_code=404, detail="Video stream not found")

        buffer = io.BytesIO()
        stream.stream_to_buffer(buffer)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="{yt.video_id}.mp4"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error streaming video: {str(e)}"
        )


@app.get("/audio")
def download_youtube_audio(
    url: str = Query(..., description="YouTube video URL")
):
    try:
        url = normalize_youtube_url(url)

        yt = YouTube(url)

        # 🎧 Highest quality audio-only stream
        audio_stream = (
            yt.streams
            .filter(only_audio=True)
            .order_by("abr")
            .desc()
            .first()
        )

        if not audio_stream:
            raise HTTPException(status_code=404, detail="Audio stream not found")

        buffer = io.BytesIO()
        audio_stream.stream_to_buffer(buffer)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="audio/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="{yt.video_id}.mp3"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading audio: {str(e)}"
        )

