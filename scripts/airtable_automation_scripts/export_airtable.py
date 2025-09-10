#!/usr/bin/env python3
"""
Airtable System Exporter - Ready to Use Script
Export your entire Airtable base structure and data automatically
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

# Get your API key from: https://airtable.com/create/tokens
#API_KEY = "pat64NbiOXuNRbd8g.b734bc9216ee9c7c68b782ff25eab97eec356e33b8b9b46ebc9e93b296595b8a"  # Starts with 'pat...'

# Chirurgie Data Export
API_KEY = "patYPbtTOgdQYYgTU.827b7b384156c120e07cd4381bb177aa116b689267bdf88313b521e6848e5c66"


# Get your base ID from the URL: airtable.com/appXXXXXXXXXXXX/...
BASE_ID = "app1SIhMIMJaKqAOZ"  # Starts with 'app...'

# ============================================================================
# MAIN EXPORT SCRIPT (No need to modify below)
# ============================================================================

class AirtableSystemExporter:
    def __init__(self, api_key, base_id):
        self.api_key = api_key
        self.base_id = base_id
        self.export_dir = f"airtable_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def setup_export_directory(self):
        """Create organized directory structure"""
        dirs = [
            self.export_dir,
            f"{self.export_dir}/csv_data",
            f"{self.export_dir}/json_data",
            f"{self.export_dir}/schema",
            f"{self.export_dir}/documentation"
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
        print(f"✓ Created export directory: {self.export_dir}/")
        
    def get_base_schema(self):
        """Fetch complete base schema using Metadata API"""
        print("📋 Fetching base schema...")
        url = f"https://api.airtable.com/v0/meta/bases/{self.base_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            schema = response.json()
            print(f"✓ Found {len(schema.get('tables', []))} tables")
            return schema
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching schema: {e}")
            if "401" in str(e):
                print("   Check your API key is correct")
            elif "404" in str(e):
                print("   Check your Base ID is correct")
            return None
    
    def get_table_records(self, table_id, table_name):
        """Fetch all records from a specific table"""
        all_records = []
        offset = None
        
        while True:
            url = f"https://api.airtable.com/v0/{self.base_id}/{table_id}"
            params = {}
            if offset:
                params['offset'] = offset
                
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                all_records.extend(data.get('records', []))
                
                # Check if there are more pages
                offset = data.get('offset')
                if not offset:
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"   ⚠ Error fetching records: {e}")
                break
                
        return all_records
    
    def export_table_data(self, table, schema):
        """Export a single table's data to CSV and JSON"""
        table_name = table['name']
        table_id = table['id']
        
        print(f"  Exporting: {table_name}")
        
        # Get all records
        records = self.get_table_records(table_id, table_name)
        
        if records:
            # Save as JSON (raw format)
            json_path = f"{self.export_dir}/json_data/{table_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            
            # Convert to DataFrame for CSV
            df_data = []
            for record in records:
                row = {'_record_id': record['id'], '_created_time': record.get('createdTime', '')}
                row.update(record.get('fields', {}))
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            
            # Save as CSV
            csv_path = f"{self.export_dir}/csv_data/{table_name}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8')
            
            print(f"    ✓ {len(records)} records exported")
            return len(records)
        else:
            print(f"    - No records found")
            return 0
    
    def create_documentation(self, schema):
        """Create human-readable documentation"""
        print("\n📝 Creating documentation...")
        
        # Markdown documentation
        doc_lines = ["# Airtable Base Documentation\n\n"]
        doc_lines.append(f"**Base ID:** `{self.base_id}`\n")
        doc_lines.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        doc_lines.append(f"**Total Tables:** {len(schema.get('tables', []))}\n\n")
        
        # Excel workbook for structured docs
        excel_path = f"{self.export_dir}/documentation/complete_documentation.xlsx"
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            
            # Tables overview
            tables_data = []
            for table in schema.get('tables', []):
                tables_data.append({
                    'Table Name': table['name'],
                    'Table ID': table['id'],
                    'Description': table.get('description', ''),
                    'Primary Field': next((f['name'] for f in table['fields'] if f.get('id') == table.get('primaryFieldId')), ''),
                    'Number of Fields': len(table.get('fields', []))
                })
            
            pd.DataFrame(tables_data).to_excel(writer, sheet_name='Tables Overview', index=False)
            
            # Document each table
            for table in schema.get('tables', []):
                table_name = table['name']
                
                # Add to markdown
                doc_lines.append(f"## Table: {table_name}\n\n")
                doc_lines.append(f"- **ID:** `{table['id']}`\n")
                if table.get('description'):
                    doc_lines.append(f"- **Description:** {table['description']}\n")
                doc_lines.append("\n### Fields:\n\n")
                
                # Field details for Excel
                fields_data = []
                
                for field in table.get('fields', []):
                    # For Excel
                    field_info = {
                        'Field Name': field['name'],
                        'Field ID': field['id'],
                        'Type': field['type'],
                        'Description': field.get('description', '')
                    }
                    
                    # Extract type-specific options
                    if field['type'] == 'singleSelect' or field['type'] == 'multipleSelects':
                        choices = field.get('options', {}).get('choices', [])
                        field_info['Options'] = ', '.join([c.get('name', '') for c in choices])
                    elif field['type'] == 'formula':
                        field_info['Formula'] = field.get('options', {}).get('formula', '')
                    elif field['type'] == 'multipleRecordLinks':
                        field_info['Linked Table'] = field.get('options', {}).get('linkedTableId', '')
                    
                    fields_data.append(field_info)
                    
                    # For Markdown
                    doc_lines.append(f"- **{field['name']}**\n")
                    doc_lines.append(f"  - Type: `{field['type']}`\n")
                    if field.get('description'):
                        doc_lines.append(f"  - Description: {field['description']}\n")
                    
                    # Add type-specific details to markdown
                    if field['type'] == 'formula':
                        formula = field.get('options', {}).get('formula', '')
                        if formula:
                            doc_lines.append(f"  - Formula: `{formula}`\n")
                    elif field['type'] == 'multipleRecordLinks':
                        linked_table = field.get('options', {}).get('linkedTableId', '')
                        if linked_table:
                            doc_lines.append(f"  - Links to: `{linked_table}`\n")
                
                # Save fields to Excel
                if fields_data:
                    # Truncate sheet name to Excel's 31 character limit
                    sheet_name = table_name[:31] if len(table_name) > 31 else table_name
                    pd.DataFrame(fields_data).to_excel(writer, sheet_name=sheet_name, index=False)
                
                doc_lines.append("\n---\n\n")
        
        # Save markdown
        md_path = f"{self.export_dir}/documentation/base_documentation.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.writelines(doc_lines)
        
        # Save raw schema
        schema_path = f"{self.export_dir}/schema/complete_schema.json"
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        print("✓ Documentation created")
    
    def create_relationships_map(self, schema):
        """Map all table relationships"""
        print("🔗 Mapping relationships...")
        
        relationships = []
        
        for table in schema.get('tables', []):
            for field in table.get('fields', []):
                if field['type'] == 'multipleRecordLinks':
                    linked_table_id = field.get('options', {}).get('linkedTableId')
                    linked_table_name = next(
                        (t['name'] for t in schema['tables'] if t['id'] == linked_table_id),
                        'Unknown'
                    )
                    
                    relationships.append({
                        'Source Table': table['name'],
                        'Field Name': field['name'],
                        'Target Table': linked_table_name,
                        'Field ID': field['id'],
                        'Target Table ID': linked_table_id
                    })
        
        if relationships:
            # Save as CSV
            rel_df = pd.DataFrame(relationships)
            rel_path = f"{self.export_dir}/documentation/table_relationships.csv"
            rel_df.to_csv(rel_path, index=False)
            
            # Print summary
            print(f"✓ Found {len(relationships)} relationships")
            for rel in relationships[:5]:  # Show first 5
                print(f"  {rel['Source Table']} --> {rel['Target Table']} (via {rel['Field Name']})")
            if len(relationships) > 5:
                print(f"  ... and {len(relationships) - 5} more")
        else:
            print("  No table relationships found")
    
    def create_summary_report(self, schema, total_records):
        """Create a summary report of the export"""
        report = f"""
# EXPORT SUMMARY REPORT
========================

## Export Details
- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Base ID: {self.base_id}
- Export Location: {self.export_dir}/

## Statistics
- Total Tables: {len(schema.get('tables', []))}
- Total Records Exported: {total_records:,}
- Total Fields: {sum(len(t.get('fields', [])) for t in schema.get('tables', []))}

## Tables Exported
"""
        
        for table in schema.get('tables', []):
            report += f"- {table['name']} ({len(table.get('fields', []))} fields)\n"
        
        report += f"""

## Files Created
- CSV files: {self.export_dir}/csv_data/
- JSON files: {self.export_dir}/json_data/
- Documentation: {self.export_dir}/documentation/
- Schema: {self.export_dir}/schema/

## Next Steps
1. Review the documentation in complete_documentation.xlsx
2. Check table_relationships.csv for data model
3. Use CSV files for data migration
4. Keep schema/complete_schema.json for reference
"""
        
        # Save report
        report_path = f"{self.export_dir}/EXPORT_SUMMARY.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print("\n" + "="*50)
        print(report)
    
    def run_export(self):
        """Main export process"""
        print("\n🚀 STARTING AIRTABLE EXPORT")
        print("="*50)
        
        # Validate credentials
        if self.api_key == "YOUR_API_KEY_HERE" or self.base_id == "YOUR_BASE_ID_HERE":
            print("❌ ERROR: Please update API_KEY and BASE_ID in the script!")
            print("\n1. Get API key from: https://airtable.com/create/tokens")
            print("2. Get Base ID from your Airtable URL: airtable.com/appXXXXXX/...")
            return False
        
        # Setup
        self.setup_export_directory()
        
        # Get schema
        schema = self.get_base_schema()
        if not schema:
            print("\n❌ Failed to fetch schema. Please check your credentials.")
            return False
        
        # Export all tables
        print(f"\n💾 Exporting {len(schema.get('tables', []))} tables...")
        total_records = 0
        
        for table in schema.get('tables', []):
            records_count = self.export_table_data(table, schema)
            total_records += records_count
        
        # Create documentation
        self.create_documentation(schema)
        
        # Map relationships
        self.create_relationships_map(schema)
        
        # Create summary
        self.create_summary_report(schema, total_records)
        
        print("\n✅ EXPORT COMPLETE!")
        print(f"📁 All files saved to: {os.path.abspath(self.export_dir)}/")
        
        return True

def main():
    """Main entry point"""
    # Check if running with command line arguments
    if len(sys.argv) == 3:
        api_key = sys.argv[1]
        base_id = sys.argv[2]
    else:
        api_key = API_KEY
        base_id = BASE_ID
    
    # Run export
    exporter = AirtableSystemExporter(api_key, base_id)
    success = exporter.run_export()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
