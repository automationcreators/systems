# Directory UI Template - File Index

Complete index of all template files and their purposes.

## Template Information

**Name**: Directory UI Template
**Version**: 1.0
**Created**: October 2025
**Last Updated**: October 2025
**Source**: dirTechStack + dirKidSports Design
**Tech Stack**: Next.js 15, Tailwind CSS v4, TypeScript, Lucide React

---

## File Structure

```
directory-ui-template/
├── components/
│   ├── home/
│   │   ├── HeroSection.tsx           [156 lines] Hero with search & stats
│   │   ├── CategoryGrid.tsx          [167 lines] Category cards display
│   │   └── StatsSection.tsx          [131 lines] Statistics section
│   └── layout/
│       └── navigation.tsx             [214 lines] Header navigation
├── styles/
│   └── globals.css                    [109 lines] Global styles & theme
├── docs/
│   ├── README.md                      [400+ lines] Main documentation
│   ├── CUSTOMIZATION.md               [500+ lines] Customization guide
│   └── TEMPLATE_INDEX.md              [This file] File index
├── layout.tsx                         [96 lines]  Root layout & SEO
├── page.tsx                           [49 lines]  Home page composition
└── TEMPLATE_INDEX.md
```

---

## Component Details

### HeroSection.tsx
**Location**: `components/home/HeroSection.tsx`
**Purpose**: Hero section with search functionality
**Dependencies**:
- `lucide-react` (Search, MapPin, Star, Users icons)
- `next/navigation` (useRouter)

**Key Features**:
- Gradient background with pattern overlay
- Search input with submit handler
- Quick search option chips
- Three stat displays
- Fully responsive

**Props**: None (self-contained)

**Customization Points**:
- Line 13-19: Quick search options array
- Line 59-62: Main heading text
- Line 65-68: Subheading text
- Line 78: Search placeholder
- Line 107-149: Stats grid

---

### CategoryGrid.tsx
**Location**: `components/home/CategoryGrid.tsx`
**Purpose**: Display categories in responsive grid
**Dependencies**:
- `lucide-react` (Code, Palette, Brain, BarChart, Megaphone, Zap icons)
- `next/link` (Link component)

**Key Features**:
- 6 pre-configured categories
- Icon + description + count
- Featured items badges
- Hover effects with transitions
- Color-coded categories

**Props**: None (self-contained)

**Customization Points**:
- Line 11-84: Categories array configuration
- Line 88: Grid column configuration

---

### StatsSection.tsx
**Location**: `components/home/StatsSection.tsx`
**Purpose**: Display key statistics and trust indicators
**Dependencies**:
- `lucide-react` (Users, MapPin, Star, TrendingUp icons)

**Key Features**:
- 4 stat cards with icons
- Pattern background overlay
- Trust messages grid
- Achievement badges
- Gradient blue background

**Props**: None (self-contained)

**Customization Points**:
- Line 8-41: Stats array
- Line 63-110: Stats grid
- Line 91-109: Trust messages
- Line 114-126: Badge labels

---

### navigation.tsx
**Location**: `components/layout/navigation.tsx`
**Purpose**: Header navigation with menus
**Dependencies**:
- `lucide-react` (Menu, X, Search, Star icons)
- `next/link` (Link component)
- `next/navigation` (usePathname)
- `clsx` (className utility)

**Key Features**:
- Logo with star icon
- Desktop menu with dropdown
- Mobile hamburger menu
- Search button
- Sticky header
- Active page highlighting

**Props**: None (self-contained)

**Customization Points**:
- Line 9-15: Navigation menu items
- Line 17-24: Category dropdown items
- Line 40-50: Logo section

---

## Style Files

### globals.css
**Location**: `styles/globals.css`
**Purpose**: Global styles, theme colors, custom classes
**Size**: 109 lines

**Contents**:
- **@theme directive**: Color palette definition (lines 3-26)
  - Primary colors (blue scale)
  - Success colors (green scale)

- **Custom Classes** (lines 28-80):
  - `.btn-primary`: Primary button style
  - `.btn-lg`: Large button variant
  - `.container-responsive`: Responsive container

- **Animations** (lines 82-108):
  - `fadeIn`: Fade in animation
  - `slideUp`: Slide up animation
  - `scaleIn`: Scale in animation

**Customization**: Edit color values in `@theme` block

---

## Layout Files

### layout.tsx
**Location**: Root directory
**Purpose**: Root layout with SEO metadata
**Size**: 96 lines

**Contents**:
- **Metadata** (lines 9-53): Complete SEO configuration
  - Title, description, keywords
  - Open Graph tags
  - Twitter Card tags
  - Robots directives

- **Structured Data** (lines 68-84): JSON-LD schema
- **Layout Structure** (lines 86-94): HTML structure with Navigation/Footer

**Customization**: Update all metadata fields for your site

---

### page.tsx
**Location**: Root directory
**Purpose**: Home page composition
**Size**: 49 lines

