from pytube import YouTube
import os


def download_youtube_video_720p(video_url, download_path="./downloads"):
    """
    유튜브 영상을 720p 해상도로 다운로드하는 함수

    Parameters:
    video_url (str): 다운로드할 유튜브 영상 URL
    download_path (str): 다운로드할 폴더 경로
    """
    try:
        print("🔗 영상 정보를 가져오는 중...")

        # YouTube 객체 생성
        yt = YouTube(video_url)

        # 영상 정보 출력
        print(f"📺 제목: {yt.title}")
        print(f"👤 채널: {yt.author}")
        print(f"⏱️ 길이: {yt.length}초")

        # 720p 해상도의 mp4 스트림 선택
        video_stream = yt.streams.filter(
            res="720p", file_extension="mp4"  # 720p 해상도 지정  # MP4 형식만
        ).first()

        # 720p가 없는 경우 사용 가능한 해상도 확인
        if video_stream is None:
            print("❌ 720p 해상도를 찾을 수 없습니다.")
            print("📋 사용 가능한 해상도:")

            # 사용 가능한 모든 해상도 출력
            available_streams = yt.streams.filter(file_extension="mp4")
            for stream in available_streams:
                if stream.resolution:
                    print(f"  - {stream.resolution}")
            return False

        print(f"✅ 720p 해상도 스트림을 찾았습니다!")
        print(f"💾 파일 크기: {video_stream.filesize_mb:.1f}MB")

        # 다운로드 폴더 생성
        if not os.path.exists(download_path):
            os.makedirs(download_path)
            print(f"📁 폴더 생성: {download_path}")

        # 영상 다운로드 시작
        print("⬇️ 다운로드 시작...")
        video_stream.download(download_path)
        print("✅ 다운로드 완료!")

        return True

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False


# 실행 코드
if __name__ == "__main__":
    # 다운로드할 유튜브 영상 URL
    video_url = "https://www.youtube.com/watch?v=W_uwR_yx4-c&t=3117s"

    # 다운로드 실행
    success = download_youtube_video_720p(video_url)

    if success:
        print("\n🎉 720p 해상도로 다운로드가 완료되었습니다!")
    else:
        print("\n😞 다운로드에 실패했습니다.")
