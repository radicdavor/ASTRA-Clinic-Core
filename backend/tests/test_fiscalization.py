from app.models.domain import Invoice
from app.services.fiscalization import CroatiaFiscalizationProviderStub, NoopFiscalizationProvider, get_fiscalization_provider


def test_default_fiscalization_provider_is_noop():
    provider = get_fiscalization_provider()
    invoice = Invoice(id=1, patient_id=1, invoice_number="DRAFT-1")

    result = provider.fiscalize_invoice(invoice)

    assert isinstance(provider, NoopFiscalizationProvider)
    assert result.success is True
    assert result.provider == "noop"


def test_croatia_fiscalization_stub_does_not_fiscalize():
    provider = get_fiscalization_provider("croatia_stub")
    invoice = Invoice(id=1, patient_id=1, invoice_number="ASTRA-20260705-00001")

    result = provider.fiscalize_invoice(invoice)

    assert isinstance(provider, CroatiaFiscalizationProviderStub)
    assert result.success is False
    assert "No external service call" in result.message
