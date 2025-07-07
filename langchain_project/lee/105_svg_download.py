# 필요한 라이브러리를 설치합니다.
# 터미널이나 명령 프롬프트에서 아래 명령어를 실행하세요.
# pip install requests
# pip install svglib
# pip install reportlab

import os
import requests
from svglib.svglib import svg2rlg
from reportlab.platypus import SimpleDocTemplate, PageBreak
from reportlab.lib.pagesizes import letter
from reportlab.graphics import renderPDF


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
            # 요청이 성공했는지 확인합니다.
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"다운로드 성공: {file_url}")
            else:
                print(f"다운로드 실패 (상태 코드: {response.status_code}): {file_url}")
        except requests.exceptions.RequestException as e:
            print(f"다운로드 중 오류 발생: {file_url}, 오류: {e}")

    print("SVG 파일 다운로드가 완료되었습니다.")


def create_pdf_from_svgs(svg_folder, pdf_file_path, start, end):
    """다운로드된 SVG 파일들을 하나의 PDF로 병합합니다."""
    print("PDF 생성을 시작합니다...")

    # PDF 문서 객체를 생성합니다.
    doc = SimpleDocTemplate(pdf_file_path, pagesize=letter)
    story = []

    # SVG 파일을 순서대로 PDF에 추가합니다.
    for i in range(start, end + 1):
        svg_path = os.path.join(svg_folder, f"{i}.svg")
        if os.path.exists(svg_path):
            try:
                # SVG를 ReportLab 그래픽 객체로 변환합니다.
                drawing = svg2rlg(svg_path)

                if drawing:
                    # 페이지 크기에 맞게 비율을 조정합니다.
                    page_width, page_height = letter
                    # 여백을 고려하여 실제 사용 가능한 너비를 계산합니다.
                    available_width = page_width - doc.leftMargin - doc.rightMargin

                    scale_factor = available_width / drawing.width
                    drawing.width = available_width
                    drawing.height = drawing.height * scale_factor

                    story.append(drawing)
                    story.append(PageBreak())
                    print(f"PDF에 추가: {svg_path}")
                else:
                    print(f"경고: {svg_path} 파일을 처리할 수 없습니다.")
            except Exception as e:
                print(f"오류: {svg_path} 파일을 처리하는 중 오류가 발생했습니다. {e}")
        else:
            print(f"경고: {svg_path} 파일이 존재하지 않아 건너뜁니다.")

    # 마지막 페이지의 불필요한 PageBreak를 제거합니다.
    if story and isinstance(story[-1], PageBreak):
        story.pop()

    if not story:
        print("PDF에 추가할 유효한 SVG 파일이 없습니다. PDF 파일을 생성하지 않습니다.")
        return

    try:
        # PDF 문서를 빌드합니다.
        doc.build(story)
        print(f"PDF 파일이 성공적으로 생성되었습니다: {pdf_file_path}")
    except Exception as e:
        print(f"PDF 생성 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    # --- 설정 ---
    BASE_URL = "https://www.dentalsalon.co.kr/ebook/view/assets/pages/"
    START_PAGE = 1
    END_PAGE = 100
    SVG_DOWNLOAD_FOLDER = "svg_downloads"  # SVG 파일이 저장될 폴더 이름
    OUTPUT_PDF_FILE = "dental_salon_ebook.pdf"  # 최종 PDF 파일 이름

    # 1. SVG 파일 다운로드
    download_svg_files(BASE_URL, START_PAGE, END_PAGE, SVG_DOWNLOAD_FOLDER)

    # 2. 다운로드된 SVG 파일로 PDF 생성
    create_pdf_from_svgs(SVG_DOWNLOAD_FOLDER, OUTPUT_PDF_FILE, START_PAGE, END_PAGE)
