from pytubefix import YouTube
from pytubefix.cli import on_progress
import os


def download_youtube_video_720p(video_url, download_path="./downloads"):
    """
    pytubefix를 사용하여 유튜브 영상을 720p 해상도로 다운로드
    """
    try:
        print("🔗 영상 정보를 가져오는 중...")

        # YouTube 객체 생성 (진행률 콜백 포함)
        yt = YouTube(video_url, on_progress_callback=on_progress)

        # 영상 정보 출력
        print(f"📺 제목: {yt.title}")
        print(f"👤 채널: {yt.author}")

        # 720p 해상도 스트림 선택
        # video_stream = yt.streams.filter(res="720p", file_extension="mp4").first()
        video_stream = yt.streams.filter(res="360p", file_extension="mp4").first()

        if video_stream is None:
            print("❌ 720p 해상도를 찾을 수 없습니다.")
            # 최고 해상도로 대체
            video_stream = yt.streams.get_highest_resolution()
            print(f"✅ 최고 해상도로 다운로드: {video_stream.resolution}")

        # 다운로드 폴더 생성
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        # 다운로드 실행
        print("⬇️ 다운로드 시작...")
        video_stream.download(download_path)
        print("✅ 다운로드 완료!")

        return True

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False


# 실행
# video_url = "https://www.youtube.com/watch?v=W_uwR_yx4-c&t=3117s"
video_url = "https://www.youtube.com/live/cg2nlJaiqLk"

download_youtube_video_720p(video_url)
