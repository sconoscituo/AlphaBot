"""
ServiceFactory - 싱글톤 패턴으로 서비스 인스턴스 관리
thread-safe 구현 (threading.Lock)
"""
import threading
from typing import Any, Dict, Type


class ServiceFactory:
    _instance: "ServiceFactory | None" = None
    _lock: threading.Lock = threading.Lock()
    _registry: Dict[str, Any] = {}

    def __new__(cls) -> "ServiceFactory":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._registry = {}
        return cls._instance

    def register(self, name: str, service: Any) -> None:
        """서비스 인스턴스를 이름으로 등록"""
        with self._lock:
            self._registry[name] = service

    def get(self, name: str) -> Any:
        """등록된 서비스 인스턴스 반환"""
        return self._registry.get(name)

    def get_or_create(self, name: str, factory_cls: Type, *args, **kwargs) -> Any:
        """서비스가 없으면 생성 후 등록, 있으면 기존 인스턴스 반환"""
        with self._lock:
            if name not in self._registry:
                self._registry[name] = factory_cls(*args, **kwargs)
        return self._registry[name]

    @classmethod
    def reset(cls) -> None:
        """테스트용 싱글톤 초기화"""
        with cls._lock:
            cls._instance = None


# 전역 팩토리 인스턴스
service_factory = ServiceFactory()
