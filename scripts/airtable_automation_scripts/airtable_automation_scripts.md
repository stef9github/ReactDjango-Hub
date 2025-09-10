# Automating Airtable System Documentation Export

## Option 1: Python Script Using Airtable API (Recommended)

### Prerequisites
```bash
pip install pyairtable pandas openpyxl requests
```

### Complete Python Script

```python
import os
import json
import pandas as pd
from pyairtable import Api
from pyairtable.models import Base
import requests
from datetime import datetime

class AirtableSystemExporter:
    def __init__(self, api_key, base_id):
        """
        Initialize the exporter with your Airtable credentials
        
        Args:
            api_key: Your Airtable API key (get from account.airtable.com/api)
            base_id: The base ID (starts with 'app...')
        """
        self.api_key = api_key
        self.base_id = base_id
        self.api = Api(api_key)
        self.base = self.api.base(base_id)
        self.export_dir = f"airtable_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def setup_export_directory(self):
        """Create organized directory structure for exports"""
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(f"{self.export_dir}/csv_data", exist_ok=True)
        os.makedirs(f"{self.export_dir}/schema", exist_ok=True)
        os.makedirs(f"{self.export_dir}/documentation", exist_ok=True)
        
    def get_base_schema(self):
        """Fetch complete base schema using Metadata API"""
        url = f"https://api.airtable.com/v0/meta/bases/{self.base_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching schema: {response.status_code}")
            return None
    
    def export_all_tables_to_csv(self, schema):
        """Export all tables data to CSV files"""
        tables_data = {}
        
        for table in schema['tables']:
            table_name = table['name']
            table_id = table['id']
            
            print(f"Exporting table: {table_name}")
            
            # Get all records from table
            table_obj = self.base.table(table_id)
            records = table_obj.all()
            
            # Convert to pandas DataFrame
            if records:
                df_data = []
                for record in records:
                    row = {'record_id': record['id']}
                    row.update(record['fields'])
                    df_data.append(row)
                
                df = pd.DataFrame(df_data)
                
                # Save to CSV
                csv_path = f"{self.export_dir}/csv_data/{table_name}.csv"
                df.to_csv(csv_path, index=False)
                
                tables_data[table_name] = df
                print(f"  ✓ Exported {len(df)} records to {csv_path}")
            else:
                print(f"  - No records in {table_name}")
                
        return tables_data
    
    def document_schema(self, schema):
        """Create detailed documentation of the schema"""
        doc_lines = ["# Airtable Base Documentation\n\n"]
        doc_lines.append(f"**Base ID:** {self.base_id}\n")
        doc_lines.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Create Excel workbook for structured documentation
        with pd.ExcelWriter(f"{self.export_dir}/documentation/schema_documentation.xlsx") as writer:
            
            # Tables overview
            tables_overview = []
            for table in schema['tables']:
                tables_overview.append({
                    'Table Name': table['name'],
                    'Table ID': table['id'],
                    'Description': table.get('description', ''),
                    'Number of Fields': len(table['fields'])
                })
            
            pd.DataFrame(tables_overview).to_excel(writer, sheet_name='Tables Overview', index=False)
            
            # Document each table
            for table in schema['tables']:
                table_name = table['name']
                doc_lines.append(f"## Table: {table_name}\n\n")
                doc_lines.append(f"**ID:** {table['id']}\n")
                
                if table.get('description'):
                    doc_lines.append(f"**Description:** {table['description']}\n")
                
                doc_lines.append("\n### Fields:\n\n")
                
                # Field details
                fields_data = []
                for field in table['fields']:
                    field_info = {
                        'Field Name': field['name'],
                        'Field ID': field['id'],
                        'Type': field['type'],
                        'Description': field.get('description', '')
                    }
                    
                    # Add field-specific options
                    if 'options' in field:
                        field_info['Options'] = json.dumps(field['options'], indent=2)
                    
                    fields_data.append(field_info)
                    
                    # Add to markdown
                    doc_lines.append(f"- **{field['name']}** ({field['type']})\n")
                    if field.get('description'):
                        doc_lines.append(f"  - Description: {field['description']}\n")
                    if field['type'] == 'formula' and 'options' in field:
                        doc_lines.append(f"  - Formula: `{field['options'].get('formula', 'N/A')}`\n")
                    if field['type'] == 'multipleRecordLinks' and 'options' in field:
                        doc_lines.append(f"  - Linked Table: {field['options'].get('linkedTableId', 'N/A')}\n")
                
                # Save to Excel
                if fields_data:
                    df_fields = pd.DataFrame(fields_data)
                    sheet_name = f"{table_name[:30]}"  # Excel sheet name limit
                    df_fields.to_excel(writer, sheet_name=sheet_name, index=False)
                
                doc_lines.append("\n---\n\n")
        
        # Save markdown documentation
        with open(f"{self.export_dir}/documentation/base_documentation.md", 'w') as f:
            f.writelines(doc_lines)
        
        # Save raw schema JSON
        with open(f"{self.export_dir}/schema/raw_schema.json", 'w') as f:
            json.dump(schema, f, indent=2)
    
    def create_relationship_map(self, schema):
        """Create a map of table relationships"""
        relationships = []
        
        for table in schema['tables']:
            for field in table['fields']:
                if field['type'] == 'multipleRecordLinks':
                    relationships.append({
                        'From Table': table['name'],
                        'From Field': field['name'],
                        'To Table': self._get_table_name_by_id(schema, field['options'].get('linkedTableId')),
                        'Relationship Type': 'Linked Records'
                    })
        
        if relationships:
            df_rel = pd.DataFrame(relationships)
            df_rel.to_csv(f"{self.export_dir}/documentation/relationships.csv", index=False)
            
            # Create visual representation
            print("\n📊 Table Relationships:")
            for rel in relationships:
                print(f"  {rel['From Table']} --[{rel['From Field']}]--> {rel['To Table']}")
    
    def _get_table_name_by_id(self, schema, table_id):
        """Helper to get table name from ID"""
        for table in schema['tables']:
            if table['id'] == table_id:
                return table['name']
        return 'Unknown'
    
    def run_full_export(self):
        """Execute the complete export process"""
        print("🚀 Starting Airtable System Export...\n")
        
        # Setup
        self.setup_export_directory()
        
        # Get schema
        print("📋 Fetching base schema...")
        schema = self.get_base_schema()
        
        if not schema:
            print("❌ Failed to fetch schema. Check your API key and base ID.")
            return
        
        print(f"✓ Found {len(schema['tables'])} tables\n")
        
        # Export data
        print("💾 Exporting table data...")
        self.export_all_tables_to_csv(schema)
        
        # Document schema
        print("\n📝 Creating documentation...")
        self.document_schema(schema)
        
        # Map relationships
        print("\n🔗 Mapping relationships...")
        self.create_relationship_map(schema)
        
        print(f"\n✅ Export complete! Check the '{self.export_dir}' directory")
        print("\nExported files:")
        print(f"  📁 {self.export_dir}/")
        print(f"     📁 csv_data/ - All table data in CSV format")
        print(f"     📁 schema/ - Raw JSON schema")
        print(f"     📁 documentation/ - Human-readable documentation")
        
        return self.export_dir

# Usage
if __name__ == "__main__":
    # Get these from your Airtable account
    API_KEY = "your_api_key_here"  # Get from: account.airtable.com/api
    BASE_ID = "appXXXXXXXXXXXX"    # Get from: airtable.com URL or API docs
    
    exporter = AirtableSystemExporter(API_KEY, BASE_ID)
    exporter.run_full_export()
```

