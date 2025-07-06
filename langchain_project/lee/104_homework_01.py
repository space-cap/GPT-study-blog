class 무의식:
    def __init__(self):
        print("무의식")


class 의식:
    def __init__(self):
        print("의식")


class 전의식:
    """의식과 무의식 사이에 위치하는 정신의 중간 영역"""

    def __init__(self, 무의식, 의식):
        self._무의식 = 무의식
        self._의식 = 의식
        print("전의식")


class 꿈:
    def __init__(self, 무의식, 전의식):
        self._무의식 = 무의식
        self._전의식 = 전의식
        print("꿈")


class 심리:
    def __init__(self):
        print("심리")


class 사고(심리):
    """논리적 분석과 판단"""

    def __init__(self, 의식):
        self._의식 = 의식
        print("사고")


class 감정(심리):
    """가치 판단과 정서적 반응"""

    def __init__(self, 의식, 무의식):
        self._의식 = 의식
        self._무의식 = 무의식
        print("감정")


class 감각(심리):
    """현실 인식과 구체적 정보 처리"""

    def __init__(self, 의식):
        self._의식 = 의식
        print("감각")


class 직관(심리):
    """가능성과 잠재력 인식"""

    def __init__(self, 무의식, 전의식):
        self._무의식 = 무의식
        self._전의식 = 전의식
        print("직관")


class 정신:
    def __init__(self):
        # 정신 구조
        self._무의식 = 무의식()
        self._의식 = 의식()
        self._전의식 = 전의식(self._무의식, self._의식)
        self._꿈 = 꿈(self._무의식, self._전의식)

        # 심리
        self._사고 = 사고(self._의식)
        self._감정 = 감정(self._의식, self._무의식)
        self._감각 = 감각(self._의식)
        self._직관 = 직관(self._무의식, self._전의식)
        print("정신")


soul = 정신()
