# Trinity 3.0 Design Guide

## Core Design Principles

### Bloomberg Terminal Aesthetic
- **NO ICONS OR EMOJIS**: Professional financial interface without decorative symbols
- **Typography-First**: Clean hierarchy using size, weight, and color
- **Data Density**: Maximum information with minimal visual noise
- **Professional Color Palette**: Dark theme with sophisticated accent colors

## Color System

### Background & Surfaces
- **Deep Background**: `#0A0E27` - Deep space blue
- **Surface**: `#0F1629` - Slightly lighter surface
- **Surface Light**: `#141B35` - Card backgrounds

### Typography Colors
- **Primary Text**: `#E8E9F3` - Bright white-blue
- **Secondary Text**: `#A0A4B8` - Muted gray-blue
- **Tertiary Text**: `#6B7290` - Subdued gray

### Accent Colors
- **Primary Accent**: `#4A9EFF` - Bright sky blue
- **Success**: `#10B981` - Emerald green
- **Warning**: `#F59E0B` - Amber
- **Danger**: `#EF4444` - Red
- **Purple**: `#8B5CF6` - Secondary accent

### Gradients
- **Header Gradient**: `linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%)`
- **Accent Gradient**: `linear-gradient(90deg, #4A9EFF, #8B5CF6)`

## Typography

### Font Stack
- **Primary**: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
- **Monospace**: JetBrains Mono, SF Mono, Monaco, monospace

### Font Sizes
- **Hero**: 3.5rem (56px) - Main headlines
- **Display**: 2.5rem (40px) - Section headers
- **Title**: 1.875rem (30px) - Card titles
- **Heading**: 1.5rem (24px) - Subsections
- **Body**: 1rem (16px) - Body text
- **Small**: 0.875rem (14px) - Secondary text
- **Micro**: 0.75rem (12px) - Labels

### Font Weights
- **Light**: 300 - Headlines
- **Regular**: 400 - Body text
- **Medium**: 500 - Emphasis
- **Semibold**: 600 - Subheadings
- **Bold**: 700 - Strong emphasis

## Component Guidelines

### Headers
- Glass morphism effect with gradient background
- Dark overlay on gradient for readability
- Status indicators using text only (LIVE, v3.0)
- No icons in navigation or status displays

### Cards
- Sharp corners (no border-radius) for professional look
- Subtle border: 1px solid `#1E2740`
- Background: `#141B35`
- Transition animations: 0.3s cubic-bezier

### Metrics Display
- Large value display with light font weight
- Change indicators using color only (no arrows)
- Subtle background highlighting for emphasis

### Charts
- Dark background matching theme
- Grid lines in muted colors
- Consistent color palette across all visualizations
- Professional Plotly configurations

## Layout Principles

### Spacing System
- **xs**: 0.25rem (4px)
- **sm**: 0.5rem (8px)
- **md**: 1rem (16px)
- **lg**: 1.5rem (24px)
- **xl**: 2rem (32px)
- **xxl**: 3rem (48px)

### Grid System
- 12-column responsive grid
- Consistent gutters: 1.5rem
- Cards in 4-column layout for metrics
- 2-column layout for detailed analysis

## DO's and DON'Ts

### DO's
- Use color to indicate status (green for success, red for danger)
- Maintain consistent spacing throughout
- Use typography hierarchy for information architecture
- Keep interfaces clean and data-focused

### DON'Ts
- Never use emojis or icons (❌ 📊 📈 ✅ ⚠️)
- Avoid rounded corners on primary components
- Don't use decorative elements
- Never compromise data density for aesthetics

## Implementation Notes

### Streamlit Specific
- Override default Streamlit styling
- Hide default header, footer, and menu
- Custom CSS injection via markdown
- Professional theme applied globally

### Status Indicators
- Text-only status: "MARKET OPEN", "DATA CONNECTED"
- Color coding: Green for active, yellow for warning, red for error
- No animated elements or spinners

### Data Display
- Monospace fonts for numbers
- Right-align numerical data
- Consistent decimal places
- Professional number formatting

## Accessibility
- High contrast ratios (WCAG AA compliant)
- Clear visual hierarchy
- Consistent interaction patterns
- Keyboard navigation support