## Option 2: Node.js Script (Alternative)

```javascript
const Airtable = require('airtable');
const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

class AirtableExporter {
    constructor(apiKey, baseId) {
        this.apiKey = apiKey;
        this.baseId = baseId;
        this.base = new Airtable({apiKey: apiKey}).base(baseId);
        this.exportDir = `airtable_export_${new Date().toISOString().slice(0,10)}`;
    }

    async setupDirectories() {
        await fs.mkdir(this.exportDir, { recursive: true });
        await fs.mkdir(path.join(this.exportDir, 'csv_data'), { recursive: true });
        await fs.mkdir(path.join(this.exportDir, 'schema'), { recursive: true });
    }

    async getSchema() {
        const response = await axios.get(
            `https://api.airtable.com/v0/meta/bases/${this.baseId}`,
            {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        return response.data;
    }

    async exportTableData(tableName) {
        const records = [];
        
        await this.base(tableName).select({
            pageSize: 100,
        }).eachPage((pageRecords, fetchNextPage) => {
            records.push(...pageRecords.map(r => ({
                id: r.id,
                ...r.fields
            })));
            fetchNextPage();
        });

        // Convert to CSV
        if (records.length > 0) {
            const csv = this.jsonToCSV(records);
            await fs.writeFile(
                path.join(this.exportDir, 'csv_data', `${tableName}.csv`),
                csv
            );
        }
        
        return records;
    }

    jsonToCSV(json) {
        if (json.length === 0) return '';
        
        const keys = Object.keys(json[0]);
        const csv = [
            keys.join(','),
            ...json.map(row => 
                keys.map(key => JSON.stringify(row[key] || '')).join(',')
            )
        ].join('\n');
        
        return csv;
    }

    async exportAll() {
        await this.setupDirectories();
        
        const schema = await this.getSchema();
        await fs.writeFile(
            path.join(this.exportDir, 'schema', 'schema.json'),
            JSON.stringify(schema, null, 2)
        );

        for (const table of schema.tables) {
            console.log(`Exporting ${table.name}...`);
            await this.exportTableData(table.name);
        }
        
        console.log(`Export complete! Check ${this.exportDir}/`);
    }
}

