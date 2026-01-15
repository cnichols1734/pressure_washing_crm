# Dark Mode Implementation Guide for AquaCRM

## Overview
Dark mode has been implemented at the base template level (`base.html`). This guide explains how to update your existing pages to support dark mode.

## What's Already Done
1. **Base Template**: Dark mode toggle, localStorage persistence, and Alpine.js integration
2. **Navigation**: Full dark mode support with smooth transitions
3. **Flash Messages**: Dark mode variants for all message types
4. **Footer**: Dark mode styling

## How Dark Mode Works
- Uses Tailwind's `dark:` prefix for dark mode styles
- Controlled by Alpine.js state stored in localStorage
- Applies `dark` class to `<html>` element when enabled
- Smooth transitions between light and dark modes

## Updating Your Pages

### 1. Background Colors
Replace single color classes with dark mode variants:
```html
<!-- Before -->
<div class="bg-white">

<!-- After -->
<div class="bg-white dark:bg-gray-800">
```

Common replacements:
- `bg-white` → `bg-white dark:bg-gray-800`
- `bg-gray-50` → `bg-gray-50 dark:bg-gray-900`
- `bg-gray-100` → `bg-gray-100 dark:bg-gray-800`
- `bg-slate-50` → `bg-slate-50 dark:bg-slate-900`

### 2. Text Colors
```html
<!-- Before -->
<p class="text-gray-900">

<!-- After -->
<p class="text-gray-900 dark:text-gray-100">
```

Common replacements:
- `text-gray-900` → `text-gray-900 dark:text-gray-100`
- `text-gray-700` → `text-gray-700 dark:text-gray-300`
- `text-gray-600` → `text-gray-600 dark:text-gray-400`
- `text-gray-500` → `text-gray-500 dark:text-gray-400`
- `text-slate-900` → `text-slate-900 dark:text-slate-100`

### 3. Border Colors
```html
<!-- Before -->
<div class="border border-gray-200">

<!-- After -->
<div class="border border-gray-200 dark:border-gray-700">
```

Common replacements:
- `border-gray-200` → `border-gray-200 dark:border-gray-700`
- `border-gray-300` → `border-gray-300 dark:border-gray-600`
- `border-slate-200` → `border-slate-200 dark:border-slate-700`

### 4. Ring/Shadow Colors
```html
<!-- Before -->
<div class="ring-1 ring-black/5">

<!-- After -->
<div class="ring-1 ring-black/5 dark:ring-white/10">
```

### 5. Hover States
```html
<!-- Before -->
<button class="hover:bg-gray-50">

<!-- After -->
<button class="hover:bg-gray-50 dark:hover:bg-gray-700">
```

### 6. Focus States
```html
<!-- Before -->
<input class="focus:ring-blue-500">

<!-- After -->
<input class="focus:ring-blue-500 dark:focus:ring-blue-400">
```

## Dashboard-Specific Updates

For your dashboard, here are the key changes needed:

### Stats Cards
```html
<!-- Update the gradient background -->
<div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-slate-900 dark:via-gray-900 dark:to-slate-900">

<!-- Update card backgrounds -->
<div class="rounded-2xl bg-white dark:bg-gray-800">

<!-- Update text colors in cards -->
<p class="text-slate-900 dark:text-slate-100">
```

### Welcome Banner
The dark gradient banner might need adjustment:
```html
<!-- Consider lightening the gradient for dark mode -->
<div class="absolute inset-0 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800">
```

### Activity Feed
```html
<!-- Update activity item backgrounds -->
<div class="p-6 hover:bg-slate-50 dark:hover:bg-gray-700">

<!-- Update icon container backgrounds -->
<div class="rounded-xl bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900 dark:to-blue-800">
```

## Form Elements

### Input Fields
```html
<input class="bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
```

### Select Dropdowns
```html
<select class="bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100">
```

### Buttons
```html
<!-- Primary button -->
<button class="bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white">

<!-- Secondary button -->
<button class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100">
```

## Tables
```html
<!-- Table header -->
<thead class="bg-gray-50 dark:bg-gray-700">

<!-- Table rows -->
<tr class="hover:bg-gray-50 dark:hover:bg-gray-700">

<!-- Table borders -->
<td class="border-b border-gray-200 dark:border-gray-700">
```

## Best Practices

1. **Test Both Modes**: Always check your changes in both light and dark modes
2. **Maintain Contrast**: Ensure text remains readable in both modes
3. **Consistent Patterns**: Use the same dark mode color mappings throughout
4. **Smooth Transitions**: The base template includes transitions for color changes
5. **Respect User Preference**: Dark mode preference is saved in localStorage

## Quick Testing
To quickly test dark mode:
1. Click the moon/sun icon in the navigation
2. Or in browser console: `document.documentElement.classList.toggle('dark')`

## Color Palette Reference

### Grays (Light → Dark)
- `gray-50` → `gray-900`
- `gray-100` → `gray-800`
- `gray-200` → `gray-700`
- `gray-300` → `gray-600`
- `gray-400` → `gray-500`
- `gray-500` → `gray-400`
- `gray-600` → `gray-300`
- `gray-700` → `gray-200`
- `gray-800` → `gray-100`
- `gray-900` → `gray-50`

### Accent Colors
Most accent colors (blue, green, red, etc.) should use a lighter shade in dark mode:
- `blue-600` → `blue-400`
- `green-600` → `green-400`
- `red-600` → `red-400`

## FOUC (Flash of Unstyled Content) Prevention

The base template includes a fix to prevent the brief flash of light mode when navigating between pages in dark mode. This is handled by:

1. **Synchronous Script**: A script in the `<head>` that runs immediately to apply the `dark` class before any content renders
2. **System Preference Detection**: Automatically respects the user's system dark mode preference on first visit
3. **Alpine.js Integration**: Seamlessly works with the existing Alpine.js dark mode toggle

This ensures smooth, flash-free dark mode transitions across all pages.

## Need Help?
If you encounter any specific scenarios not covered here, the pattern is generally:
1. Darker backgrounds become lighter in dark mode
2. Lighter text becomes darker in dark mode
3. Reduce contrast slightly for dark mode (easier on the eyes)
4. Test readability in both modes 