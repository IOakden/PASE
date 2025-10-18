# PASE Frontend Style Guide

## Design Philosophy

The PASE frontend should convey **professionalism, academic rigor, and scientific credibility**. This is a research tool for computational biology, not a consumer app.

## Core Style Rules

### 1. Professional and Academic Aesthetic
- Clean, minimal design inspired by scientific journals and research publications
- Typography-focused layout with clear hierarchy
- Ample whitespace for readability
- Conservative, research-appropriate visual language

### 2. Color Palette
**Light theme with muted, professional colors. No excessively strong or saturated colors.**

Approved color scheme:
- **Background**: Off-white and light grays (#f8f9fa, #ffffff)
- **Surface**: Very light grays (#ffffff, #f5f6f7)
- **Primary accent**: Muted blue (#4a6fa5, #5b7ba6) - NOT bright indigo/purple
- **Text**: Dark grays and slate (#1e293b, #475569)
- **Borders**: Light grays (#d1d5db, #e5e7eb)
- **Status indicators**: Muted greens/ambers (#5a8a7a, #a08958)

**Forbidden colors**:
- ❌ Bright/neon colors
- ❌ High saturation gradients
- ❌ Rainbow or playful color schemes

### 3. Typography
- Use clean, professional fonts (Inter, SF Pro, or system fonts)
- Clear hierarchy: headings should be distinguished by size and weight, not color
- Body text: 16px minimum for readability
- Line height: 1.6-1.8 for academic readability

### 4. No Emojis
**Emojis are strictly forbidden.**

Replace emojis with:
- Text labels
- Professional icons (if necessary, minimal SVG icons)
- Typography-based indicators

### 5. Sharp Corners
**No rounded corners (border-radius).**

- All elements use `border-radius: 0`
- Cards, buttons, and containers have sharp, rectangular edges
- This conveys precision and scientific rigor

### 6. Layout Principles
- **Desktop-first design**: This is a desktop research tool, not a mobile app
- **Compact layout**: Small, efficient use of space - not large mobile-style navbars
- **Maximum width**: Content should not exceed 900-1000px
- Grid-based layouts with tight, professional spacing
- Consistent spacing (use multiples of 8px)
- Clear visual separation between sections
- Avoid decorative elements and excessive padding

### 7. Interactive Elements
- Buttons: Rectangular with subtle borders
- Hover states: Minimal changes (slight background shift, border highlight)
- No animations except subtle transitions
- Focus states must be clear for accessibility

### 8. Data Visualization
- If charts/graphs are added: use muted colors, clear labels
- Scientific color schemes (sequential, diverging)
- Accessibility: ensure sufficient contrast

## Examples

### ✅ Good
```
Professional button:
- Sharp rectangular border
- Muted blue background (#5b7ba6)
- Clean sans-serif text
- Subtle hover state
```

### ❌ Bad
```
Consumer-style button:
- Rounded corners (border-radius: 12px)
- Bright gradient (purple to pink)
- Emoji icon
- Bouncy animation
```

## Component Guidelines

### Headers
- **Compact and minimal**: Small header, not large mobile-style navbar
- Simple, bold typography
- Institution/lab name styling
- Minimal padding and decoration
- Desktop-appropriate sizing

### Cards
- Sharp corners
- Subtle borders
- Muted background colors
- Clear content hierarchy

### Forms
- Clean input fields with sharp borders
- Clear labels above inputs
- Minimal visual styling
- Focus on functionality

### Status Indicators
- Use muted colors
- Text-based when possible
- Small dot indicators acceptable (no emojis)

## Accessibility

- Maintain WCAG AA contrast ratios
- Keyboard navigation must be clear
- Screen reader friendly
- No reliance on color alone for information

## Reference

Look to these for inspiration:
- Nature journal website
- PubMed interface
- Academic institution websites
- Professional data analysis tools

Avoid:
- Consumer social media apps
- Playful SaaS products
- Entertainment websites

