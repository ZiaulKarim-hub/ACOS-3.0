---
name: frontend-coding
description: Structured guidance for implementing frontend components, UI, and client-side logic. Covers React, Vue, Angular, Svelte, Next.js, Nuxt.js.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Frontend Coding Skill

## Purpose

This skill provides structured guidance for implementing frontend components, user interfaces, and client-side functionality.

## When to Use

Apply this skill when:
- Creating UI components
- Implementing user interactions
- Building forms and input handling
- Managing client-side state
- Handling API integrations on the client
- Implementing responsive designs

## Skill Protocol

### Phase 1: Context Gathering

1. Read the component/feature specification
2. Identify the UI framework in use
3. Check existing component patterns in the codebase
4. Understand styling approach (CSS, Tailwind, styled-components, etc.)

### Phase 2: Component Planning

1. Break down the UI into components
2. Identify:
   - Props interface
   - State requirements
   - Event handlers needed
   - API calls required
3. Plan component hierarchy

### Phase 3: Implementation

1. Create component file(s)
2. Implement:
   - Props and types
   - Local state (if needed)
   - Event handlers
   - Render logic
3. Apply styles
4. Add accessibility attributes

### Phase 4: Integration

1. Wire up to parent components
2. Connect to state management (if applicable)
3. Integrate API calls
4. Handle loading and error states

## Quality Checklist

### Structure
- [ ] Components are appropriately sized (not too large)
- [ ] Props are properly typed
- [ ] Component hierarchy is logical

### Functionality
- [ ] All user interactions work correctly
- [ ] Form validation is implemented
- [ ] Error states are handled
- [ ] Loading states are shown

### Accessibility
- [ ] Semantic HTML is used
- [ ] ARIA attributes where needed
- [ ] Keyboard navigation works
- [ ] Focus management is correct

### Styling
- [ ] Responsive on all target screen sizes
- [ ] Follows design system/guidelines
- [ ] No layout shifts on load

### Performance
- [ ] No unnecessary re-renders
- [ ] Large lists are virtualized
- [ ] Images are optimized
- [ ] Code splitting where appropriate

## Common Patterns

### React Component Structure

```tsx
import { useState, useEffect } from 'react';
import type { ComponentProps } from './types';

export function ComponentName({ prop1, prop2 }: ComponentProps) {
  const [state, setState] = useState(initialValue);

  useEffect(() => {
    // Side effects
  }, [dependencies]);

  const handleEvent = () => {
    // Event logic
  };

  return (
    <div className="component-class">
      {/* JSX */}
    </div>
  );
}
```

### Form Handling

```tsx
const [formData, setFormData] = useState({ field: '' });
const [errors, setErrors] = useState({});

const handleSubmit = async (e) => {
  e.preventDefault();
  const validationErrors = validate(formData);
  if (Object.keys(validationErrors).length > 0) {
    setErrors(validationErrors);
    return;
  }
  await submitData(formData);
};
```

### API Integration

```tsx
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

useEffect(() => {
  const fetchData = async () => {
    try {
      const result = await api.getData();
      setData(result);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };
  fetchData();
}, []);
```

## Output Requirements

When completing frontend work, ensure:

1. All components render without errors
2. TypeScript/PropTypes are properly defined
3. Tests cover critical paths
4. Code matches project conventions
5. Evidence bundle includes console error check and build verification

---

*Frontend Coding Skill - Building interfaces users love.*
