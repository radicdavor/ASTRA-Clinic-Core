from dataclasses import dataclass

from app.models.domain import Invoice


@dataclass(frozen=True)
class FiscalizationResult:
    status: str
    reference: str | None = None


class FiscalizationProvider:
    def fiscalize(self, invoice: Invoice) -> FiscalizationResult:
        raise NotImplementedError


class NoopFiscalizationProvider(FiscalizationProvider):
    def fiscalize(self, invoice: Invoice) -> FiscalizationResult:
        return FiscalizationResult(status="not_applicable", reference=None)
