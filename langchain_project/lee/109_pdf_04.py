import PyPDF2
import pandas as pd
import re
from typing import List, Dict
import json
import os
from pathlib import Path

class PDFToKnowledgeConverter:
    def __init__(self, output_dir: str = "knowledge_output"):
        self.knowledge_base = []
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 텍스트 추출 (인코딩 문제 해결)"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- 페이지 {page_num + 1} ---\n"
                            text += page_text + "\n"
                    except Exception as e:
                        print(f"페이지 {page_num + 1} 텍스트 추출 실패: {e}")
                        continue
        except Exception as e:
            print(f"PDF 텍스트 추출 오류: {e}")
        return text
    
    def extract_tables_from_pdf(self, pdf_path: str) -> List[pd.DataFrame]:
        """PDF에서 표 추출 (인코딩 옵션 추가)"""
        try:
            import tabula
            print("tabula-py를 사용하여 표 추출 시도...")
            
            encodings = ['utf-8', 'cp949', 'euc-kr', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    print(f"인코딩 {encoding} 시도 중...")
                    tables = tabula.read_pdf(
                        pdf_path, 
                        pages='all', 
                        multiple_tables=True,
                        encoding=encoding,
                        lattice=True,
                        stream=True
                    )
                    if tables:
                        print(f"✅ {encoding} 인코딩으로 {len(tables)}개 표 추출 성공")
                        return tables
                except Exception as e:
                    print(f"{encoding} 인코딩 실패: {e}")
                    continue
                    
            print("⚠️ 모든 인코딩 방식 실패, 빈 리스트 반환")
            return []
            
        except ImportError:
            print("❌ tabula-py가 설치되지 않았습니다.")
            return []
        except Exception as e:
            print(f"표 추출 오류: {e}")
            return []
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[Dict]:
        """PDF에서 이미지 추출 및 저장"""
        images_info = []
        
        try:
            import fitz  # PyMuPDF
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(pdf_document, xref)
                    
                    if pix.n - pix.alpha < 4:
                        img_filename = f"page_{page_num+1}_img_{img_index+1}.png"
                        img_path = self.images_dir / img_filename
                        
                        pix.save(str(img_path))
                        
                        images_info.append({
                            "filename": img_filename,
                            "path": str(img_path),
                            "page": page_num + 1,
                            "index": img_index + 1,
                            "width": pix.width,
                            "height": pix.height,
                            "description": f"페이지 {page_num+1}의 이미지 {img_index+1}",
                            "tags": ["document_image", f"page_{page_num+1}"]
                        })
                    
                    pix = None
            
            pdf_document.close()
            print(f"✅ {len(images_info)}개의 이미지를 추출했습니다.")
            
        except ImportError:
            print("⚠️ PyMuPDF가 설치되지 않았습니다. 이미지 추출을 건너뜁니다.")
        except Exception as e:
            print(f"이미지 추출 중 오류: {e}")
        
        return images_info
    
    def clean_text(self, text: str) -> str:
        """텍스트 정제 (한글 지원)"""
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s가-힣.,?!():\-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def split_into_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """텍스트를 청크로 분할"""
        if not text:
            return []
        
        sentences = re.split(r'[.!?]\s+', text)
        
        chunks = []
        current_chunk = ""
        current_size = 0
        
        for sentence in sentences:
            words = sentence.split()
            sentence_size = len(words)
            
            if current_size + sentence_size <= chunk_size:
                current_chunk += sentence + ". "
                current_size += sentence_size
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
                current_size = sentence_size
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def table_to_qa_pairs(self, table: pd.DataFrame, table_index: int) -> List[Dict]:
        """표를 Q&A 쌍으로 변환"""
        qa_pairs = []
        
        if table.empty:
            return qa_pairs
        
        try:
            qa_pairs.append({
                "question": f"표 {table_index + 1}의 구조를 알려주세요.",
                "answer": f"표 {table_index + 1}은 {len(table.columns)}개 열, {len(table)}개 행으로 구성되어 있습니다. 열 이름은 {', '.join(str(col) for col in table.columns)}입니다.",
                "source": "table_structure",
                "metadata": {
                    "table_index": table_index,
                    "columns": len(table.columns),
                    "rows": len(table)
                }
            })
            
            for row_idx, row in table.iterrows():
                if row_idx >= 10:
                    break
                    
                first_col = str(table.columns[0])
                first_value = str(row.iloc[0]) if pd.notna(row.iloc[0]) else "정보 없음"
                
                answer_parts = []
                for col, value in row.items():
                    if pd.notna(value) and str(value).strip():
                        answer_parts.append(f"{col}: {value}")
                
                if answer_parts:
                    question = f"{first_col} '{first_value}'에 대한 정보를 알려주세요."
                    answer = f"{first_col} '{first_value}'의 정보는 다음과 같습니다. " + ", ".join(answer_parts) + "."
                    
                    qa_pairs.append({
                        "question": question,
                        "answer": answer,
                        "source": "table_row",
                        "metadata": {
                            "table_index": table_index,
                            "row_index": row_idx,
                            "primary_key": first_value
                        }
                    })
                    
        except Exception as e:
            print(f"표 {table_index} Q&A 변환 중 오류: {e}")
        
        return qa_pairs
    
    def text_to_knowledge_structure(self, text_chunks: List[str]) -> List[Dict]:
        """텍스트 청크를 지식 구조로 변환"""
        knowledge_items = []
        
        for i, chunk in enumerate(text_chunks):
            if not chunk.strip():
                continue
                
            sentences = chunk.split('.')
            title = sentences[0].strip()[:100]
            if not title:
                title = f"문서 섹션 {i + 1}"
            
            words = chunk.split()
            keywords = []
            for word in words:
                if len(word) > 2 and word.isalpha():
                    keywords.append(word)
            keywords = list(set(keywords))[:10]
            
            knowledge_item = {
                "id": f"doc_chunk_{i}",
                "title": title,
                "content": chunk,
                "type": "document",
                "keywords": keywords,
                "metadata": {
                    "chunk_index": i,
                    "word_count": len(chunk.split()),
                    "character_count": len(chunk)
                }
            }
            knowledge_items.append(knowledge_item)
        
        return knowledge_items
    
    def process_pdf(self, pdf_path: str) -> Dict:
        """PDF 전체 처리 파이프라인"""
        result = {
            "document_knowledge": [],
            "table_qa_pairs": [],
            "images": [],
            "summary": {},
            "metadata": {
                "source_file": pdf_path,
                "processing_timestamp": pd.Timestamp.now().isoformat()
            }
        }
        
        print(f"📄 PDF 처리 시작: {pdf_path}")
        
        # 텍스트 추출
        print("📝 텍스트 추출 중...")
        raw_text = self.extract_text_from_pdf(pdf_path)
        
        if raw_text:
            cleaned_text = self.clean_text(raw_text)
            text_chunks = self.split_into_chunks(cleaned_text, chunk_size=300)
            print(f"✅ {len(text_chunks)}개의 텍스트 청크 생성")
            result["document_knowledge"] = self.text_to_knowledge_structure(text_chunks)
        else:
            print("⚠️ 추출된 텍스트가 없습니다.")
        
        # 표 추출
        print("📊 표 추출 및 Q&A 생성 중...")
        tables = self.extract_tables_from_pdf(pdf_path)
        
        for table_idx, table in enumerate(tables):
            if not table.empty:
                print(f"📋 표 {table_idx + 1} 처리 중... (크기: {table.shape})")
                qa_pairs = self.table_to_qa_pairs(table, table_idx)
                result["table_qa_pairs"].extend(qa_pairs)
        
        # 이미지 추출
        print("🖼️ 이미지 추출 중...")
        images_info = self.extract_images_from_pdf(pdf_path)
        result['images'] = images_info
        
        # 요약
        result["summary"] = {
            "total_text_chunks": len(result["document_knowledge"]),
            "total_tables": len(tables),
            "total_qa_pairs": len(result["table_qa_pairs"]),
            "total_images": len(images_info),
            "total_knowledge_items": len(result["document_knowledge"]),
            "original_text_length": len(raw_text) if raw_text else 0
        }
        
        print("✅ PDF 처리 완료!")
        return result
    
    def save_readable_results(self, knowledge_data: Dict, output_name: str):
        """가독성 좋은 형태로 결과 저장"""
        
        # HTML 보고서 생성
        html_path = self.output_dir / f"{output_name}_report.html"
        self.create_html_report(knowledge_data, html_path)
        
        # 텍스트 요약 파일
        txt_path = self.output_dir / f"{output_name}_summary.txt"
        self.create_text_summary(knowledge_data, txt_path)
        
        # Excel 파일
        excel_path = self.output_dir / f"{output_name}_tables.xlsx"
        self.create_excel_tables(knowledge_data, excel_path)
        
        # CSV 파일
        csv_path = self.output_dir / f"{output_name}_qa_pairs.csv"
        self.create_qa_csv(knowledge_data, csv_path)
        
        # JSON 파일
        json_path = self.output_dir / f"{output_name}_knowledge.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 결과물이 저장되었습니다:")
        print(f"📄 HTML 보고서: {html_path}")
        print(f"📝 텍스트 요약: {txt_path}")
        print(f"📊 Excel 표: {excel_path}")
        print(f"❓ Q&A CSV: {csv_path}")
        print(f"🖼️ 이미지 폴더: {self.images_dir}")
        print(f"💾 JSON 데이터: {json_path}")
    
    def create_html_report(self, knowledge_data: Dict, output_path: Path):
        """HTML 보고서 생성"""
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF 지식 구조 변환 보고서</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .summary-box {{ background: #e3f2fd; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0; }}
        .section {{ margin: 30px 0; }}
        .knowledge-item {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .qa-pair {{ background: #f5f5f5; padding: 10px; margin: 8px 0; border-radius: 5px; }}
        .question {{ font-weight: bold; color: #1976D2; }}
        .answer {{ margin-top: 5px; }}
        .image-gallery {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .image-item {{ border: 1px solid #ddd; padding: 10px; border-radius: 5px; text-align: center; }}
        .image-item img {{ max-width: 200px; max-height: 200px; }}
        .metadata {{ font-size: 0.9em; color: #666; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 PDF 지식 구조 변환 보고서</h1>
        <p><strong>원본 파일:</strong> {knowledge_data.get('metadata', {}).get('source_file', 'Unknown')}</p>
        <p><strong>처리 시간:</strong> {knowledge_data.get('metadata', {}).get('processing_timestamp', 'Unknown')}</p>
    </div>

    <div class="summary-box">
        <h2>📊 처리 결과 요약</h2>
        <ul>
            <li>📝 텍스트 청크: <strong>{knowledge_data['summary']['total_text_chunks']:,}개</strong></li>
            <li>📊 추출된 표: <strong>{knowledge_data['summary']['total_tables']:,}개</strong></li>
            <li>❓ Q&A 쌍: <strong>{knowledge_data['summary']['total_qa_pairs']:,}개</strong></li>
            <li>🖼️ 추출된 이미지: <strong>{knowledge_data['summary']['total_images']:,}개</strong></li>
            <li>📄 원본 텍스트 길이: <strong>{knowledge_data['summary']['original_text_length']:,} 문자</strong></li>
        </ul>
    </div>
"""
        
        # 이미지 갤러리
        if knowledge_data.get('images'):
            html_content += """
    <div class="section">
        <h2>🖼️ 추출된 이미지</h2>
        <div class="image-gallery">
"""
            for img in knowledge_data['images']:
                html_content += f"""
            <div class="image-item">
                <img src="images/{img['filename']}" alt="{img['description']}">
                <div class="metadata">
                    <strong>{img['description']}</strong><br>
                    크기: {img['width']} x {img['height']}<br>
                    태그: {', '.join(img['tags'])}
                </div>
            </div>
"""
            html_content += """
        </div>
    </div>
"""
        
        # 문서 지식
        html_content += """
    <div class="section">
        <h2>📚 문서 지식 구조</h2>
"""
        for item in knowledge_data['document_knowledge'][:5]:
            html_content += f"""
        <div class="knowledge-item">
            <h3>{item['title']}</h3>
            <p>{item['content'][:500]}...</p>
            <div class="metadata">
                <strong>키워드:</strong> {', '.join(item.get('keywords', [])[:8])}<br>
                <strong>단어 수:</strong> {item['metadata']['word_count']}<br>
                <strong>문자 수:</strong> {item['metadata']['character_count']}
            </div>
        </div>
"""
        
        # Q&A
        if knowledge_data['table_qa_pairs']:
            html_content += """
    </div>
    
    <div class="section">
        <h2>❓ 표 기반 Q&A</h2>
"""
            for qa in knowledge_data['table_qa_pairs'][:10]:
                html_content += f"""
        <div class="qa-pair">
            <div class="question">Q: {qa['question']}</div>
            <div class="answer">A: {qa['answer']}</div>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def create_text_summary(self, knowledge_data: Dict, output_path: Path):
        """텍스트 요약 파일 생성"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("📄 PDF 지식 구조 변환 요약 보고서\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"원본 파일: {knowledge_data.get('metadata', {}).get('source_file', 'Unknown')}\n")
            f.write(f"처리 시간: {knowledge_data.get('metadata', {}).get('processing_timestamp', 'Unknown')}\n\n")
            
            f.write("📊 처리 결과:\n")
            f.write(f"- 텍스트 청크: {knowledge_data['summary']['total_text_chunks']:,}개\n")
            f.write(f"- 추출된 표: {knowledge_data['summary']['total_tables']:,}개\n")
            f.write(f"- Q&A 쌍: {knowledge_data['summary']['total_qa_pairs']:,}개\n")
            f.write(f"- 추출된 이미지: {knowledge_data['summary']['total_images']:,}개\n")
            f.write(f"- 원본 텍스트 길이: {knowledge_data['summary']['original_text_length']:,} 문자\n\n")
    
    def create_excel_tables(self, knowledge_data: Dict, output_path: Path):
        """Excel 파일 생성"""
        try:
            with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
                summary_data = {
                    '항목': ['텍스트 청크', '추출된 표', 'Q&A 쌍', '추출된 이미지', '원본 텍스트 길이'],
                    '개수': [
                        knowledge_data['summary']['total_text_chunks'],
                        knowledge_data['summary']['total_tables'],
                        knowledge_data['summary']['total_qa_pairs'],
                        knowledge_data['summary']['total_images'],
                        knowledge_data['summary']['original_text_length']
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='요약', index=False)
        except Exception as e:
            print(f"Excel 파일 생성 실패: {e}")
    
    def create_qa_csv(self, knowledge_data: Dict, output_path: Path):
        """Q&A CSV 생성"""
        try:
            qa_data = []
            for qa in knowledge_data['table_qa_pairs']:
                qa_data.append({
                    '질문': qa['question'],
                    '답변': qa['answer'],
                    '출처': qa['source'],
                    '테이블_인덱스': qa['metadata'].get('table_index', ''),
                    '행_인덱스': qa['metadata'].get('row_index', ''),
                    '주요키': qa['metadata'].get('primary_key', '')
                })
            
            if qa_data:
                pd.DataFrame(qa_data).to_csv(str(output_path), index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"CSV 파일 생성 실패: {e}")

# 실행 함수
def process_pdf_with_enhanced_output(pdf_path: str):
    """향상된 출력 기능이 포함된 PDF 처리"""
    
    path = Path(pdf_path)
    if not path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {pdf_path}")
        return None
    
    try:
        output_name = path.stem
        converter = PDFToKnowledgeConverter(output_dir=f"{output_name}_results")
        
        print("🚀 PDF 처리 시작 (이미지 포함)")
        knowledge_data = converter.process_pdf(str(path))
        
        converter.save_readable_results(knowledge_data, output_name)
        
        print("\n🎉 처리 완료!")
        return knowledge_data
        
    except Exception as e:
        print(f"❌ 처리 실패: {e}")
        return None

# 실행
if __name__ == "__main__":
    pdf_file = ".\\20250630_더존비즈온.pdf"
    process_pdf_with_enhanced_output(pdf_file)
