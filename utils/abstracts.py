from abc import ABC, abstractmethod


class InfrastructureCreateBlock(ABC):
    @abstractmethod
    def apply(self):
        pass
