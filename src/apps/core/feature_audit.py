FEATURE_AUDIT_GROUPS = [
    {
        "title": "Mitglieder & Rollen",
        "summary": "Registrierung, Rollenmodell und operative Mitgliederverwaltung fuer Vorstand und Mitarbeitende.",
        "items": [
            {"name": "Bootstrap des ersten Vorstandsaccounts", "status": "implemented"},
            {"name": "Mitgliederverzeichnis mit Suche, Statusfiltern und CSV-Export", "status": "implemented"},
            {"name": "Mitgliederprofil und Limits im Self-Service", "status": "implemented"},
            {"name": "Mehrstufiger Bewerbungsworkflow mit Dokumentennachforderung", "status": "partial"},
            {"name": "Digitale Mitgliedsausweise und QR-Ausgabe", "status": "implemented"},
        ],
    },
    {
        "title": "Shop, Abgabe & Limits",
        "summary": "Mitgliedershop, Reservierung, harte Tages-/Monatslimits und Quittungsgrundlage.",
        "items": [
            {"name": "Sortenkatalog, Warenkorb und Checkout", "status": "implemented"},
            {"name": "Tageslimit 25g und Monatslimit 50g inkl. Datenbank-Constraint", "status": "implemented"},
            {"name": "48h Reservierungslogik und Bestellhistorie", "status": "implemented"},
            {"name": "Rueckgaengigmachen von Ausgaben aus dem Admin-Interface", "status": "partial"},
            {"name": "POS-Flow mit Ausweis-/QR-Scan", "status": "planned"},
        ],
    },
    {
        "title": "Anbau & Inventar",
        "summary": "Seed-to-sale-Bestand mit Grow Cycles, Pflanzen, Harvest Batches und Lagerorten.",
        "items": [
            {"name": "Grow Cycles, Pflanzen, Plant Logs und Harvest Batches", "status": "implemented"},
            {"name": "Lagerorte, Inventuren und Bestandsverschiebungen", "status": "implemented"},
            {"name": "Niedrigbestand-Warnungen im Cockpit", "status": "implemented"},
            {"name": "Equipment-/Raumplanung", "status": "partial"},
            {"name": "Vernichtungs- und Transportnachweise", "status": "implemented"},
        ],
    },
    {
        "title": "Finanzen & Forderungen",
        "summary": "SEPA, Mahnlogik, DATEV-Export und offener Zahlungsbestand fuer den Vorstand.",
        "items": [
            {"name": "SEPA-Mandate, Vorabankuendigung und Einzug", "status": "implemented"},
            {"name": "Rechnungen, Zahlungen und Mahnstufen", "status": "implemented"},
            {"name": "DATEV-Export ueber konfigurierbaren Exportpfad", "status": "implemented"},
            {"name": "GoBD-festes Kassenbuch", "status": "partial"},
            {"name": "Sammelueberweisungen und Lastschriftlauf-UI", "status": "planned"},
        ],
    },
    {
        "title": "Compliance & Vorstandsbetrieb",
        "summary": "Verdachtsfaelle, Jahresberichte, Schichten und operative Vorstandsaufgaben.",
        "items": [
            {"name": "Compliance-Berichte und offene Verdachtsfaelle", "status": "implemented"},
            {"name": "Vorstands-Cockpit mit Aufgaben, Risiken und Schnellaktionen", "status": "implemented"},
            {"name": "Arbeitsstunden und Schichtplanung", "status": "implemented"},
            {"name": "Automatisierte Einladungen und Erinnerungen fuer Vereinsbetrieb", "status": "implemented"},
            {"name": "Aufgabenboard fuer Vorstand und Mitarbeitende", "status": "implemented"},
            {"name": "Mitgliederversammlungen mit Agenda, Protokoll und Beschlusshistorie", "status": "implemented"},
            {"name": "Unveraenderbarer Audit-Trail fuer alle Admin-Aktionen", "status": "implemented"},
        ],
    },
    {
        "title": "Kommunikation & UX",
        "summary": "Massenkommunikation, lokale Assets, Health-Checks und UI fuer Desktop und Mobile.",
        "items": [
            {"name": "Massen-E-Mails, SMS, Vorlagen und Provider-Management", "status": "implemented"},
            {"name": "Lokales CSS/JS ohne externe Build-Pflicht im Laufzeitcontainer", "status": "implemented"},
            {"name": "Health- und Readiness-Endpunkte", "status": "implemented"},
            {"name": "PWA-Basis, Offline-Seite und Consent-Banner", "status": "implemented"},
            {"name": "CSP, 2FA und formale Accessibility-Regressionstests", "status": "partial"},
        ],
    },
    {
        "title": "Integrationen & Exporte",
        "summary": "API-Exports, Webhooks und externe Anbindungen fuer Finanz- und Betriebsprozesse.",
        "items": [
            {"name": "API-Endpunkte fuer Mitglieder, Rechnungen, Aufgaben und Nachweise", "status": "implemented"},
            {"name": "Konfigurierbare Webhooks mit Zustellprotokoll", "status": "implemented"},
            {"name": "Drucker- und Buchhaltungsanbindungen ueber API-Key / Webhook", "status": "implemented"},
            {"name": "Bidirektionale Sync-Strategien mit Konfliktmanagement", "status": "planned"},
        ],
    },
]

RECOMMENDED_FEATURES = [
    "2FA fuer Vorstandskonten und verpflichtende Re-Authentifizierung bei kritischen Aktionen.",
    "GoBD-konformes Kassenbuch mit revisionssicherem Export- und Beleg-Workflow.",
    "Bewerbungsworkflow mit Dokumentenpruefung, Rueckfragen und Wiedervorlage.",
    "Bidirektionale Buchhaltungssynchronisation mit Fehlerqueue und Wiederholungslauf.",
    "POS-Flow fuer Ausgabe mit QR-Scan, Unterschrift und Etikettendruck.",
    "Rollenbasierte Benachrichtigungen fuer ueberfaellige Aufgaben, Nachweise und auslaufende Karten.",
]


def feature_audit_summary():
    counts = {"implemented": 0, "partial": 0, "planned": 0}
    for group in FEATURE_AUDIT_GROUPS:
        for item in group["items"]:
            counts[item["status"]] += 1
    counts["total"] = sum(counts.values())
    return counts
