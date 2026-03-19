"""
헥사고날 아키텍처 - Base Repository Port
Generic[T] 추상 리포지토리 인터페이스
"""
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class AbstractRepository(ABC, Generic[T]):
    """모든 리포지토리가 구현해야 하는 추상 인터페이스"""

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        """ID로 단일 엔티티 조회"""
        ...

    @abstractmethod
    async def get_all(self) -> List[T]:
        """전체 엔티티 목록 조회"""
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        """새 엔티티 생성"""
        ...

    @abstractmethod
    async def update(self, id: int, entity: T) -> Optional[T]:
        """엔티티 수정"""
        ...

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """엔티티 삭제"""
        ...
