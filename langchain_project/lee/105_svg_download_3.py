# --- 라이브러리 설치 안내 ---
# 이 코드를 실행하려면 새로운 라이브러리가 필요합니다.
# 터미널(명령 프롬프트)에서 아래 명령어를 실행하여 설치해주세요.
# pip install requests cairosvg pypdf

# [중요] cairosvg 설치 참고:
# Windows에서는 'cairosvg' 설치 시 오류가 발생할 수 있습니다.
# 이 경우, 먼저 GTK+ for Windows를 설치해야 할 수 있습니다.
# https://www.gtk.org/docs/installations/windows/ 에서 안내를 확인하세요.

import os
import io
import requests
import cairosvg
from pypdf import PdfWriter, PdfReader


def download_svg_files(base_url, start, end, download_folder):
    """지정된 URL 패턴에서 SVG 파일을 다운로드합니다."""
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        print(f"'{download_folder}' 폴더를 생성했습니다.")

    print("SVG 파일 다운로드를 시작합니다...")
    for i in range(start, end + 1):
        file_url = f"{base_url}{i}.svg"
        file_path = os.path.join(download_folder, f"{i}.svg")

        try:
            response = requests.get(file_url, stream=True)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"다운로드 성공: {file_url}")
            else:
                print(f"다운로드 실패 (상태 코드: {response.status_code}): {file_url}")
        except requests.exceptions.RequestException as e:
            print(f"다운로드 중 오류 발생: {file_url}, 오류: {e}")

    print("SVG 파일 다운로드가 완료되었습니다.")


def create_pdf_from_svgs_robust(svg_folder, pdf_file_path, start, end):
    """
    cairosvg와 pypdf를 사용하여 SVG 파일들을 하나의 PDF로 안정적으로 병합합니다.
    """
    print("PDF 생성을 시작합니다 (안정적인 방법)...")
    pdf_writer = PdfWriter()

    for i in range(start, end + 1):
        svg_path = os.path.join(svg_folder, f"{i}.svg")
        if os.path.exists(svg_path):
            try:
                # SVG 파일을 PDF 데이터로 메모리상에서 변환합니다.
                pdf_bytes = cairosvg.svg2pdf(url=svg_path)

                # 변환된 PDF 데이터를 읽어옵니다.
                pdf_reader = PdfReader(io.BytesIO(pdf_bytes))

                # 읽어온 PDF의 첫 페이지를 최종 PDF에 추가합니다.
                pdf_writer.add_page(pdf_reader.pages[0])
                print(f"PDF에 추가 성공: {svg_path}")

            except Exception as e:
                # SVG 파일 자체에 문제가 있어 변환이 불가능한 경우를 처리합니다.
                print(
                    f"오류: {svg_path} 파일을 PDF 페이지로 변환하는 중 오류 발생. {e}"
                )
        else:
            print(f"경고: {svg_path} 파일이 존재하지 않아 건너뜁니다.")

    if len(pdf_writer.pages) > 0:
        try:
            # 병합된 PDF를 파일로 저장합니다.
            with open(pdf_file_path, "wb") as f:
                pdf_writer.write(f)
            print(f"PDF 파일이 성공적으로 생성되었습니다: {pdf_file_path}")
        except Exception as e:
            print(f"최종 PDF 파일 저장 중 오류 발생: {e}")
    else:
        print("PDF에 추가할 유효한 SVG 파일이 없습니다. PDF 파일을 생성하지 않습니다.")


if __name__ == "__main__":
    # --- 설정 ---
    BASE_URL = "https://www.dentalsalon.co.kr/ebook/view/assets/pages/"
    START_PAGE = 1
    END_PAGE = 100
    SVG_DOWNLOAD_FOLDER = "svg_downloads"
    OUTPUT_PDF_FILE = "dental_salon_ebook_final.pdf"

    # 1. SVG 파일 다운로드 (기존과 동일)
    download_svg_files(BASE_URL, START_PAGE, END_PAGE, SVG_DOWNLOAD_FOLDER)

    # 2. 다운로드된 SVG 파일로 PDF 생성 (새롭고 안정적인 방법)
    create_pdf_from_svgs_robust(
        SVG_DOWNLOAD_FOLDER, OUTPUT_PDF_FILE, START_PAGE, END_PAGE
    )
