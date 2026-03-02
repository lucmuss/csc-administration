# CSC Administration - Test Strategie & User Stories

> E2E Tests, Flow Tests, Smoke Tests mit Playwright + MCP + Chrome DevTools
> Stand: 2. März 2026

---

## 🎯 Test-Pyramide

```
        /\
       /  \     E2E Tests (Playwright)
      / 10%\    (Kritische User Flows)
     /--------\
    /          \   Integration Tests
   /    30%    \  (API, Database, Services)
  /--------------\
 /                \  Unit Tests
/       60%       \ (Models, Utils, Business Logic)
--------------------
```

---

## 👤 User Stories für Testing

### Kategorie: Kritische Geschäftsprozesse (Muss funktionieren!)

#### US-TEST-001: Mitglieds-Registrierung komplett
**Als** potenzielles Mitglied  
**möchte ich** mich registrieren und verifizieren können  
**damit** ich Bestellungen tätigen kann.

**Akzeptanzkriterien (Testbar):**
- [ ] Formular lädt in < 2 Sekunden
- [ ] E-Mail-Validierung zeigt Fehler bei ungültiger E-Mail
- [ ] Altersprüfung (21+) funktioniert
- [ ] Bestätigungs-E-Mail wird versendet
- [ ] 8-Wochen-Deadline-Tracking startet
- [ ] Nach Verifizierung: Status ändert sich zu "Aktiv"

**E2E Test (Playwright):**
```javascript
test('komplette Registrierung', async ({ page }) => {
  await page.goto('/register');
  await page.fill('[name=email]', 'test@example.com');
  await page.fill('[name=birthdate]', '1990-01-01');
  await page.click('[type=submit]');
  await expect(page.locator('.success')).toContainText('E-Mail versendet');
  // E-Mail abrufen (Test-Mail-Server)
  const email = await getTestEmail('test@example.com');
  await expect(email.subject).toContain('Mitgliedschaft');
});
```

---

#### US-TEST-002: Limit-Prüfung bei Bestellung
**Als** Mitglied  
**möchte ich** nicht mehr als 25g/Tag und 50g/Monat bestellen können  
**damit** ich CanG-konform bleibe.

**Akzeptanzkriterien:**
- [ ] Limit-Prüfung in Echtzeit (vor Warenkorb)
- [ ] Fehlermeldung bei Überschreitung
- [ ] Automatische Sperre bei >50g/Monat
- [ ] Reset um 00:00 Uhr funktioniert

**E2E Test:**
```javascript
test('Limit-Überschreitung verhindern', async ({ page }) => {
  // Einloggen als Test-Mitglied mit 48g/Monat verbraucht
  await login(page, 'test-member');
  await page.goto('/shop');
  await page.fill('[name=quantity]', '5'); // 5g hinzufügen
  await expect(page.locator('.error')).toContainText('Limit überschritten');
  await expect(page.locator('[type=submit]')).toBeDisabled();
});
```

---

#### US-TEST-003: SEPA-Zahlung komplett
**Als** Mitglied  
**möchte ich** per SEPA-Lastschrift bezahlen  
**damit** ich kein Bargeld brauche.

**Akzeptanzkriterien:**
- [ ] Mandat wird erstellt mit eindeutiger Referenz
- [ ] Vorabankündigung per E-Mail (1 Tag vorher)
- [ ] Abbuchung funktioniert
- [ ] Bei Rückläufer: Mitglied wird informiert + Status "Zahlung ausstehend"

**E2E Test:**
```javascript
test('SEPA-Zahlung erfolgreich', async ({ page }) => {
  await login(page, 'test-member');
  await page.goto('/payment');
  await page.fill('[name=iban]', 'DE89370400440532013000');
  await page.check('[name=mandate]');
  await page.click('text=Bestätigen');
  await expect(page.locator('.success')).toContainText('Mandat erstellt');
  // Cron-Job simulieren
  await runCron('sepa-collection');
  await expect(await getMemberBalance()).toBeGreaterThan(0);
});
```

---

### Kategorie: Admin-Prozesse

#### US-TEST-004: Mitglieder-Akzeptanz durch Vorstand
**Als** Vorstand  
**möchte ich** Mitglieder akzeptieren oder ablehnen können  
**damit** nur geprüfte Mitglieder aufgenommen werden.

**Akzeptanzkriterien:**
- [ ] Liste der ausstehenden Anträge wird angezeigt
- [ ] Dokumente können eingesehen werden
- [ ] Akzeptieren/Ablehnen mit Begründung
- [ ] Mitglied erhält E-Mail bei Status-Änderung

**E2E Test:**
```javascript
test('Mitglied akzeptieren', async ({ page }) => {
  await loginAsStaff(page, 'vorstand');
  await page.goto('/admin/members/pending');
  await page.click('text=Max Mustermann');
  await page.click('text=Akzeptieren');
  await page.fill('[name=notes]', 'Dokumente OK');
  await page.click('text=Bestätigen');
  await expect(page.locator('.success')).toContainText('Mitglied akzeptiert');
  // E-Mail prüfen
  const email = await getLastEmail('max@example.com');
  await expect(email.subject).toContain('Aufnahme bestätigt');
});
```

