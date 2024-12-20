import streamlit as st

st.title("Hello world!")

st.subheader("Welcome to Streamlit!")

st.markdown(
    """
    Streamlit은 Python 개발자들이 데이터 애플리케이션을 쉽고 빠르게 만들 수 있도록 도와주는 오픈소스 프레임워크입니다. 다음은 Streamlit의 주요 특징과 장점입니다:

## Streamlit의 특징

### 간편한 웹 애플리케이션 개발
Streamlit을 사용하면 복잡한 웹 개발 지식 없이도 Python 코드만으로 인터랙티브한 웹 애플리케이션을 만들 수 있습니다. HTML, CSS, JavaScript에 대한 지식이 없어도 됩니다[1].

### 데이터 시각화에 최적화
데이터 분석 결과를 쉽게 시각화할 수 있습니다. Matplotlib, Plotly, Altair 등 다양한 시각화 라이브러리와 통합되어 있어 복잡한 데이터도 쉽게 시각화할 수 있습니다[5].

### 실시간 업데이트
사용자의 입력이 변경될 때마다 애플리케이션이 자동으로 업데이트되어 새로운 결과를 보여줍니다[5].

## Streamlit의 활용

Streamlit은 다음과 같은 다양한 용도로 활용될 수 있습니다:

1. **데이터 시각화 대시보드**: 판매 데이터 분석, 금융 데이터 시각화 등의 대시보드를 쉽게 만들 수 있습니다[6].

2. **머신러닝 모델 배포**: Python으로 만든 머신러닝 모델을 웹 애플리케이션으로 쉽게 배포할 수 있습니다[6].

3. **인터랙티브 데이터 분석 도구**: 사용자가 데이터를 직접 탐색하고 분석 결과를 실시간으로 확인할 수 있는 도구를 만들 수 있습니다[6].

4. **실시간 데이터 모니터링**: 서버 상태나 센서 데이터를 실시간으로 모니터링하는 대시보드를 만들 수 있습니다[6].

## Streamlit 사용 방법

Streamlit을 사용하려면 다음과 같은 단계를 따르면 됩니다:

1. Streamlit 설치: `pip install streamlit`

2. Python 스크립트 작성: Streamlit 라이브러리를 import하고 필요한 코드를 작성합니다.

3. 애플리케이션 실행: `streamlit run your_script.py` 명령어로 실행합니다[8].

Streamlit은 데이터 과학자, 엔지니어, 연구자들이 복잡한 웹 개발 기술 없이도 데이터 중심의 웹 애플리케이션을 빠르게 구축하고 공유할 수 있게 해주는 강력한 도구입니다.

Citations:
[1] https://codemagician.tistory.com/entry/Streamlit-00-Streamlit-%EC%9D%B4%EB%9E%80-%EB%AC%B4%EC%97%87%EC%9D%B8%EA%B0%80%EC%9A%94
[2] https://gsroot.tistory.com/63
[3] https://shrimp-taco.tistory.com/entry/Streamlit-%EC%8A%A4%ED%8A%B8%EB%A6%BC%EB%A6%BF%EC%9D%B4%EB%9E%80-%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B6%84%EC%84%9D-%EC%8B%9C%EA%B0%81%ED%99%94-%EC%98%A4%ED%94%88%EC%86%8C%EC%8A%A4-%EB%9D%BC%EC%9D%B4%EB%B8%8C%EB%9F%AC%EB%A6%AC
[4] https://www.sktenterprise.com/bizInsight/blogDetail/dev/10237
[5] https://f-lab.kr/insight/developing-data-science-applications-with-streamlit
[6] https://mvje.tistory.com/218
[7] https://sksdudtjs.tistory.com/64
[8] https://minimin2.tistory.com/184
[9] https://psystat.tistory.com/217
[10] https://zzsza.github.io/mlops/2021/02/07/python-streamlit-dashboard/
"""
)