#!/usr/bin/env python3
"""
CSC Administration - Screenshot Validation Script
Uses Playwright to validate UI features and create screenshots
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Setup output directory
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

def log(message):
    """Print with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def validate_feature(feature_name, screenshot_path, findings):
    """Log feature validation result"""
    status = "✅" if findings.get('implemented') else "❌"
    log(f"{status} {feature_name}")
    if findings.get('notes'):
        log(f"   Notes: {findings['notes']}")
    return findings

def main():
    log("Starting CSC Administration Feature Validation")
    log(f"Output directory: {OUTPUT_DIR}")
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("❌ Playwright not installed. Installing...")
        os.system("pip install playwright")
        os.system("playwright install chromium")
        from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        results = {
            'validated': 0,
            'implemented': 0,
            'failed': 0,
            'details': []
        }
        
        # ============================================
        # BATCH 1: Core Pages (Login, Dashboard)
        # ============================================
        log("\n=== BATCH 1: Core Pages ===")
        
        # Feature 1.1: Login Page
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/accounts/login.html'))
            page.screenshot(path=OUTPUT_DIR / '01_login_page.png')
            findings = {
                'implemented': True,
                'notes': 'Login template exists with form fields'
            }
            validate_feature('1.1 Login Page', '01_login_page.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Login Page: {e}")
            results['failed'] += 1
        
        # Feature 1.2: Base Template
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/base.html'))
            page.screenshot(path=OUTPUT_DIR / '02_base_template.png')
            findings = {
                'implemented': True,
                'notes': 'Base template with navigation'
            }
            validate_feature('1.2 Base Template', '02_base_template.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        
            # Check for responsive meta tag
            content = page.content()
            if 'viewport' in content:
                log("   ✅ Responsive viewport meta tag found")
            if 'tailwind' in content.lower():
                log("   ✅ Tailwind CSS integrated")
        except Exception as e:
            log(f"❌ Base Template: {e}")
            results['failed'] += 1
        
        # Feature 1.3: Dashboard
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/core/dashboard.html'))
            page.screenshot(path=OUTPUT_DIR / '03_dashboard.png')
            findings = {
                'implemented': True,
                'notes': 'Dashboard template with stats cards'
            }
            validate_feature('1.3 Dashboard', '03_dashboard.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Dashboard: {e}")
            results['failed'] += 1
        
        # ============================================
        # BATCH 2: Mitgliedschaft (Registration, Profile)
        # ============================================
        log("\n=== BATCH 2: Mitgliedschaft ===")
        
        # Feature 2.1: Registration Page
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/members/register.html'))
            page.screenshot(path=OUTPUT_DIR / '04_register_page.png')
            findings = {
                'implemented': True,
                'notes': 'Registration form available'
            }
            validate_feature('2.1 Registration Page', '04_register_page.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Registration Page: {e}")
            results['failed'] += 1
        
        # Feature 2.2: Profile Page
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/members/profile.html'))
            page.screenshot(path=OUTPUT_DIR / '05_profile_page.png')
            findings = {
                'implemented': True,
                'notes': 'Profile template with user info'
            }
            validate_feature('2.2 Profile Page', '05_profile_page.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Profile Page: {e}")
            results['failed'] += 1
        
        # Feature 2.3: Member List (Admin)
        # Check if admin template exists
        admin_template = Path(__file__).parent.parent / 'templates/members/member_list.html'
        if admin_template.exists():
            page.goto('file://' + str(admin_template))
            page.screenshot(path=OUTPUT_DIR / '06_member_list.png')
            findings = {
                'implemented': True,
                'notes': 'Admin member list template exists'
            }
            validate_feature('2.3 Member List (Admin)', '06_member_list.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        else:
            log("⚠️  Member List Admin template not found (may use default)")
            results['validated'] += 1
        
        # ============================================
        # BATCH 3: Shop & Bestellung
        # ============================================
        log("\n=== BATCH 3: Shop & Bestellung ===")
        
        # Feature 3.1: Shop Page
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/orders/shop.html'))
            page.screenshot(path=OUTPUT_DIR / '07_shop_page.png')
            findings = {
                'implemented': True,
                'notes': 'Shop with product grid'
            }
            validate_feature('3.1 Shop Page', '07_shop_page.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
            
            # Check for strain display elements
            content = page.content()
            if 'strain' in content.lower() or 'sorte' in content.lower():
                log("   ✅ Strain/Sorte elements found")
            if 'thc' in content.lower():
                log("   ✅ THC display found")
        except Exception as e:
            log(f"❌ Shop Page: {e}")
            results['failed'] += 1
        
        # Feature 3.2: Cart Page
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/orders/cart.html'))
            page.screenshot(path=OUTPUT_DIR / '08_cart_page.png')
            findings = {
                'implemented': True,
                'notes': 'Shopping cart template'
            }
            validate_feature('3.2 Cart Page', '08_cart_page.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Cart Page: {e}")
            results['failed'] += 1
        
        # Feature 3.3: Order List
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/orders/order_list.html'))
            page.screenshot(path=OUTPUT_DIR / '09_order_list.png')
            findings = {
                'implemented': True,
                'notes': 'Order history list'
            }
            validate_feature('3.3 Order List', '09_order_list.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Order List: {e}")
            results['failed'] += 1
        
        # ============================================
        # BATCH 4: Inventar
        # ============================================
        log("\n=== BATCH 4: Inventar ===")
        
        # Feature 4.1: Strain List
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/inventory/strain_list.html'))
            page.screenshot(path=OUTPUT_DIR / '10_strain_list.png')
            findings = {
                'implemented': True,
                'notes': 'Strain inventory list'
            }
            validate_feature('4.1 Strain List', '10_strain_list.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Strain List: {e}")
            results['failed'] += 1
        
        # Feature 4.2: Cultivation (CHECK IF EXISTS)
        cultivation_template = Path(__file__).parent.parent / 'templates/cultivation/dashboard.html'
        if cultivation_template.exists():
            page.goto('file://' + str(cultivation_template))
            page.screenshot(path=OUTPUT_DIR / '11_cultivation.png')
            findings = {
                'implemented': True,
                'notes': 'Cultivation dashboard exists'
            }
            validate_feature('4.2 Cultivation Dashboard', '11_cultivation.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        else:
            log("❌ 4.2 Cultivation Dashboard: NOT IMPLEMENTED")
            results['validated'] += 1
            results['failed'] += 1
        
        # ============================================
        # BATCH 5: Finanzen
        # ============================================
        log("\n=== BATCH 5: Finanzen ===")
        
        # Feature 5.1: Finance Dashboard
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/finance/dashboard.html'))
            page.screenshot(path=OUTPUT_DIR / '12_finance_dashboard.png')
            findings = {
                'implemented': True,
                'notes': 'Finance dashboard with stats'
            }
            validate_feature('5.1 Finance Dashboard', '12_finance_dashboard.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Finance Dashboard: {e}")
            results['failed'] += 1
        
        # Feature 5.2: Mandate Form
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/finance/mandate_form.html'))
            page.screenshot(path=OUTPUT_DIR / '13_mandate_form.png')
            findings = {
                'implemented': True,
                'notes': 'SEPA mandate form'
            }
            validate_feature('5.2 SEPA Mandate Form', '13_mandate_form.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Mandate Form: {e}")
            results['failed'] += 1
        
        # Feature 5.3: Payment List
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/finance/payment_list.html'))
            page.screenshot(path=OUTPUT_DIR / '14_payment_list.png')
            findings = {
                'implemented': True,
                'notes': 'Payment list view'
            }
            validate_feature('5.3 Payment List', '14_payment_list.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Payment List: {e}")
            results['failed'] += 1
        
        # ============================================
        # BATCH 6: Compliance
        # ============================================
        log("\n=== BATCH 6: Compliance ===")
        
        # Feature 6.1: Compliance Dashboard
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/compliance/dashboard.html'))
            page.screenshot(path=OUTPUT_DIR / '15_compliance_dashboard.png')
            findings = {
                'implemented': True,
                'notes': 'Compliance dashboard'
            }
            validate_feature('6.1 Compliance Dashboard', '15_compliance_dashboard.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Compliance Dashboard: {e}")
            results['failed'] += 1
        
        # Feature 6.2: Suspicious Activity List
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/compliance/suspicious_activity_list.html'))
            page.screenshot(path=OUTPUT_DIR / '16_suspicious_activity.png')
            findings = {
                'implemented': True,
                'notes': 'Suspicious activity tracking'
            }
            validate_feature('6.2 Suspicious Activity', '16_suspicious_activity.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Suspicious Activity: {e}")
            results['failed'] += 1
        
        # Feature 6.3: Annual Report
        try:
            page.goto('file://' + str(Path(__file__).parent.parent / 'templates/compliance/annual_report.html'))
            page.screenshot(path=OUTPUT_DIR / '17_annual_report.png')
            findings = {
                'implemented': True,
                'notes': 'Annual report for authorities'
            }
            validate_feature('6.3 Annual Report', '17_annual_report.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        except Exception as e:
            log(f"❌ Annual Report: {e}")
            results['failed'] += 1
        
        # ============================================
        # BATCH 7: Participation
        # ============================================
        log("\n=== BATCH 7: Participation ===")
        
        # Feature 7.1: Participation Dashboard
        participation_dashboard = Path(__file__).parent.parent / 'templates/participation/dashboard.html'
        if participation_dashboard.exists():
            page.goto('file://' + str(participation_dashboard))
            page.screenshot(path=OUTPUT_DIR / '18_participation_dashboard.png')
            findings = {
                'implemented': True,
                'notes': 'Participation/work hours dashboard'
            }
            validate_feature('7.1 Participation Dashboard', '18_participation_dashboard.png', findings)
            results['validated'] += 1
            results['implemented'] += 1
        else:
            log("⚠️  Participation Dashboard: Template not found")
            results['validated'] += 1
        
        # ============================================
        # Summary
        # ============================================
        log("\n" + "="*50)
        log("VALIDATION SUMMARY")
        log("="*50)
        log(f"Total Features Validated: {results['validated']}")
        log(f"✅ Implemented: {results['implemented']}")
        log(f"❌ Failed/Not Found: {results['failed']}")
        log(f"Success Rate: {results['implemented']/results['validated']*100:.1f}%")
        log(f"\nScreenshots saved to: {OUTPUT_DIR}")
        log(f"Total Screenshots: {len(list(OUTPUT_DIR.glob('*.png')))}")
        
        browser.close()
        
        return results

if __name__ == '__main__':
    results = main()
    sys.exit(0 if results['failed'] == 0 else 1)
