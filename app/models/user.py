"""
사용자 ORM 모델
JWT 인증 기반 사용자 계정 관리
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"

    # 기본 키
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 이메일 (고유, 로그인 아이디)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # 사용자 이름
    username: Mapped[str] = mapped_column(String(100), nullable=False)

    # 해싱된 비밀번호
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # 계정 활성화 여부
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 프리미엄 구독 여부 (10년 데이터 + AI 전략 사용 가능)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)

    # 계정 생성 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # 마지막 로그인 시각
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
