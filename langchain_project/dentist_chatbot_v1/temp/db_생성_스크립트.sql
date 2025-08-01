-- =================================================================
-- 데이터베이스 생성
-- =================================================================
-- 만약 dentist_chatbot_db 데이터베이스가 존재하면 삭제합니다.
DROP DATABASE IF EXISTS dentist_chatbot_db;

-- dentist_chatbot_db 데이터베이스를 생성하고, 기본 문자셋을 utf8mb4로 설정합니다.
CREATE DATABASE dentist_chatbot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 생성한 데이터베이스를 사용합니다.
USE dentist_chatbot_db;

-- =================================================================
-- 테이블 생성
-- =================================================================

-- -----------------------------------------------------
-- 테이블: `환자` (Patients)
-- 설명: 환자의 기본 정보를 저장하는 테이블입니다.
-- -----------------------------------------------------
CREATE TABLE `환자` (
    `환자ID` INT NOT NULL AUTO_INCREMENT COMMENT '환자 고유 식별자 (Primary Key)',
    `이름` VARCHAR(50) NOT NULL COMMENT '환자 이름',
    `생년월일` DATE NULL COMMENT '환자 생년월일',
    `연락처` VARCHAR(20) NOT NULL COMMENT '환자 연락처 (휴대폰 번호)',
    `이메일` VARCHAR(100) NULL COMMENT '환자 이메일 주소',
    `주소` VARCHAR(255) NULL COMMENT '환자 주소',
    `등록일` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '환자 정보 최초 등록일',
    PRIMARY KEY (`환자ID`),
    UNIQUE INDEX `연락처_UNIQUE` (`연락처` ASC) VISIBLE COMMENT '연락처는 고유해야 합니다.'
) ENGINE = InnoDB COMMENT = '환자 정보 테이블';

-- -----------------------------------------------------
-- 테이블: `의사` (Doctors)
-- 설명: 치과 의사의 정보를 저장하는 테이블입니다.
-- -----------------------------------------------------
CREATE TABLE `의사` (
    `의사ID` INT NOT NULL AUTO_INCREMENT COMMENT '의사 고유 식별자 (Primary Key)',
    `이름` VARCHAR(50) NOT NULL COMMENT '의사 이름',
    `전문분야` VARCHAR(100) NULL COMMENT '전문 진료 분야 (예: 임플란트, 교정, 보철)',
    `진료시간` VARCHAR(255) NULL COMMENT '의사별 진료 가능 시간',
    PRIMARY KEY (`의사ID`)
) ENGINE = InnoDB COMMENT = '의사 정보 테이블';