---

#### US-TEST-005: Inventar-Eingabe und Abgabe
**Als** Mitarbeiter  
**möchte ich** neue Chargen einpflegen und ausgeben können  
**damit** der Bestand korrekt geführt wird.

**Akzeptanzkriterien:**
- [ ] Neue Charge mit THC/CBD-Werten anlegen
- [ ] Bestand wird automatisch aktualisiert
- [ ] QR-Code-Scan bei Abgabe funktioniert
- [ ] Limit wird bei Abgabe reduziert
- [ ] Quittung wird generiert

**E2E Test:**
```javascript
test('Charge ausgeben', async ({ page }) => {
  await loginAsStaff(page, 'mitarbeiter');
  await page.goto('/inventory');
  await page.click('text=Blue Dream');
  await page.fill('[name=quantity]', '5');
  await page.click('text=Ausgeben');
  // QR-Code scannen simulieren
  await page.fill('[name=member_qr]', 'MEMBER-100001');
  await page.click('text=Bestätigen');
  await expect(page.locator('.receipt')).toBeVisible();
});
```

---

## 🔄 Flow Tests (Kritische End-to-End Prozesse)

### Flow 1: Happy Path - Kompletter Kauf
```gherkin
Gegeben: Mitglied ist eingeloggt und verifiziert
Und: Mitglied hat Guthaben von € 100
Und: Limit ist 0g/25g (Tag) und 10g/50g (Monat)

Wenn: Mitglied geht zu "Bestellen"
Und: Wählt "Blue Dream" (5g, € 40)
Und: Klickt "In den Warenkorb"
Und: Geht zu Kasse
Und: Wählt Zahlung per Guthaben
Und: Bestätigt Bestellung

Dann: Bestellung wird erstellt mit Status "Bezahlt"
Und: Guthaben ist € 60
Und: Limit ist 5g/25g (Tag) und 15g/50g (Monat)
Und: E-Mail-Bestätigung wird gesendet
Und: Reservierung läuft (48h Timer startet)
```

**Playwright Implementierung:**
```javascript
test('Happy Path: Kompletter Kauf', async ({ page }) => {
  // Setup
  const member = await createTestMember({ balance: 100 });
  await login(page, member.email);
  
  // Flow
  await page.goto('/shop');
  await page.locator('[data-product="blue-dream"]').fill('5');
  await page.click('text=In den Warenkorb');
  await page.click('text=Zur Kasse');
  await page.click('text=Mit Guthaben bezahlen');
  await page.click('text=Bestellung bestätigen');
  
  // Assertions
  await expect(page.locator('.order-confirmation')).toBeVisible();
  await expect(await getMemberBalance(member.id)).toBe(60);
  await expect(await getMemberDailyUsage(member.id)).toBe(5);
});
```

---

### Flow 2: Error Path - Limit überschritten
```gherkin
Gegeben: Mitglied hat heute 22g bestellt

Wenn: Mitglied versucht 5g hinzuzufügen (wäre 27g)

Dann: Fehlermeldung wird angezeigt: "Tageslimit überschritten"
Und: Button "Zur Kasse" ist deaktiviert
Und: Mitglied kann nicht bestellen
```

---

### Flow 3: Admin Flow - Verdachtsanzeige
```gherkin
Gegeben: Mitglied "X" hat 52g diesen Monat bestellt

Wenn: System prüft Limits nächtlich
Dann: Verdachtsanzeige wird automatisch generiert
Und: Vorstand erhält Alert-E-Mail
Und: Mitglied wird vorläufig gesperrt

Wenn: Vorstand prüft Fall
Und: Entscheidet "Kein Verdacht"
Dann: Mitglied wird entsperrt
Und: Verdachtsanzeige wird verworfen
```

---

## 💨 Smoke Tests (Schnelle Integritätsprüfung)

### Smoke Test Suite (läuft bei jedem Deploy)

```javascript
// tests/smoke/critical-paths.spec.js
test.describe('Smoke Tests', () => {
  
  test('Homepage lädt', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('body')).toContainText('CSC Administration');
    await expect(page.locator('.loading')).not.toBeVisible();
  });

  test('Login funktioniert', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name=email]', process.env.TEST_USER_EMAIL);
    await page.fill('[name=password]', process.env.TEST_USER_PASSWORD);
    await page.click('text=Anmelden');
    await expect(page).toHaveURL('/dashboard');
  });

  test('Datenbank-Verbindung', async ({ request }) => {
    const response = await request.get('/api/health/db');
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.status).toBe('healthy');
  });

  test('Limits werden berechnet', async ({ request }) => {
    const response = await request.get('/api/test-member/limits');
    const data = await response.json();
    expect(data.daily).toBeDefined();
    expect(data.monthly).toBeDefined();
    expect(data.daily.max).toBe(25);
    expect(data.monthly.max).toBe(50);
  });

  test('E-Mail-Versand funktioniert', async () => {
    const result = await sendTestEmail('test@example.com');
    expect(result.sent).toBe(true);
    expect(result.messageId).toBeDefined();
  });

});
```

