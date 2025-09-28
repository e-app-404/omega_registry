from abc import ABC, abstractmethod


class AbstractEnricher(ABC):
    @abstractmethod
    def enrich(self, entity: dict, context: dict) -> dict:
        """
        Enrich an entity with additional fields or transformations.
        Args:
            entity: The entity dictionary to enrich.
            context: Additional context or lookups needed for enrichment.
        Returns:
            dict: The enriched entity (may be a new dict or mutated in place).
        """
        pass
