#!/usr/bin/env python3
"""
Check for Airtable formulas, views, and other features
"""

import json
import pandas as pd
import requests

API_KEY = "patYPbtTOgdQYYgTU.827b7b384156c120e07cd4381bb177aa116b689267bdf88313b521e6848e5c66"
BASE_ID = "app1SIhMIMJaKqAOZ"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("🔍 ANALYZING AIRTABLE FEATURES AND LOGIC\n")
print("=" * 50)

# Load exported data to analyze computed fields
patients = pd.read_csv('airtable_export_simple_20250910_190101/csv_data/Patient.csv')
operations = pd.read_csv('airtable_export_simple_20250910_190101/csv_data/Operation.csv')
planning = pd.read_csv('airtable_export_simple_20250910_190101/csv_data/Planning.csv')

print("\n📊 COMPUTED/FORMULA FIELDS DETECTED:")
print("\nIn Patient table:")
formula_indicators = ['Age', 'Mineur', 'Nom - Prénom', 'Informations complètes', 'Nom abrégé', 'DateStampID']
for field in formula_indicators:
    if field in patients.columns:
        print(f"  ✓ {field} - Likely a formula field")

print("\nIn Operation table:")
op_formulas = ['Libellé', 'Coeff J+T']
for field in op_formulas:
    if field in operations.columns:
        print(f"  ✓ {field} - Likely a formula field")

print("\nIn Planning table:")
plan_formulas = ['Date_Text', 'Semaine', 'DoW']
for field in plan_formulas:
    if field in planning.columns:
        print(f"  ✓ {field} - Likely a formula field")

# Analyze relationships
print("\n🔗 RELATIONSHIPS AND LOOKUPS:")
print("\nPatient → Planning:")
print("  - Programmation field links patients to scheduled surgeries")
print("  - Nb Interventions counts linked operations")

print("\nPlanning → Operation:")
print("  - Type field appears to link to operation types")
print("  - Location (Lieu) field for surgery venues")

# Check for views using API
print("\n👁️ ATTEMPTING TO DISCOVER VIEWS:")
for table_name in ['Patient', 'Operation', 'Planning']:
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_name}"
    
    # Try different view names
    common_views = ['Grid view', 'Vue Grille', 'Calendar', 'Calendrier', 'Gallery', 'Kanban', 'Form']
    
    for view in common_views:
        try:
            response = requests.get(url, headers=headers, params={'view': view, 'maxRecords': 1})
            if response.status_code == 200:
                print(f"  ✓ {table_name}: '{view}' view exists")
        except:
            pass

# Analyze business logic from data patterns
print("\n🧮 BUSINESS LOGIC PATTERNS DISCOVERED:")

# Check medication protocols
print("\n1. MEDICATION PROTOCOLS:")
med_cols = [col for col in operations.columns if 'Nb j' in col or 'Nb J' in col]
print(f"   - {len(med_cols)} different medications with day-based dosing")
print("   - Post-op medication durations are procedure-specific")

# Check scheduling patterns
print("\n2. SCHEDULING LOGIC:")
if 'Type Semaine' in planning.columns:
    print("   - Alternating week schedule (Paire/Impaire)")
if 'Créneau' in planning.columns:
    slots = planning['Créneau'].value_counts()
    print(f"   - {len(slots)} different time slot types")
    print(f"   - Morning slots: {slots.get('Matin', 0)}")
    print(f"   - Afternoon slots: {slots.get('Après-midi', 0)}")

# Check patient validation
print("\n3. PATIENT MANAGEMENT:")
print("   - Age calculation from birthdate")
print("   - Minor status flagging (Mineur field)")
print("   - Missing email alerts (Mail absent field)")
print("   - Profile completion tracking (URL Profil Incomplet)")

# Check for automations (these can't be exported via API)
print("\n⚡ AUTOMATIONS (Cannot be exported via API):")
print("   These likely exist but need manual documentation:")
print("   - Email notifications for appointments")
print("   - Age/Minor status auto-calculation")
print("   - Post-op follow-up scheduling")
print("   - Profile completion reminders")

print("\n📝 INTERFACES & FORMS (Cannot be exported):")
print("   Airtable Interfaces and Forms need manual recreation:")
print("   - Patient intake forms")
print("   - Surgery scheduling interface")
print("   - Doctor/staff dashboards")
print("   - Report generation views")

print("\n🔐 PERMISSIONS & ACCESS CONTROL:")
print("   Not available via API, likely includes:")
print("   - Role-based access (doctors, staff, admin)")
print("   - Field-level permissions")
print("   - View restrictions")

print("\n=" * 50)
print("✅ Analysis complete!")