**Contents**:
- Hero section import & render
- Categories section with heading
- Stats section
- CTA section

**Structure**:
```tsx
<HeroSection />
<section> Categories </section>
<StatsSection />
<section> CTA </section>
```

**Customization**: Add/remove/reorder sections

---

## Documentation Files

### README.md
**Location**: `docs/README.md`
**Purpose**: Main template documentation
**Sections**:
- Overview & features
- Tech stack
- File structure
- Component usage
- Quick start guide
- SEO features
- Accessibility
- Production checklist

---

### CUSTOMIZATION.md
**Location**: `docs/CUSTOMIZATION.md`
**Purpose**: Detailed customization guide
**Sections**:
- Branding & identity
- Color scheme
- Content customization
- Component modifications
- Layout adjustments
- Advanced customization
- Troubleshooting

---

### TEMPLATE_INDEX.md
**Location**: `docs/TEMPLATE_INDEX.md`
**Purpose**: Complete file index (this file)

---

## Usage Instructions

### Quick Setup (5 minutes)

1. **Copy files to your Next.js project**:
   ```bash
   cp -r components/ src/
   cp styles/globals.css src/app/
   cp layout.tsx src/app/
   cp page.tsx src/app/
   ```

2. **Install dependencies**:
   ```bash
   npm install lucide-react clsx
   ```

3. **Update metadata** in `layout.tsx`

4. **Customize content** in components

5. **Start dev server**:
   ```bash
   npm run dev
   ```

### Full Setup (30 minutes)

Follow the complete guide in [README.md](README.md)

---

## Dependencies

### Required
- `next`: ^15.0.0
- `react`: ^19.0.0
- `lucide-react`: ^0.400.0+
- `clsx`: ^2.0.0+
- `tailwindcss`: ^4.0.0

### Fonts
- `next/font/google` - Inter font

---

## Component Dependencies Tree

```
layout.tsx
├── Navigation
│   └── lucide-react (Menu, X, Search, Star)
│   └── next/link
│   └── next/navigation
│   └── clsx
└── page.tsx
    ├── HeroSection
    │   └── lucide-react (Search, MapPin, Star, Users)
    │   └── next/navigation
    ├── CategoryGrid
    │   └── lucide-react (Code, Palette, Brain, etc.)
    │   └── next/link
    └── StatsSection
        └── lucide-react (Users, MapPin, Star, TrendingUp)
```

---

## File Sizes

| File | Lines | Size (approx) |
|------|-------|---------------|
| HeroSection.tsx | 156 | 4.2 KB |
| CategoryGrid.tsx | 167 | 5.1 KB |
| StatsSection.tsx | 131 | 3.8 KB |
| navigation.tsx | 214 | 6.5 KB |
| globals.css | 109 | 2.1 KB |
| layout.tsx | 96 | 3.0 KB |
| page.tsx | 49 | 1.2 KB |
| **Total** | **922** | **~26 KB** |

---

## Color Palette Reference

### Primary (Blue)
- 50: `#eff6ff`
- 100: `#dbeafe`
- 200: `#bfdbfe`
- 300: `#93c5fd`
- 400: `#60a5fa`
- 500: `#3b82f6`
- **600: `#2563eb`** ← Primary
- **700: `#1d4ed8`** ← Hover
- 800: `#1e40af`
- 900: `#1e3a8a`

### Success (Green)
- **600: `#059669`** ← Success
- 700: `#047857`

---

## Icon Reference

All icons from **lucide-react**:

**Navigation**: Menu, X, Search, Star
**Hero**: Search, MapPin, Star, Users
**Categories**: Code, Palette, Brain, BarChart, Megaphone, Zap
**Stats**: Users, MapPin, Star, TrendingUp

View all icons: https://lucide.dev

---

## Browser Support

✅ Chrome/Edge 90+
✅ Firefox 90+
✅ Safari 14+
✅ iOS Safari 14+
✅ Chrome Mobile 90+

---

## Performance Metrics

**Target Scores** (Lighthouse):
- Performance: 90+
- Accessibility: 95+
- Best Practices: 95+
- SEO: 100

**Bundle Size** (estimated):
- Components: ~26 KB
- CSS: ~2 KB
- Total: ~28 KB (before minification)

---

## Version History

**v1.0** - October 2025
- Initial template creation
- Hero with search
- Category grid
- Stats section
- Navigation with dropdown
- Complete documentation

---

## Template Metadata

```json
{
  "name": "directory-ui-template",
  "version": "1.0.0",
  "type": "ui-framework",
  "framework": "nextjs",
  "styling": "tailwindcss-v4",
  "icons": "lucide-react",
  "responsive": true,
  "seo-optimized": true,
  "accessibility": "wcag-2.1-aa",
  "created": "2025-10",
  "components": 4,
  "total-lines": 922,
  "documentation-pages": 3
}
```

---

**Last Updated**: October 2025
**Maintained By**: Claude Code Systems
**Template Location**: `systems/templates/directory-ui-template/`