// Usage
const exporter = new AirtableExporter('YOUR_API_KEY', 'YOUR_BASE_ID');
exporter.exportAll();
```

## Option 3: No-Code Tools

### 1. **Zapier/Make (Integromat)**
- Create a workflow that triggers on schedule
- Use Airtable modules to fetch all records
- Export to Google Sheets or CSV files

### 2. **Airtable Scripting Extension**
```javascript
// Run this in Airtable's Scripting Extension
// It will create a downloadable documentation

const base = base;
const documentation = [];

for (const table of base.tables) {
    const tableDoc = {
        name: table.name,
        fields: table.fields.map(field => ({
            name: field.name,
            type: field.type,
            options: field.options
        }))
    };
    documentation.push(tableDoc);
}

console.log(JSON.stringify(documentation, null, 2));
output.markdown('# Copy the console output for your documentation');
```

### 3. **Third-Party Services**
- **On2Air Backups**: Automated daily backups with schema
- **Basebackup.com**: Scheduled exports of data and structure
- **Railsware's Airtable Backup**: GitHub integration for version control

## Option 4: Quick Bash Script (Using curl)

```bash
#!/bin/bash

# Configuration
API_KEY="your_api_key"
BASE_ID="appXXXXXXXX"
OUTPUT_DIR="airtable_export_$(date +%Y%m%d)"

# Create directories
mkdir -p "$OUTPUT_DIR/schema"
mkdir -p "$OUTPUT_DIR/data"

# Fetch schema
echo "Fetching schema..."
curl -H "Authorization: Bearer $API_KEY" \
     "https://api.airtable.com/v0/meta/bases/$BASE_ID" \
     > "$OUTPUT_DIR/schema/base_schema.json"

# Parse and export each table (requires jq)
echo "Exporting tables..."
TABLES=$(curl -s -H "Authorization: Bearer $API_KEY" \
     "https://api.airtable.com/v0/meta/bases/$BASE_ID" \
     | jq -r '.tables[].name')

for table in $TABLES; do
    echo "Exporting $table..."
    curl -H "Authorization: Bearer $API_KEY" \
         "https://api.airtable.com/v0/$BASE_ID/$table" \
         > "$OUTPUT_DIR/data/${table}.json"
done

echo "Export complete! Check $OUTPUT_DIR/"
```

## Getting Your Credentials

### 1. Get Your API Key:
1. Go to [airtable.com/account](https://airtable.com/account)
2. Click on "API" section or go to [airtable.com/create/tokens](https://airtable.com/create/tokens)
3. Create a personal access token with these scopes:
   - `data.records:read`
   - `schema.bases:read`

### 2. Get Your Base ID:
- Option A: From URL - `airtable.com/appXXXXXXXXXXXX/...`
- Option B: From API docs you're about to access
- Option C: In the API documentation page

## Quick Start Instructions

1. **Install Python and required packages:**
```bash
pip install pyairtable pandas openpyxl requests
```

2. **Save the Python script** as `export_airtable.py`

3. **Update credentials** in the script:
```python
API_KEY = "patXXXXXXXXXXXX"  # Your personal access token
BASE_ID = "appXXXXXXXXXXXX"  # Your base ID
```

4. **Run the script:**
```bash
python export_airtable.py
```

## What You'll Get

```
airtable_export_20240910_143022/
├── csv_data/           # All your data in CSV format
│   ├── Table1.csv
│   ├── Table2.csv
│   └── Table3.csv
├── schema/             # Complete structure
│   └── raw_schema.json
└── documentation/      # Human-readable docs
    ├── base_documentation.md
    ├── schema_documentation.xlsx
    └── relationships.csv
```

## Advanced Features to Add

- **Export automations** (requires web scraping as not in API)
- **Export interfaces** (not available via API)
- **Version control integration** (auto-commit to Git)
- **Scheduled backups** (using cron or Task Scheduler)
- **Data validation reports**
- **Migration scripts** to other databases

The Python script is production-ready and will give you everything you need to recreate the system!
