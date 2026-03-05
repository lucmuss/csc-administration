# E2E Tests für CSC-Administration

Dieses Verzeichnis enthält End-to-End Tests für alle wichtigen Features.

## Struktur

```
tests/e2e/
├── __init__.py              # (leer)
├── conftest.py              # Shared fixtures
├── test_auth_flow.py        # Login, Register, Logout
├── test_member_flow.py      # Mitgliederverwaltung
├── test_inventory_flow.py   # Inventar/Sorten
├── test_orders_flow.py      # Bestellungen/Shop
├── test_messaging_flow.py   # Massen-E-Mails
├── test_finance_flow.py     # Zahlungen/SEPA
├── test_compliance_flow.py  # Compliance/Regeln
├── test_cultivation_flow.py # Anbau (nicht implementiert)
└── test_admin_flow.py       # Admin-Funktionen
```

## Ausführung

```bash
# Alle E2E Tests
pytest tests/e2e/ -v

# Einzelne Test-Datei
pytest tests/e2e/test_messaging_flow.py -v

# Mit Coverage
pytest tests/e2e/ --cov=apps --cov-report=term-missing
```

## Fixtures (conftest.py)

| Fixture | Beschreibung |
|---------|--------------|
| `member_user` | Standard-Mitglied |
| `staff_user` | Mitarbeiter |
| `board_user` | Vorstand |
| `pending_member` | Mitglied mit pending Status |
| `strain` | Test-Sorte |
| `batch` | Test-Charge |
| `email_group` | Test-E-Mail-Gruppe |
| `mass_email_draft` | Test-Massen-E-Mail |
| `invoice` | Test-Rechnung |
| `sepa_mandate` | Test-SEPA-Mandat |

## Test-Abdeckung

| Bereich | Tests | Status |
|---------|-------|--------|
| Auth | 10 | ✅ |
| Messaging | 14 | ✅ |
| Orders | 11 | ✅ |
| Members | 14 | ✅ |
| Inventory | 14 | ✅ |
| Finance | 14 | ✅ |
| Compliance | 13 | ✅ |
| Admin | 15 | ✅ |
| Cultivation | 10 | ⏸️ (nicht implementiert) |

**Gesamt: 115 Tests**
