import os

# 현재 작업 디렉토리 확인
print("현재 작업 디렉토리:", os.getcwd())

# 파일 존재 여부 확인
pdf_file = "20250630_더존비즈온.pdf"
if os.path.exists(pdf_file):
    print("파일이 존재합니다.")
else:
    print("파일을 찾을 수 없습니다.")

# 현재 디렉토리의 모든 파일 목록 출력
print("\n현재 디렉토리 파일 목록:")
for file in os.listdir("."):
    if file.endswith(".pdf"):
        print(f"- {file}")
