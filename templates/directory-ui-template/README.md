# Directory UI Template

A professional, SEO-optimized directory website template with modern design, responsive layout, and production-ready components.

## Overview

This template provides a complete UI framework for building directory-style websites (tools, services, products, etc.). It features:

- **Modern Design**: Clean gradient hero, card-based layouts, smooth animations
- **Responsive**: Mobile-first design that works on all devices
- **SEO Optimized**: Structured data, meta tags, semantic HTML
- **Accessible**: WCAG compliant with proper ARIA labels
- **Performance**: Optimized CSS, lazy loading, Core Web Vitals friendly

## Template Origin

**Source Project**: dirTechStack (Tech Stack Directory)
**Design Inspiration**: dirKidSports UI Framework
**Created**: October 2025
**Last Updated**: October 2025

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Styling**: Tailwind CSS v4
- **Icons**: Lucide React
- **Font**: Inter (Google Fonts)
- **Type Safety**: TypeScript

## File Structure

```
directory-ui-template/
├── components/
│   ├── home/
│   │   ├── HeroSection.tsx       # Hero with search and stats
│   │   ├── CategoryGrid.tsx      # Category cards grid
│   │   └── StatsSection.tsx      # Statistics display
│   └── layout/
│       └── navigation.tsx        # Header navigation with dropdown
├── styles/
│   └── globals.css               # Global styles and theme
├── layout.tsx                    # Root layout with SEO metadata
├── page.tsx                      # Home page composition
└── docs/
    ├── README.md                 # This file
    └── CUSTOMIZATION.md          # Customization guide
```

## Components

### HeroSection
**Purpose**: Eye-catching hero with search functionality and key metrics

**Features**:
- Gradient background with pattern overlay
- Search input with quick search options
- Stats display (customizable metrics)
- Responsive design

**Usage**:
```tsx
import { HeroSection } from '@/components/home/HeroSection'

<HeroSection />
```

**Customization**:
- Edit `quickSearchOptions` array for search chips
- Modify gradient colors in className
- Update stats in the stats grid section

### CategoryGrid
**Purpose**: Display categories with icons, descriptions, and featured items

**Features**:
- 6 pre-configured categories with icons
- Hover effects and animations
- Count badges
- Featured items display
- Responsive grid (1/2/3 columns)

**Usage**:
```tsx
import { CategoryGrid } from '@/components/home/CategoryGrid'

<CategoryGrid />
```

**Customization**:
- Edit `categories` array to add/modify categories
- Change icons from Lucide React library
- Update colors and descriptions

### StatsSection
**Purpose**: Trust indicators and key metrics

**Features**:
- 4 stat cards with icons
- Gradient background
- Trust badges
- Feature highlights

**Usage**:
```tsx
import { StatsSection } from '@/components/home/StatsSection'

<StatsSection />
```

**Customization**:
- Modify `stats` array for different metrics
- Update trust messages in the grid
- Change background gradient

### Navigation
**Purpose**: Sticky header with dropdown menus

**Features**:
- Logo with icon
- Desktop dropdown menu (Categories)
- Mobile hamburger menu
- Search button
- Smooth transitions

**Usage**:
```tsx
import { Navigation } from '@/components/layout/navigation'

<Navigation />
```

**Customization**:
- Update `navigation` array for menu items
- Modify `categoryDropdown` for dropdown items
- Change logo in the header section

## Styling System

### Color Palette

The template uses a primary blue color scheme:

```css
--color-primary-600: #2563eb (Primary Blue)
--color-primary-700: #1d4ed8 (Hover Blue)
--color-success-600: #059669 (Success Green)
```

### Custom CSS Classes

**Buttons**:
- `.btn-primary` - Primary button style
- `.btn-lg` - Large button variant

**Layout**:
- `.container-responsive` - Responsive container with max-width

### Tailwind Configuration

Colors are defined in `globals.css` using the `@theme` directive for Tailwind v4 compatibility.

## Quick Start

### 1. Copy Template to Your Project

```bash
# From your Next.js project root
cp -r /path/to/templates/directory-ui-template/components ./src/
cp /path/to/templates/directory-ui-template/styles/globals.css ./src/app/
cp /path/to/templates/directory-ui-template/layout.tsx ./src/app/
cp /path/to/templates/directory-ui-template/page.tsx ./src/app/
```

### 2. Install Dependencies

```bash
npm install lucide-react clsx
```

### 3. Update Metadata

Edit `src/app/layout.tsx`:

```tsx
export const metadata: Metadata = {
  title: 'Your Directory Name',
  description: 'Your directory description',
  // ... update other fields
}
```

### 4. Customize Content

1. **Categories**: Edit `CategoryGrid.tsx` - Update categories array
2. **Hero Text**: Edit `HeroSection.tsx` - Update heading and description
3. **Stats**: Edit `StatsSection.tsx` - Update stats array
4. **Navigation**: Edit `navigation.tsx` - Update menu items
5. **Colors**: Edit `globals.css` - Update color variables

### 5. Start Development Server

```bash
npm run dev
```

## SEO Features

### Metadata
- Comprehensive Open Graph tags
- Twitter Card support
- Canonical URLs
- Robots meta tags

### Structured Data
- Schema.org WebSite markup
- SearchAction for search engines
- JSON-LD format

### Performance
- Optimized CSS (no @apply overhead)
- Responsive images
- Minimal JavaScript
- Fast page loads

## Accessibility

- Semantic HTML5 elements
- ARIA labels for screen readers
- Keyboard navigation support
- Focus indicators
- High contrast mode support
- Reduced motion support

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Responsive Breakpoints

- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

## Common Customizations

### Change Primary Color

Edit `globals.css`:

```css
@theme {
  --color-primary-600: #your-color;
  --color-primary-700: #your-hover-color;
}
```

### Add New Category

Edit `CategoryGrid.tsx`:

```tsx
{
  name: 'Your Category',
  slug: 'your-category',
  description: 'Category description',
  icon: YourIcon, // from lucide-react
  color: 'bg-blue-500',
  count: 100,
  featured: ['Item 1', 'Item 2', 'Item 3', 'Item 4']
}
```

### Change Hero Gradient

Edit `HeroSection.tsx`:

```tsx
<section className="relative bg-gradient-to-br from-[your-color] via-[your-color] to-[your-color]">
```

### Update Search Options

Edit `HeroSection.tsx`:

```tsx
const quickSearchOptions = [
  { label: 'Your Option', value: 'your-value', category: 'your-category' },
  // ...
]
```

## Production Checklist

- [ ] Update all metadata in layout.tsx
- [ ] Replace placeholder text and images
- [ ] Update color scheme if needed
- [ ] Test all responsive breakpoints
- [ ] Run accessibility audit
- [ ] Optimize images
- [ ] Test SEO with Lighthouse
- [ ] Configure sitemap
- [ ] Add analytics
- [ ] Set up error tracking

## Support & Resources

- **Next.js Docs**: https://nextjs.org/docs
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Lucide Icons**: https://lucide.dev

## Version History

- **v1.0** (October 2025) - Initial template creation
  - Hero with search
  - Category grid
  - Stats section
  - Responsive navigation
  - SEO optimization

## License

This template is part of your personal claudec system for use in your projects.

---

**Template Created By**: Claude Code with dirKidSports Design Framework
**Last Updated**: October 2025