-- -----------------------------------------------------
-- 테이블: `예약` (Appointments)
-- 설명: 환자의 진료 예약을 관리하는 테이블입니다.
-- -----------------------------------------------------
CREATE TABLE `예약` (
    `예약ID` INT NOT NULL AUTO_INCREMENT COMMENT '예약 고유 식별자 (Primary Key)',
    `환자ID` INT NOT NULL COMMENT '예약을 한 환자의 ID (환자 테이블 FK)',
    `의사ID` INT NOT NULL COMMENT '담당 의사의 ID (의사 테이블 FK)',
    `예약일시` DATETIME NOT NULL COMMENT '예약된 날짜 및 시간',
    `진료내용` TEXT NULL COMMENT '예약 시 환자가 요청한 진료 내용 또는 증상',
    `예약상태` VARCHAR(20) NOT NULL DEFAULT '예약완료' COMMENT '예약 상태 (예: 예약완료, 진료완료, 예약취소)',
    `등록일` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '예약 정보가 등록된 시간',
    PRIMARY KEY (`예약ID`),
    INDEX `fk_예약_환자_idx` (`환자ID` ASC) VISIBLE,
    INDEX `fk_예약_의사_idx` (`의사ID` ASC) VISIBLE,
    CONSTRAINT `fk_예약_환자` FOREIGN KEY (`환자ID`) REFERENCES `환자` (`환자ID`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_예약_의사` FOREIGN KEY (`의사ID`) REFERENCES `의사` (`의사ID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB COMMENT = '진료 예약 정보 테이블';

-- -----------------------------------------------------
-- 테이블: `진료기록` (Medical_Records)
-- 설명: 환자의 진료 내역을 상세하게 기록하는 테이블입니다.
-- -----------------------------------------------------
CREATE TABLE `진료기록` (
    `기록ID` INT NOT NULL AUTO_INCREMENT COMMENT '진료기록 고유 식별자 (Primary Key)',
    `예약ID` INT NOT NULL COMMENT '관련된 예약의 ID (예약 테이블 FK)',
    `환자ID` INT NOT NULL COMMENT '진료받은 환자의 ID (환자 테이블 FK)',
    `의사ID` INT NOT NULL COMMENT '진료한 의사의 ID (의사 테이블 FK)',
    `진료일` DATE NOT NULL COMMENT '실제 진료가 이루어진 날짜',
    `증상` TEXT NULL COMMENT '환자가 호소한 증상',
    `진단명` VARCHAR(255) NULL COMMENT '의사의 진단 결과',
    `처방및치료` TEXT NULL COMMENT '처방된 약 또는 시행된 치료에 대한 상세 내용',
    `비용` DECIMAL(10, 2) NULL COMMENT '발생한 진료 비용',
    PRIMARY KEY (`기록ID`),
    INDEX `fk_진료기록_예약_idx` (`예약ID` ASC) VISIBLE,
    INDEX `fk_진료기록_환자_idx` (`환자ID` ASC) VISIBLE,
    INDEX `fk_진료기록_의사_idx` (`의사ID` ASC) VISIBLE,
    CONSTRAINT `fk_진료기록_예약` FOREIGN KEY (`예약ID`) REFERENCES `예약` (`예약ID`) ON DELETE NO ACTION ON UPDATE CASCADE,
    CONSTRAINT `fk_진료기록_환자` FOREIGN KEY (`환자ID`) REFERENCES `환자` (`환자ID`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_진료기록_의사` FOREIGN KEY (`의사ID`) REFERENCES `의사` (`의사ID`) ON DELETE NO ACTION ON UPDATE CASCADE
) ENGINE = InnoDB COMMENT = '환자 진료 기록 테이블';

-- -----------------------------------------------------
-- 테이블: `챗봇대화기록` (Chatbot_Logs)
-- 설명: 사용자와 챗봇 간의 대화 내용을 저장하는 테이블입니다.
-- -----------------------------------------------------
CREATE TABLE `챗봇대화기록` (
    `로그ID` BIGINT NOT NULL AUTO_INCREMENT COMMENT '대화 로그 고유 식별자 (Primary Key)',
    `세션ID` VARCHAR(100) NOT NULL COMMENT '동일한 사용자의 대화를 묶는 세션 ID',
    `환자ID` INT NULL COMMENT '로그인한 환자의 경우 환자 ID (환자 테이블 FK, 비회원은 NULL)',
    `사용자메시지` TEXT NULL COMMENT '사용자가 입력한 메시지',
    `챗봇응답` TEXT NULL COMMENT '챗봇이 응답한 메시지',
    `의도` VARCHAR(50) NULL COMMENT '파악된 사용자의 의도 (예: 예약문의, 증상문의)',
    `타임스탬프` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '대화가 기록된 시간',
    PRIMARY KEY (`로그ID`),
    INDEX `fk_챗봇대화기록_환자_idx` (`환자ID` ASC) VISIBLE,
    CONSTRAINT `fk_챗봇대화기록_환자` FOREIGN KEY (`환자ID`) REFERENCES `환자` (`환자ID`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB COMMENT = '챗봇 대화 로그 테이블';

-- =================================================================
-- 샘플 데이터 삽입
-- =================================================================

-- 의사 샘플 데이터
INSERT INTO
    `의사` (`이름`, `전문분야`, `진료시간`)
VALUES (
        '김민국',
        '임플란트, 보철',
        '월/수/금 09:00-18:00'
    ),
    (
        '박하나',
        '치아교정, 소아치과',
        '화/목 09:00-18:00, 토 09:00-13:00'
    );

-- 환자 샘플 데이터
INSERT INTO
    `환자` (
        `이름`,
        `생년월일`,
        `연락처`,
        `이메일`,
        `주소`
    )
VALUES (
        '홍길동',
        '1990-05-15',
        '010-1234-5678',
        'gildong@example.com',
        '서울시 강남구 테헤란로'
    ),
    (
        '이순신',
        '1985-11-20',
        '010-8765-4321',
        'soonshin@example.com',
        '서울시 중구 세종대로'
    );

-- 예약 샘플 데이터
INSERT INTO
    `예약` (
        `환자ID`,
        `의사ID`,
        `예약일시`,
        `진료내용`,
        `예약상태`
    )
VALUES (
        1,
        1,
        '2025-08-10 10:30:00',
        '스케일링 및 구강 검진 원합니다.',
        '예약완료'
    ),
    (
        2,
        2,
        '2025-08-11 14:00:00',
        '앞니가 시려서 상담받고 싶습니다.',
        '예약완료'
    );

-- 챗봇 대화 기록 샘플 데이터
INSERT INTO
    `챗봇대화기록` (
        `세션ID`,
        `환자ID`,
        `사용자메시지`,
        `챗봇응답`,
        `의도`
    )
VALUES (
        'SESSION_XYZ_12345',
        1,
        '예약하고 싶어요',
        '네, 예약 도와드리겠습니다. 원하시는 날짜와 시간을 말씀해주세요.',
        '예약문의'
    ),
    (
        'SESSION_XYZ_12345',
        1,
        '다음 주 월요일 오전 10시요',
        '죄송하지만 해당 시간은 이미 예약이 마감되었습니다. 다른 시간은 어떠신가요?',
        '예약시간입력'
    );

SELECT '데이터베이스 및 테이블 생성이 완료되었습니다. 샘플 데이터가 추가되었습니다.' AS `결과`;