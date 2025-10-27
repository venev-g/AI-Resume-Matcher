---
applyTo: "frontend/**/*.{tsx, ts}"
---

# Frontend Next.js 15 Development Instructions

## Project Context
Building the frontend for enterprise AI Resume Matcher using Next.js 15, React 19, and Tailwind CSS.

## Key Requirements

### Next.js 15 Features
- Use **Turbopack** for development (10x faster)
- Prefer **Server Components** by default
- Use **'use client'** only when needed (state, events, browser APIs)
- Implement **Server Actions** for form submissions
- Use **fetch()** with enhanced caching

### Component Structure
```typescript
// Client Component Pattern
'use client';

import { useState } from 'react';

interface ComponentProps {
  data: DataType;
  onAction: (param: string) => Promise<void>;
}

export default function Component({ data, onAction }: ComponentProps) {
  const [state, setState] = useState<StateType>(initialState);
  
  return (
    <div className="container mx-auto">
      {/* Component JSX */}
    </div>
  );
}
```

### Tailwind CSS Styling
- Use **utility classes** (no custom CSS unless necessary)
- Follow **mobile-first** approach
- Use **semantic color names** (bg-blue-600, not bg-#0000ff)
- Apply **responsive modifiers** (sm:, md:, lg:, xl:)
- Use **group hover** for interactive elements

Common patterns:
```jsx
<button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition disabled:bg-gray-400">
  Submit
</button>
```

### State Management
- Use **useState** for local component state
- Use **useEffect** sparingly (React 19 improvements)
- Implement **optimistic updates** for better UX
- Handle **loading states** explicitly
- Show **error messages** to users

### API Communication
```typescript
// Fetch pattern
const response = await fetch('http://localhost:8000/api/match', {
  method: 'POST',
  body: formData,
});

if (!response.ok) {
  throw new Error('API request failed');
}

const data = await response.json();
```

### TypeScript Best Practices
- Define **interfaces** for all props and data structures
- Use **type guards** for runtime type checking
- Avoid **any** type (use unknown if needed)
- Export **types** from centralized types/ directory
- Use **enums** for fixed value sets

### Form Handling
- Use **FormData** for file uploads
- Validate **input client-side** before submission
- Show **validation errors** inline
- Disable **submit button** during processing
- Clear **form after** successful submission

### Performance
- Use **React.memo** for expensive components
- Implement **lazy loading** for large data sets
- Optimize **images** with next/image
- Use **dynamic imports** for code splitting
- Avoid **unnecessary re-renders**

### Accessibility
- Add **aria-labels** to interactive elements
- Use **semantic HTML** (button, nav, main, etc.)
- Ensure **keyboard navigation** works
- Maintain **color contrast** ratios (WCAG AA)
- Add **alt text** to images