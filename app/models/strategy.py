"""
백테스팅 전략 ORM 모델
사용자가 저장한 전략 파라미터 보관
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Strategy(Base):
    """전략 테이블"""
    __tablename__ = "strategies"

    # 기본 키
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 소유자 (사용자 FK)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 전략 이름 (예: "20/60 이동평균 교차")
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 전략 유형 (ma_cross / rsi / ai_generated)
    strategy_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # 전략 파라미터 (JSON 문자열)
    # 예: {"short_window": 20, "long_window": 60}
    params_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # Gemini가 생성한 전략인 경우 설명
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 전략 생성 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Strategy id={self.id} name={self.name} type={self.strategy_type}>"
