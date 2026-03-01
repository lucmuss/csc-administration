# Seed Data

This directory contains seed data for the CSC Admin System development and testing.

## Files

### members.csv
Member data with 55+ entries. Contains all fields required for the member management system.

**Fields:**
- member_number (unique ID)
- first_name, last_name
- email, phone
- birth_date (YYYY-MM-DD)
- street, zip_code, city
- join_date, application_date
- monthly_limit (default: 50g)
- daily_limit (default: 25g)
- balance (account balance)
- status (active/pending/suspended)
- is_verified, is_accepted (0/1)
- payment_status (pending/paid/failed)
- Various consent fields (0/1)
- iban, bic, bank_name

### strains.csv
Available cannabis strains (8 flowers + 8 clones).

**Fields:**
- id
- name (strain name)
- type (flower/clone)
- category (bluete/steckling)
- price_per_gram
- availability (current stock)
- thc_content, cbd_content (optional)
- description
- is_active (0/1)

## Usage

### Import to Database

```bash
# Import members
python3 ../import_members.py import members.csv

# Import strains (if separate script exists)
python3 import_strains.py strains.csv
```

### CSV Format Notes

- Dates: YYYY-MM-DD format
- Boolean: 0 = false, 1 = true  
- Prices: Decimal with dot (8.50)
- Empty values: left blank
- Encoding: UTF-8

## Data Privacy

⚠️ **IMPORTANT**: This data is for development/testing only.
- Based on real member structures but anonymized
- Use only for local development
- Never commit real member data to version control
- Protect production data according to DSGVO/GDPR

## Updates

When data structure changes:
1. Update CSV headers
2. Update import scripts
3. Update this README
4. Test import with sample data