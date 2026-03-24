from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    adapter_id: str
    ontology_type: type
    
    @classmethod
    @abstractmethod
    def translate(cls, payload: dict):
        raise NotImplementedError("Subclasses must implement the translate method.")
    