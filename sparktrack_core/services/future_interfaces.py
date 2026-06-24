from abc import ABC, abstractmethod
from typing import Any


class OllamaIntegration(ABC):
    @abstractmethod
    def analyze(self, prompt: str, context: dict[str, Any]) -> str:
        raise NotImplementedError


class LocalLLMAnalysisEngine(ABC):
    @abstractmethod
    def summarize_entity(self, entity_type: str, entity_id: int) -> str:
        raise NotImplementedError


class BackupEngine(ABC):
    @abstractmethod
    def create_backup(self) -> str:
        raise NotImplementedError


class EncryptionEngine(ABC):
    @abstractmethod
    def encrypt_database(self) -> None:
        raise NotImplementedError


class SyncEngine(ABC):
    @abstractmethod
    def sync(self) -> None:
        raise NotImplementedError


class AndroidCompanionGateway(ABC):
    @abstractmethod
    def export_companion_payload(self) -> dict[str, Any]:
        raise NotImplementedError