**Ausführung:**
```bash
# Smoke Tests (schnell, < 2 Minuten)
pytest tests/smoke/ -v

# Oder mit Playwright
npx playwright test tests/smoke/ --project=chromium
```

---

## 🛠️ MCP + Chrome DevTools Integration

### 1. Chrome DevTools MCP für visuelle Tests

```python
# tests/visual/test_ui_with_cdt.py
import pytest
from playwright.sync_api import sync_playwright

@pytest.mark.visual
def test_dashboard_layout():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Login
        page.goto('http://localhost:8080/login')
        page.fill('#email', 'test@example.com')
        page.fill('#password', 'password')
        page.click('button[type=submit]')
        
        # Dashboard öffnen
        page.goto('http://localhost:8080/dashboard')
        
        # Chrome DevTools öffnen via MCP
        client = page.context.new_cdp_session(page)
        
        # Layout-Shift messen
        metrics = client.send('Performance.getMetrics')
        assert metrics['LayoutShift'] < 0.1  # CLS < 0.1
        
        # Kontrast prüfen (Accessibility)
        axe_results = client.send('Accessibility.getFullAXTree')
        # Analysiere mit axe-core...
        
        # Screenshot für visuelle Regression
        page.screenshot(path='tests/visual/dashboard.png')
        
        browser.close()
```

### 2. MCP für API-Testing

```python
# MCP Context für API-Tests
{
  "mcpServers": {
    "csc-api": {
      "command": "python",
      "args": ["-m", "csc_admin.mcp_server"],
      "env": {
        "DJANGO_SETTINGS_MODULE": "csc_admin.settings.test"
      }
    }
  }
}
```

**Verwendung:**
```python
# Mit MCP direkt auf Models zugreifen
response = mcp_client.call('get_member_limits', {
    'member_id': 12345
})
assert response['daily_used'] == 5
assert response['daily_remaining'] == 20
```

### 3. Automatisierte Lighthouse-Tests

```javascript
// tests/lighthouse/performance.spec.js
const { playAudit } = require('playwright-lighthouse');

test('Lighthouse Performance', async ({ page }) => {
  await page.goto('/dashboard');
  
  await playAudit({
    page: page,
    thresholds: {
      performance: 90,
      accessibility: 100,
      'best-practices': 90,
      seo: 90,
    },
    port: 9222,
  });
});
```

---

## 📊 Test-Daten (Fixtures)

```python
# conftest.py
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def test_member(db):
    """Standard-Testmitglied"""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Max',
        last_name='Test'
    )
    user.profile.member_number = '100001'
    user.profile.balance = 100.00
    user.profile.is_verified = True
    user.profile.save()
    return user

@pytest.fixture
def test_staff(db):
    """Vorstand-Testuser"""
    user = User.objects.create_user(
        email='vorstand@example.com',
        password='testpass123',
        is_staff=True
    )
    return user

@pytest.fixture
def test_strain(db):
    """Test-Sorte"""
    return Strain.objects.create(
        name='Blue Dream',
        thc_content=18.5,
        cbd_content=0.2,
        price_per_gram=8.50,
        stock_grams=500
    )
```

---

## 🚀 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  smoke-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Smoke Tests
        run: |
          docker-compose up -d
          pytest tests/smoke/ -v --tb=short
          
  e2e-tests:
    runs-on: ubuntu-latest
    needs: smoke-tests
    steps:
      - uses: actions/checkout@v3
      - name: Install Playwright
        run: |
          npm install -g @playwright/test
          npx playwright install chromium
      - name: Run E2E Tests
        run: |
          docker-compose up -d
          npx playwright test tests/e2e/ --project=chromium
      - name: Upload Test Results
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
          
  visual-tests:
    runs-on: ubuntu-latest
    needs: smoke-tests
    steps:
      - uses: actions/checkout@v3
      - name: Run Visual Tests
        run: |
          pip install pytest-playwright
          pytest tests/visual/ --browser chromium
```

---

## 📈 Test-Metriken

| Metrik | Ziel | Aktuell |
|--------|------|---------|
| Code Coverage | > 80% | - |
| E2E Test Success Rate | > 95% | - |
| Smoke Test Duration | < 2 min | - |
| Visual Regression | 0 | - |
| Critical Bugs | 0 | - |

---

**Nächste Schritte:**
1. [ ] Playwright installieren
2. [ ] Baseline-Screenshots erstellen
3. [ ] MCP Server für Django aufsetzen
4. [ ] CI/CD Pipeline konfigurieren
