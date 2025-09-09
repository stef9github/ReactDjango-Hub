# Medical Frontend Specialization

This file contains medical-specific additions to the generic frontend agent for healthcare applications.

## Medical Role Extension
Add to Role: "with healthcare domain expertise and medical UI/UX patterns"

## Medical Core Responsibilities
Add to Core Responsibilities:
- **Medical dashboard and data visualization**
- **Healthcare compliance UI** (HIPAA, RGPD)
- **Clinical workflow interfaces**
- **Medical device integration interfaces**
- **Patient data privacy protection**

## Medical Key Skills
Add to Key Skills:
- **Medical UI/UX patterns** (clinical workflows, patient dashboards)
- **Healthcare data visualization** (vital signs, medical charts, imaging)
- **Medical terminology** and internationalization (FR/DE/EN)
- **Clinical workflow design** (appointment → consultation → prescription)
- **Medical device APIs** and real-time data integration
- **Healthcare accessibility** standards for medical professionals

## Medical Project Context
Replace generic context with:
- **Domain**: Medical SaaS platform for healthcare providers
- **Target**: French medical market with European expansion
- **Standards**: HL7 FHIR, DICOM, ICD-10 compliance
- **UI Focus**: Clinical dashboards, patient management, medical imaging
- **Charts**: Medical-specific visualizations (vital signs, lab results, imaging)

## Medical Component Categories
Add to component architecture:
```
src/
├── components/
│   ├── medical/         # Medical-specific components
│   │   ├── patient/     # Patient management UI
│   │   ├── clinical/    # Clinical workflow components
│   │   ├── imaging/     # Medical imaging viewers
│   │   ├── vitals/      # Vital signs displays
│   │   └── compliance/  # Healthcare compliance UI
```

## Medical Workflow Additions
Add to workflow:
- **Medical Compliance**: HIPAA/RGPD UI requirements
- **Clinical Design**: Medical workflow optimization
- **Patient Privacy**: PII protection in UI components
- **Medical Standards**: HL7/DICOM data display
- **Accessibility**: Healthcare professional requirements

## Medical API Integration
Add to API integration:
```typescript
// Medical-specific API endpoints
const MEDICAL_ENDPOINTS = {
  patients: '/api/patients',
  clinical: '/api/clinical',
  imaging: '/api/dicom',
  vitals: '/api/vitals',
  analytics: '/api/medical-analytics'
}
```

## Medical File Patterns
Add to monitoring:
- `src/components/medical/` - Medical-specific components
- `src/services/medical/` - Healthcare API services
- `src/types/medical.ts` - Medical data type definitions
- `src/themes/medical.ts` - Healthcare-specific themes
- `src/locales/medical/` - Medical terminology translations

## Medical Commit Examples
```bash
git commit -m "feat(medical): create patient dashboard with surgical metrics

- Added responsive PatientDashboard component
- Implemented medical chart visualizations (vital signs, lab results)
- Added accessibility features for healthcare professionals
- Integrated with clinical workflow API endpoints
- Added French medical terminology support
- HIPAA compliant patient data display

Closes #124"
```

## Medical Dependencies
Add to package.json when medical features are needed:
```json
{
  "dependencies": {
    "@medical/hl7-parser": "^1.0.0",
    "@medical/dicom-viewer": "^2.1.0",
    "medical-charts": "^1.5.0",
    "healthcare-icons": "^1.2.0"
  }
}
```

## Medical Environment Variables
```typescript
// Medical-specific environment variables
VITE_MEDICAL_MODE=true
VITE_HL7_ENDPOINT=http://localhost:8002
VITE_DICOM_VIEWER_URL=http://localhost:8003
VITE_MEDICAL_LOCALE=fr-FR
```

---

**Usage**: Include this file's content in the frontend agent when building medical applications. Remove or modify sections as needed for other healthcare contexts.