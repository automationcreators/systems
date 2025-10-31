# Directory UI Template - Customization Guide

Complete guide for customizing the Directory UI Template for your specific use case.

## Table of Contents

1. [Branding & Identity](#branding--identity)
2. [Color Scheme](#color-scheme)
3. [Content Customization](#content-customization)
4. [Component Modifications](#component-modifications)
5. [Layout Adjustments](#layout-adjustments)
6. [Advanced Customization](#advanced-customization)

---

## Branding & Identity

### Update Site Name and Logo

**File**: `src/components/layout/navigation.tsx`

```tsx
// Change the logo icon (line ~40)
<Star className="h-6 w-6 text-white" fill="white" />
// Replace with your icon from lucide-react

// Update site name (lines ~44-47)
<div className="text-xl font-bold text-gray-900">
  Your Site Name
</div>
<div className="text-sm text-gray-600">Tagline</div>
```

### Update Metadata

**File**: `src/app/layout.tsx`

```tsx
export const metadata: Metadata = {
  title: 'Your Site - Your Tagline',
  description: 'Your site description for SEO',
  keywords: 'your, keywords, here',
  metadataBase: new URL('https://yoursite.com'),
  // ... update all other fields
}
```

---

## Color Scheme

### Primary Colors

**File**: `src/app/globals.css`

Replace the color variables:

```css
@theme {
  /* Your primary color palette */
  --color-primary-600: #your-main-color;
  --color-primary-700: #your-hover-color;
  --color-primary-800: #your-darker-color;

  /* Success/accent colors */
  --color-success-600: #your-success-color;
}
```

### Gradient Backgrounds

**Hero Gradient** - `src/components/home/HeroSection.tsx`:

```tsx
<section className="relative bg-gradient-to-br from-purple-600 via-purple-700 to-purple-800">
// Change from-*/via-*/to-* to your colors
```

**Stats Section Gradient** - `src/components/home/StatsSection.tsx`:

```tsx
<section className="py-16 bg-indigo-600 relative overflow-hidden">
// Change bg-*-600 to your color
```

### Category Colors

**File**: `src/components/home/CategoryGrid.tsx`

Each category has configurable colors:

```tsx
{
  color: 'bg-green-500',      // Icon background
  hoverColor: 'hover:bg-green-600',  // Icon hover
  textColor: 'text-green-600',       // Badge text
}
```

---

## Content Customization

### Hero Section

**File**: `src/components/home/HeroSection.tsx`

**Main Heading** (line ~59):
```tsx
<h1 className="text-4xl md:text-6xl font-bold text-white mb-6 text-balance">
  Your Main Headline{' '}
  <span className="text-yellow-400">Highlighted Text</span>
</h1>
```

**Subheading** (line ~65):
```tsx
<p className="text-xl md:text-2xl text-primary-100 mb-8 text-pretty max-w-3xl mx-auto">
  Your description text here
</p>
```

**Search Placeholder** (line ~78):
```tsx
<input
  placeholder="Search for your items..."
  // ...
/>
```

**Quick Search Options** (line ~13):
```tsx
const quickSearchOptions = [
  { label: 'Option 1', value: 'option-1', category: 'cat-1' },
  { label: 'Option 2', value: 'option-2', category: 'cat-2' },
  // Add your options...
]
```

**Stats Numbers** (line ~107):
```tsx
<span className="text-3xl font-bold text-white">1000+</span>
<p className="text-primary-100">Your Metric</p>
```

### Categories

**File**: `src/components/home/CategoryGrid.tsx`

**Add/Modify Category** (line ~11):
```tsx
const categories = [
  {
    name: 'Your Category',           // Display name
    slug: 'your-category',           // URL slug
    description: 'Description text', // Subtitle
    icon: Code,                      // Icon from lucide-react
    color: 'bg-green-500',          // Background color
    hoverColor: 'hover:bg-green-600', // Hover color
    textColor: 'text-green-600',    // Text color
    count: 150,                      // Number badge
    featured: [                      // Featured items
      'Item 1', 'Item 2', 'Item 3', 'Item 4'
    ]
  },
  // ... more categories
]
```

**Change Number of Columns**:
```tsx
// Currently: 1/2/3 columns (line ~88)
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">

// For 4 columns:
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
```

### Stats Section

**File**: `src/components/home/StatsSection.tsx`

**Update Stats** (line ~8):
```tsx
const stats = [
  {
    label: 'Your Metric',
    value: '500+',
    description: 'Description of metric',
    icon: MapPin,  // Icon from lucide-react
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  // ... more stats
]
```

**Update Trust Messages** (line ~63):
```tsx
<div>
  <div className="text-2xl font-bold text-white mb-2">
    Your Trust Message
  </div>
  <p className="text-primary-100 text-sm">
    Supporting text for this message.
  </p>
</div>
```

**Update Badges** (line ~84):
```tsx
<div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2 flex items-center">
  <Star className="h-5 w-5 text-yellow-300 mr-2" />
  <span className="text-white font-medium text-sm">Your Badge Text</span>
</div>
```

### Navigation Menu

**File**: `src/components/layout/navigation.tsx`

**Update Menu Items** (line ~9):
```tsx
const navigation = [
  { name: 'Home', href: '/' },
  { name: 'Your Page', href: '/your-page' },
  { name: 'Categories', href: '/categories' },
  // ... your items
]
```

**Update Category Dropdown** (line ~17):
```tsx
const categoryDropdown = [
  { name: 'Category 1', href: '/categories/cat1', icon: '💻' },
  { name: 'Category 2', href: '/categories/cat2', icon: '🎨' },
  // ... your categories
]
```

---

## Component Modifications

### Add New Section to Home Page

**File**: `src/app/page.tsx`

Add between existing sections:

```tsx
{/* Your New Section */}
<section className="py-16 bg-white">
  <div className="container-responsive">
    <div className="text-center mb-12">
      <h2 className="text-3xl font-bold text-gray-900 mb-4">
        Your Section Title
      </h2>
      <p className="text-lg text-gray-600 max-w-2xl mx-auto">
        Your section description
      </p>
    </div>
    {/* Your content here */}
  </div>
</section>
```

### Create New Component

Create `src/components/home/YourComponent.tsx`:

```tsx
import { YourIcon } from 'lucide-react'

export function YourComponent() {
  return (
    <div className="your-classes">
      {/* Your component JSX */}
    </div>
  )
}
```

Then import in `page.tsx`:
```tsx
import { YourComponent } from '@/components/home/YourComponent'
```

---

## Layout Adjustments

### Change Container Width

**File**: `src/app/globals.css`

```css
.container-responsive {
  max-width: 80rem;  /* Change to your preferred width */
  /* 64rem = 1024px, 80rem = 1280px, 96rem = 1536px */
}
```

### Adjust Section Spacing

Change padding in section elements:

```tsx
// Default
<section className="py-16">

// More spacing
<section className="py-20">

// Less spacing
<section className="py-12">
```

### Responsive Breakpoints

Tailwind breakpoints used:
- `sm:` = 640px
- `md:` = 768px
- `lg:` = 1024px
- `xl:` = 1280px

Example adjustment:
```tsx
// Change tablet breakpoint from md to lg
<div className="grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
// to
<div className="grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
```

---

## Advanced Customization

### Add Custom Font

**File**: `src/app/layout.tsx`

```tsx
import { YourFont } from 'next/font/google'

const yourFont = YourFont({
  subsets: ["latin"],
  weight: ['400', '500', '600', '700']
})

// Update className in body
<body className={`${yourFont.className} ...`}>
```

### Add Animation

**File**: `src/app/globals.css`

```css
/* Add keyframe */
@keyframes yourAnimation {
  from { /* start state */ }
  to { /* end state */ }
}

/* Use in component */
.your-element {
  animation: yourAnimation 0.3s ease-out;
}
```

### Add Dark Mode Support

1. Add dark mode colors to `@theme`
2. Use Tailwind's `dark:` prefix:
```tsx
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
```

### Custom Icon Set

Replace Lucide icons with your own:

```tsx
// Instead of
import { Code } from 'lucide-react'

// Use custom SVG
const CustomIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24">
    {/* your SVG path */}
  </svg>
)
```

### Add Footer

Create `src/components/layout/Footer.tsx` based on dirKidSports footer template, then add to `layout.tsx`:

```tsx
import { Footer } from '@/components/layout/footer'

// In return
<Footer />
```

---

## Testing Your Changes

1. **Save files** - Changes auto-reload with Next.js
2. **Check responsive** - Test mobile/tablet/desktop views
3. **Validate HTML** - Use W3C Validator
4. **Test accessibility** - Use Lighthouse/axe DevTools
5. **Check SEO** - Use Google Search Console

---

## Common Issues

### Colors Not Updating

- Clear browser cache (Cmd/Ctrl + Shift + R)
- Restart dev server
- Check CSS variable names match

### Component Not Displaying

- Check import path
- Verify component export
- Check for TypeScript errors

### Layout Breaking

- Validate HTML structure
- Check Tailwind classes
- Inspect with browser DevTools

---

## Need Help?

Refer to:
- [README.md](../README.md) - Template overview
- [Next.js Docs](https://nextjs.org/docs)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Lucide Icons](https://lucide.dev)

---

**Last Updated**: October 2025
