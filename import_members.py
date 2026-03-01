#!/usr/bin/env python3
"""
CSC Member Import Script
Importiert Mitgliederdaten aus CSV in die SQLite-Datenbank
"""

import sqlite3
import csv
from datetime import datetime, timedelta
import re
import sys
import os
import json

class CSVToDatabaseImporter:
    def __init__(self, db_path='csc_database.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.stats = {
            'processed': 0,
            'imported': 0,
            'errors': 0,
            'skipped': 0
        }
        
    def connect(self):
        """Verbindung zur Datenbank herstellen"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"✓ Datenbank verbunden: {self.db_path}")
        
    def init_database(self):
        """Datenbank-Schema initialisieren"""
        schema_path = os.path.join(os.path.dirname(__file__), 'database_schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
            self.cursor.executescript(schema)
            self.conn.commit()
            print("✓ Datenbank-Schema erstellt")
        else:
            print(f"⚠️  Schema-Datei nicht gefunden: {schema_path}")
            
    def parse_date(self, date_str):
        """Konvertiert Datumsstring zu Python datetime"""
        if not date_str or date_str.strip() == '':
            return None
        try:
            # Versuche verschiedene Formate
            formats = ['%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%d/%m/%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except:
                    continue
            return None
        except:
            return None
            
    def parse_bool(self, value):
        """Konvertiert zu Boolean"""
        if not value:
            return False
        return str(value).strip().lower() in ['1', 'true', 'yes', 'ja', 'wahr']
        
    def clean_iban(self, iban):
        """Bereinigt IBAN (entfernt Leerzeichen)"""
        if not iban:
            return None
        return re.sub(r'\s+', '', str(iban).upper())
        
    def clean_phone(self, phone):
        """Bereinigt Telefonnummer"""
        if not phone:
            return None
        cleaned = re.sub(r'[^\d+]', '', str(phone))
        return cleaned if cleaned else None
        
    def import_member(self, data):
        """Importiert ein einzelnes Mitglied"""
        try:
            self.stats['processed'] += 1
            
            # Pflichtfelder prüfen
            email = data.get('email', '').strip()
            if not email:
                print(f"  ⚠️  Überspringe Zeile {self.stats['processed']}: Keine E-Mail")
                self.stats['skipped'] += 1
                return
                
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            if not first_name or not last_name:
                print(f"  ⚠️  Überspringe {email}: Kein Name")
                self.stats['skipped'] += 1
                return
                
            # Mitgliedsnummer
            member_num = data.get('member_number', '')
            try:
                member_number = int(float(member_num)) if member_num else None
            except:
                member_number = None
                
            if not member_number:
                print(f"  ⚠️  Überspringe {email}: Keine Mitgliedsnummer")
                self.stats['skipped'] += 1
                return
                
            # Prüfe ob Mitglied bereits existiert
            self.cursor.execute(
                "SELECT id FROM members WHERE member_number = ? OR email = ?",
                (member_number, email)
            )
            if self.cursor.fetchone():
                print(f"  ⚠️  Mitglied existiert bereits: {member_number} / {email}")
                self.stats['skipped'] += 1
                return
                
            # Daten konvertieren
            birth_date = self.parse_date(data.get('birth_date', ''))
            join_date = self.parse_date(data.get('join_date', ''))
            application_date = self.parse_date(data.get('application_date', ''))
            
            # Adresse
            street = data.get('street', '').strip()
            zip_code = data.get('zip_code', '').strip()
            city = data.get('city', '').strip()
            
            # Telefon
            phone = self.clean_phone(data.get('phone', ''))
            
            # Limits
            try:
                monthly_limit = int(float(data.get('monthly_limit', 50)))
            except:
                monthly_limit = 50
                
            try:
                daily_limit = int(float(data.get('daily_limit', 25)))
            except:
                daily_limit = 25
                
            # Guthaben
            try:
                balance = float(data.get('balance', 0))
            except:
                balance = 0.0
                
            # Consent/Status
            privacy_consent = self.parse_bool(data.get('privacy_consent', ''))
            sepa_consent = self.parse_bool(data.get('sepa_consent', ''))
            age_verified = self.parse_bool(data.get('age_verified', ''))
            residence_verified = self.parse_bool(data.get('residence_verified', ''))
            no_other_club = self.parse_bool(data.get('no_other_club', ''))
            newsletter_important = self.parse_bool(data.get('newsletter_important', ''))
            newsletter_optional = self.parse_bool(data.get('newsletter_optional', ''))
            
            is_accepted = self.parse_bool(data.get('is_accepted', ''))
            is_verified = self.parse_bool(data.get('is_verified', ''))
            
            payment_status = data.get('payment_status', 'pending').strip().lower()
            if payment_status not in ['pending', 'paid', 'failed']:
                payment_status = 'pending'
            
            # Mitglied einfügen
            self.cursor.execute("""
                INSERT INTO members (
                    member_number, first_name, last_name, birth_date, email, phone,
                    street, zip_code, city, join_date, application_date,
                    monthly_limit, daily_limit, status, is_verified, is_accepted,
                    payment_status, balance, privacy_consent, sepa_consent,
                    age_verified, residence_verified, no_other_club,
                    newsletter_important, newsletter_optional
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                member_number, first_name, last_name, birth_date, email, phone,
                street, zip_code, city, join_date, application_date,
                monthly_limit, daily_limit, 'active', is_verified, is_accepted,
                payment_status, balance, privacy_consent, sepa_consent,
                age_verified, residence_verified, no_other_club,
                newsletter_important, newsletter_optional
            ))
            
            member_id = self.cursor.lastrowid
            
            # Bankdaten einfügen (separate Tabelle)
            iban = self.clean_iban(data.get('iban', ''))
            if iban:
                bic = data.get('bic', '').strip() or None
                bank_name = data.get('bank_name', '').strip() or None
                
                self.cursor.execute("""
                    INSERT INTO member_bank_details (
                        member_id, iban, bic, bank_name, account_holder, sepa_mandate_active
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (member_id, iban, bic, bank_name, f"{first_name} {last_name}", sepa_consent))
                
            self.conn.commit()
            self.stats['imported'] += 1
            
            if self.stats['imported'] % 10 == 0:
                print(f"  ✓ {self.stats['imported']} Mitglieder importiert...")
                
        except Exception as e:
            self.stats['errors'] += 1
            print(f"  ❌ Fehler bei {data.get('email', 'unbekannt')}: {str(e)}")
            self.conn.rollback()
            
    def import_from_csv(self, csv_path):
        """Hauptfunktion: Importiert alle Daten aus CSV"""
        print("=" * 60)
        print("CSC MITGLIEDER IMPORT (CSV)")
        print("=" * 60)
        
        if not os.path.exists(csv_path):
            print(f"❌ Datei nicht gefunden: {csv_path}")
            return False
        
        # Datenbank vorbereiten
        self.connect()
        
        # Prüfe ob Schema existiert
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='members'")
        if not self.cursor.fetchone():
            print("\n🗄️  Initialisiere Datenbank...")
            self.init_database()
        
        # CSV einlesen
        print(f"\n📖 Lese CSV-Datei: {csv_path}")
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            print(f"❌ Fehler beim Lesen der CSV: {e}")
            return False
            
        if not rows:
            print("⚠️  Keine Daten zum Importieren gefunden")
            return False
            
        print(f"✓ {len(rows)} Datensätze gefunden")
        print(f"\n📥 Starte Import...\n")
        
        for data in rows:
            self.import_member(data)
            
        # Zusammenfassung
        print("\n" + "=" * 60)
        print("IMPORT-ZUSAMMENFASSUNG")
        print("=" * 60)
        print(f"Verarbeitet:     {self.stats['processed']:>4}")
        print(f"Importiert:      {self.stats['imported']:>4} ✅")
        print(f"Übersprungen:    {self.stats['skipped']:>4} ⚠️")
        print(f"Fehler:          {self.stats['errors']:>4} ❌")
        print("=" * 60)
        
        self.conn.close()
        print(f"\n✓ Import abgeschlossen!")
        print(f"  Datenbank: {os.path.abspath(self.db_path)}")
        
        return self.stats['errors'] == 0
        
    def export_to_csv(self, output_path='members_export.csv'):
        """Exportiert Mitglieder als CSV"""
        self.connect()
        self.cursor.execute("""
            SELECT 
                member_number, first_name, last_name, email, phone,
                street, zip_code, city, birth_date, join_date,
                monthly_limit, daily_limit, status, balance
            FROM members
            ORDER BY member_number
        """)
        
        rows = self.cursor.fetchall()
        headers = [description[0] for description in self.cursor.description]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
            
        print(f"✓ CSV exportiert: {output_path} ({len(rows)} Einträge)")
        self.conn.close()


def main():
    """Hauptprogramm"""
    if len(sys.argv) < 2:
        print("Verwendung:")
        print(f"  {sys.argv[0]} import <datei.csv> [datenbank.db]")
        print(f"  {sys.argv[0]} export [datenbank.db] [output.csv]")
        print()
        print("Beispiele:")
        print(f"  {sys.argv[0]} import seed_data/members.csv")
        print(f"  {sys.argv[0]} import seed_data/members.csv meine_csc.db")
        print(f"  {sys.argv[0]} export meine_csc.db backup.csv")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == 'import':
        if len(sys.argv) < 3:
            print("❌ Bitte CSV-Datei angeben")
            sys.exit(1)
            
        csv_file = sys.argv[2]
        db_file = sys.argv[3] if len(sys.argv) > 3 else 'csc_database.db'
        
        if not os.path.exists(csv_file):
            print(f"❌ Datei nicht gefunden: {csv_file}")
            sys.exit(1)
            
        importer = CSVToDatabaseImporter(db_file)
        success = importer.import_from_csv(csv_file)
        sys.exit(0 if success else 1)
        
    elif command == 'export':
        db_file = sys.argv[2] if len(sys.argv) > 2 else 'csc_database.db'
        csv_file = sys.argv[3] if len(sys.argv) > 3 else 'members_export.csv'
        
        if not os.path.exists(db_file):
            print(f"❌ Datenbank nicht gefunden: {db_file}")
            sys.exit(1)
            
        importer = CSVToDatabaseImporter(db_file)
        importer.export_to_csv(csv_file)
        
    else:
        print(f"❌ Unbekannter Befehl: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()