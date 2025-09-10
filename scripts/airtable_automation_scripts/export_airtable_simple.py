#!/usr/bin/env python3
"""
Simple Airtable Exporter - Works without schema API permissions
Export table data when you know the table names
"""

import os
import json
import pandas as pd
from datetime import datetime
import requests
import sys

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

API_KEY = "patYPbtTOgdQYYgTU.827b7b384156c120e07cd4381bb177aa116b689267bdf88313b521e6848e5c66"
BASE_ID = "app1SIhMIMJaKqAOZ"

# TABLE NAMES - Add your actual table names here
# You can find these in your Airtable base interface
TABLE_NAMES = [
    # Add your table names like this:
    # "Patients",
    # "Surgeries", 
    # "Doctors",
    # etc.
]

# ============================================================================
# SIMPLE EXPORT SCRIPT
# ============================================================================

class SimpleAirtableExporter:
    def __init__(self, api_key, base_id, table_names):
        self.api_key = api_key
        self.base_id = base_id
        self.table_names = table_names
        self.export_dir = f"airtable_export_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def setup_export_directory(self):
        """Create export directory structure"""
        dirs = [
            self.export_dir,
            f"{self.export_dir}/csv_data",
            f"{self.export_dir}/json_data",
            f"{self.export_dir}/logs"
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
        print(f"✓ Created export directory: {self.export_dir}/")
    
    def discover_tables(self):
        """Try to discover table names from the base"""
        print("🔍 Attempting to discover tables...")
        
        # Common table name patterns to try
        common_names = [
            "Patients", "Patient", "Chirurgies", "Chirurgie", "Surgery", "Surgeries",
            "Doctors", "Doctor", "Medecins", "Medecin", "Staff", "Personnel",
            "Interventions", "Intervention", "Operations", "Operation",
            "Rendez-vous", "Appointments", "Planning", "Schedule",
            "Equipment", "Equipement", "Materials", "Materiaux",
            "Notes", "Comments", "Observations", "Rapports", "Reports"
        ]
        
        discovered_tables = []
        
        for table_name in common_names:
            try:
                url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"
                response = requests.get(url, headers=self.headers, params={"maxRecords": 1})
                
                if response.status_code == 200:
                    discovered_tables.append(table_name)
                    print(f"  ✅ Found table: {table_name}")
                elif response.status_code == 404:
                    continue  # Table doesn't exist
                else:
                    print(f"  ⚠ Error checking {table_name}: {response.status_code}")
                    
            except Exception as e:
                print(f"  ⚠ Error checking {table_name}: {e}")
        
        return discovered_tables
    
    def get_table_records(self, table_name):
        """Fetch all records from a specific table"""
        print(f"  📊 Exporting: {table_name}")
        all_records = []
        offset = None
        
        while True:
            url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"
            params = {"pageSize": 100}
            if offset:
                params['offset'] = offset
                
            try:
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    records = data.get('records', [])
                    all_records.extend(records)
                    
                    # Check if there are more pages
                    offset = data.get('offset')
                    if not offset:
                        break
                        
                elif response.status_code == 404:
                    print(f"    ❌ Table '{table_name}' not found")
                    return []
                else:
                    print(f"    ⚠ Error: {response.status_code} - {response.text}")
                    break
                    
            except Exception as e:
                print(f"    ❌ Error fetching records: {e}")
                break
                
        return all_records
    
    def export_table_data(self, table_name):
        """Export a table's data to CSV and JSON"""
        records = self.get_table_records(table_name)
        
        if records:
            # Save as JSON (raw format)
            json_path = f"{self.export_dir}/json_data/{table_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            
            # Convert to DataFrame for CSV
            df_data = []
            for record in records:
                row = {
                    '_record_id': record['id'], 
                    '_created_time': record.get('createdTime', '')
                }
                row.update(record.get('fields', {}))
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            
            # Save as CSV
            csv_path = f"{self.export_dir}/csv_data/{table_name}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8')
            
            print(f"    ✅ Exported {len(records)} records")
            return len(records), list(df.columns)
        else:
            print(f"    📝 No records found")
            return 0, []
    
    def create_summary_report(self, results):
        """Create a summary of the export"""
        total_records = sum(result[0] for result in results.values())
        
        report = f"""
# SIMPLE AIRTABLE EXPORT SUMMARY
=====================================

## Export Details
- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Base ID: {self.base_id}
- Export Location: {self.export_dir}/

## Statistics
- Tables Exported: {len(results)}
- Total Records: {total_records:,}

## Tables and Fields
"""
        
        for table_name, (record_count, columns) in results.items():
            report += f"\n### {table_name}\n"
            report += f"- Records: {record_count:,}\n"
            report += f"- Fields: {len(columns)}\n"
            if columns:
                report += f"- Columns: {', '.join(columns[:10])}"
                if len(columns) > 10:
                    report += f" ... and {len(columns) - 10} more"
                report += "\n"
        
        report += f"""

## Files Created
- CSV files: {self.export_dir}/csv_data/
- JSON files: {self.export_dir}/json_data/

## Next Steps
1. Review CSV files for data analysis
2. Use JSON files for data migration
3. Check logs for any errors or warnings
"""
        
        # Save report
        report_path = f"{self.export_dir}/EXPORT_SUMMARY.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(report)
    
    def run_export(self):
        """Main export process"""
        print("\n🚀 STARTING SIMPLE AIRTABLE EXPORT")
        print("="*50)
        
        # Setup
        self.setup_export_directory()
        
        # Determine which tables to export
        tables_to_export = self.table_names
        
        # If no tables specified, try to discover them
        if not tables_to_export:
            print("\n🔍 No table names provided, attempting discovery...")
            tables_to_export = self.discover_tables()
            
            if not tables_to_export:
                print("\n❌ No tables found!")
                print("\nTo fix this, either:")
                print("1. Add your table names to TABLE_NAMES in this script, or")
                print("2. Fix your API token permissions for schema access")
                return False
        
        print(f"\n📋 Found {len(tables_to_export)} tables to export:")
        for table in tables_to_export:
            print(f"  - {table}")
        
        # Export each table
        print(f"\n💾 Exporting data...")
        results = {}
        
        for table_name in tables_to_export:
            try:
                record_count, columns = self.export_table_data(table_name)
                results[table_name] = (record_count, columns)
            except Exception as e:
                print(f"  ❌ Error exporting {table_name}: {e}")
                results[table_name] = (0, [])
        
        # Create summary
        self.create_summary_report(results)
        
        print(f"\n✅ EXPORT COMPLETE!")
        print(f"📁 All files saved to: {os.path.abspath(self.export_dir)}/")
        
        return True

def main():
    """Main entry point"""
    
    if not TABLE_NAMES:
        print("⚠️  WARNING: No table names specified in TABLE_NAMES list")
        print("   The script will attempt to discover tables automatically")
        print("   For better results, add your table names to the TABLE_NAMES list\n")
    
    # Run export
    exporter = SimpleAirtableExporter(API_KEY, BASE_ID, TABLE_NAMES)
    success = exporter.run_export()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()