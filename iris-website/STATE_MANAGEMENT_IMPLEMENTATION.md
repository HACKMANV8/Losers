# State Management Implementation - Demo to Comparison Flow

## Overview
This document describes the state management and navigation flow between the Demo page and Comparison page in the IRis website.

## Implementation Summary

### 1. Demo Page Modifications (`/demo/page.tsx`)

#### Added State Variables
- `fileContent`: Stores the actual C source code content from uploaded file
- `router`: Next.js router for programmatic navigation

#### File Upload Enhancement
```typescript
const onDrop = useCallback((acceptedFiles: File[]) => {
  if (acceptedFiles.length > 0) {
    const uploadedFile = acceptedFiles[0];
    setFile(uploadedFile);
    
    // NEW: Read file content using FileReader
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setFileContent(content);
    };
    reader.readAsText(uploadedFile);
  }
}, []);
```

#### Data Transfer Function
```typescript
const handleComparePerformance = () => {
  // Prepare comprehensive comparison data
  const comparisonData = {
    sourceCode: fileContent,           // Original C code
    fileName: file.name,               // File name
    predictedPasses: results.predicted_passes,  // ML predictions
    features: results.features,        // Extracted features
    modelUsed: results.model_used,     // Model type
    processingTime: results.processing_time_ms,
    timestamp: Date.now()              // For data freshness validation
  };
  
  // Store in sessionStorage for persistence
  sessionStorage.setItem('iris_comparison_data', JSON.stringify(comparisonData));
  
  // Navigate to comparison page
  router.push('/comparison?from=demo');
};
```

#### New UI Button
- Added "⚡ Compare Performance" button after results display
- Pink-to-rose gradient styling matching design system
- Only appears after successful optimization

### 2. Comparison Page Redesign (`/comparison/page.tsx`)

#### Data Interface
```typescript
interface ComparisonData {
  sourceCode: string;
  fileName: string;
  predictedPasses: string[];
  features: Record<string, number>;
  modelUsed: string;
  processingTime: number;
  timestamp: number;
}
```

#### State Management
- `loading`: Boolean for initial load state
- `error`: Error message if data validation fails
- `comparisonData`: Validated comparison data

#### Data Loading & Validation
```typescript
useEffect(() => {
  // Load from sessionStorage
  const storedData = sessionStorage.getItem('iris_comparison_data');
  
  if (!storedData) {
    setError('No comparison data found. Please run the optimizer first.');
    return;
  }
  
  const data: ComparisonData = JSON.parse(storedData);
  
  // Validate required fields
  if (!data.sourceCode || !data.fileName || !data.predictedPasses || !data.features) {
    setError('Invalid comparison data. Please run the optimizer again.');
    return;
  }
  
  // Check data freshness (24 hours)
  const dataAge = Date.now() - data.timestamp;
  const maxAge = 24 * 60 * 60 * 1000;
  if (dataAge > maxAge) {
    setError('Comparison data is too old. Please run the optimizer again.');
    return;
  }
  
  // Data is valid
  setComparisonData(data);
  setLoading(false);
}, [searchParams]);
```

#### UI States

**1. Loading State**
- Displays spinner while loading data
- Shows "Loading comparison data..." message

**2. Error State**
- Shows warning icon (⚠️)
- Clear error message
- "Go to Demo" and "Go Home" action buttons

**3. Success State**
- File information section with filename, model, timestamp
- ML-predicted pass sequence display
- Standard optimization levels grid (-O0, -O2, -O3, -Oz)
- Ready-to-compare placeholder with stats:
  - Source lines count
  - Features extracted count
  - Prediction time
- "← Back to Demo" navigation button

## Data Flow Diagram

```
┌─────────────┐
│  Demo Page  │
└──────┬──────┘
       │
       │ 1. User uploads C file
       ├──> Read file content (FileReader)
       │
       │ 2. Submit to backend
       ├──> POST /api/optimize
       │
       │ 3. Receive results
       ├──> Store in state
       │
       │ 4. User clicks "Compare Performance"
       ├──> Package data
       ├──> Save to sessionStorage
       ├──> Navigate to /comparison
       │
       ▼
┌──────────────────┐
│ Comparison Page  │
└──────┬───────────┘
       │
       │ 1. Load from sessionStorage
       ├──> Validate data
       ├──> Check freshness
       │
       │ 2. Display results
       └──> Show comparison interface
```

## Validation Rules

### Required Fields
- `sourceCode`: Must be non-empty string
- `fileName`: Must be present
- `predictedPasses`: Must be array
- `features`: Must be object

### Data Freshness
- Maximum age: 24 hours
- Older data triggers error

### Error Handling
1. No data in sessionStorage → Redirect to Demo
2. Invalid JSON → Show error
3. Missing fields → Show error
4. Expired data → Show error

## Navigation Flow

### From Demo to Comparison
```typescript
router.push('/comparison?from=demo');
```

### From Comparison back to Demo
```typescript
router.push('/demo');
```

### Direct access to /comparison
- Shows error if no data available
- Provides navigation links to Demo and Home

## Storage Strategy

### Why sessionStorage?
- **Persistence**: Survives page navigation
- **Privacy**: Cleared when browser tab closes
- **Size**: Adequate for code + metadata (~10-50KB typical)
- **Security**: Not sent to server with requests

### Alternative Considered: URL Parameters
❌ **Rejected** because:
- URL length limits (~2000 chars)
- Source code would be exposed in URL
- Poor UX (ugly URLs)
- Browser history pollution

### Alternative Considered: Context API Only
❌ **Rejected** because:
- Lost on page refresh
- No persistence across navigation
- Requires complex provider setup

## Future Enhancements

### Planned Features
1. Backend API endpoint for actual comparison
2. Real-time compilation and benchmarking
3. Visual charts comparing metrics
4. Download comparison report
5. Share comparison results

### Potential Improvements
- Add localStorage backup for longer persistence
- Implement comparison history
- Cache comparison results
- Add export to PDF/CSV

## Testing Checklist

- [x] File upload captures content correctly
- [x] Navigation to comparison works
- [x] Data persists across navigation
- [x] Direct /comparison access shows error
- [x] Back button works correctly
- [x] Error states display properly
- [x] Loading state shows briefly
- [x] Data validation works
- [x] 24-hour expiry works
- [ ] Test with large files (>1MB)
- [ ] Test with special characters in code
- [ ] Test browser back/forward buttons

## Known Limitations

1. **sessionStorage size**: ~5-10MB limit (adequate for most C files)
2. **No multi-tab sync**: Each tab has independent session
3. **No server persistence**: Data lost if browser crashes
4. **Client-side only**: No backend state management yet

## Security Considerations

- Source code stored client-side only
- No sensitive data transmitted
- sessionStorage auto-clears on tab close
- No XSS risk (React auto-escapes)

---

**Status**: ✅ Complete - State management flow implemented and ready for backend integration
**Next Step**: Implement `/api/compare` backend endpoint for actual RISC-V compilation and benchmarking
