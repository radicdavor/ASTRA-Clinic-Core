from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.models.domain import Invoice


@dataclass(frozen=True)
class FiscalizationResult:
    success: bool
    provider: str
    reference: str | None = None
    message: str | None = None
    fiscalized_at: datetime | None = None


class FiscalizationProvider(Protocol):
    name: str

    def fiscalize_invoice(self, invoice: Invoice) -> FiscalizationResult:
        ...

    def fiscalize(self, invoice: Invoice) -> FiscalizationResult:
        ...


class NoopFiscalizationProvider:
    name = "noop"

    def fiscalize(self, invoice: Invoice) -> FiscalizationResult:
        return self.fiscalize_invoice(invoice)

    def fiscalize_invoice(self, invoice: Invoice) -> FiscalizationResult:
        return FiscalizationResult(
            success=True,
            provider=self.name,
            reference=None,
            message="Fiscalization disabled for this environment.",
            fiscalized_at=datetime.now(UTC),
        )


class CroatiaFiscalizationProviderStub:
    name = "croatia_stub"

    def fiscalize(self, invoice: Invoice) -> FiscalizationResult:
        return self.fiscalize_invoice(invoice)

    def fiscalize_invoice(self, invoice: Invoice) -> FiscalizationResult:
        return FiscalizationResult(
            success=False,
            provider=self.name,
            reference=None,
            message="Croatian fiscalization adapter boundary only. No external service call was made.",
            fiscalized_at=None,
        )


def get_fiscalization_provider(provider_name: str | None = None) -> FiscalizationProvider:
    if provider_name == "croatia_stub":
        return CroatiaFiscalizationProviderStub()
    return NoopFiscalizationProvider()
