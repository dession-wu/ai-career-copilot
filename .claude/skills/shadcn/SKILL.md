---
name: shadcn
description: |
  shadcn/ui skill for managing and using shadcn/ui components.
  Provides guidelines for adding, updating, and composing shadcn/ui components
  in React/Next.js projects using Tailwind CSS.
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
---

# shadcn/ui Components & Design System

A framework for building ui, components and design systems. Components are added as source code to the user's project via the CLI.

> **IMPORTANT:** Run all CLI commands using the project's package runner: `npx shadcn@latest`, `pnpm dlx shadcn@latest`, or `bunx --bun shadcn@latest` — based on the project's `packageManager`. Examples below use `npx shadcn@latest` but substitute the correct runner for the project.

## Current Project Context

When working with shadcn/ui, first get the project context:

```bash
npx shadcn@latest info --json
```

The JSON above contains the project config and installed components. Use `npx shadcn@latest docs <component>` to get documentation and example URLs for any component.

## Principles

1. **Use existing components first.** Use `npx shadcn@latest search` to check registries before writing custom UI. Check community registries too.
2. **Compose, don't reinvent.** Settings page = Tabs + Card + form controls. Dashboard = Sidebar + Card + Chart + Table.
3. **Use built-in variants before custom styles.** `variant="outline"`, `size="sm"`, etc.
4. **Use semantic colors.** `bg-primary`, `text-muted-foreground` — never raw values like `bg-blue-500`.

## Critical Rules

### Styling & Tailwind

* **`className` for layout, not styling.** Never override component colors or typography.
* **No `space-x-*` or `space-y-*`.** Use `flex` with `gap-*`. For vertical stacks, `flex flex-col gap-*`.
* **Use `size-*` when width and height are equal.** `size-10` not `w-10 h-10`.
* **Use `truncate` shorthand.** Not `overflow-hidden text-ellipsis whitespace-nowrap`.
* **No manual `dark:` color overrides.** Use semantic tokens (`bg-background`, `text-muted-foreground`).
* **Use `cn()` for conditional classes.** Don't write manual template literal ternaries.
* **No manual `z-index` on overlay components.** Dialog, Sheet, Popover, etc. handle their own stacking.

### Forms & Inputs

* **Forms use `FieldGroup` + `Field`.** Never use raw `div` with `space-y-*` or `grid gap-*` for form layout.
* **`InputGroup` uses `InputGroupInput`/`InputGroupTextarea`.** Never raw `Input`/`Textarea` inside `InputGroup`.
* **Buttons inside inputs use `InputGroup` + `InputGroupAddon`.**
* **Option sets (2–7 choices) use `ToggleGroup`.** Don't loop `Button` with manual active state.
* **`FieldSet` + `FieldLegend` for grouping related checkboxes/radios.** Don't use a `div` with a heading.
* **Field validation uses `data-invalid` + `aria-invalid`.** `data-invalid` on `Field`, `aria-invalid` on the control. For disabled: `data-disabled` on `Field`, `disabled` on the control.

### Component Structure

* **Items always inside their Group.** `SelectItem` → `SelectGroup`. `DropdownMenuItem` → `DropdownMenuGroup`. `CommandItem` → `CommandGroup`.
* **Use `asChild` (radix) or `render` (base) for custom triggers.**
* **Dialog, Sheet, and Drawer always need a Title.** `DialogTitle`, `SheetTitle`, `DrawerTitle` required for accessibility. Use `className="sr-only"` if visually hidden.
* **Use full Card composition.** `CardHeader`/`CardTitle`/`CardDescription`/`CardContent`/`CardFooter`. Don't dump everything in `CardContent`.
* **Button has no `isPending`/`isLoading`.** Compose with `Spinner` + `data-icon` + `disabled`.
* **`TabsTrigger` must be inside `TabsList`.** Never render triggers directly in `Tabs`.
* **`Avatar` always needs `AvatarFallback`.** For when the image fails to load.

### Use Components, Not Custom Markup

* **Use existing components before custom markup.** Check if a component exists before writing a styled `div`.
* **Callouts use `Alert`.** Don't build custom styled divs.
* **Empty states use `Empty`.** Don't build custom empty state markup.
* **Toast via `sonner`.** Use `toast()` from `sonner`.
* **Use `Separator`** instead of `<hr>` or `<div className="border-t">`.
* **Use `Skeleton`** for loading placeholders. No custom `animate-pulse` divs.
* **Use `Badge`** instead of custom styled spans.

### Icons

* **Icons in `Button` use `data-icon`.** `data-icon="inline-start"` or `data-icon="inline-end"` on the icon.
* **No sizing classes on icons inside components.** Components handle icon sizing via CSS. No `size-4` or `w-4 h-4`.
* **Pass icons as objects, not string keys.** `icon={CheckIcon}`, not a string lookup.

### CLI

* **Never decode or fetch preset codes manually.** Pass them directly to `npx shadcn@latest init --preset <code>`.

## Key Patterns

```tsx
// Form layout: FieldGroup + Field, not div + Label.
<FieldGroup>
  <Field>
    <FieldLabel htmlFor="email">Email</FieldLabel>
    <Input id="email" />
  </Field>
</FieldGroup>

// Validation: data-invalid on Field, aria-invalid on the control.
<Field data-invalid>
  <FieldLabel>Email</FieldLabel>
  <Input aria-invalid />
  <FieldDescription>Invalid email.</FieldDescription>
</Field>

// Icons in buttons: data-icon, no sizing classes.
<Button>
  <SearchIcon data-icon="inline-start" />
  Search
</Button>

// Spacing: gap-*, not space-y-*.
<div className="flex flex-col gap-4">  // correct
<div className="space-y-4">           // wrong

// Equal dimensions: size-*, not w-* h-*.
<Avatar className="size-10">   // correct
<Avatar className="w-10 h-10"> // wrong

// Status colors: Badge variants or semantic tokens, not raw colors.
<Badge variant="secondary">+20.1%</Badge>    // correct
<span className="text-emerald-600">+20.1%</span> // wrong
```

## Component Selection

| Need | Use |
| --- | --- |
| Button/action | `Button` with appropriate variant |
| Form inputs | `Input`, `Select`, `Combobox`, `Switch`, `Checkbox`, `RadioGroup`, `Textarea`, `InputOTP`, `Slider` |
| Toggle between 2–5 options | `ToggleGroup` + `ToggleGroupItem` |
| Data display | `Table`, `Card`, `Badge`, `Avatar` |
| Navigation | `Sidebar`, `NavigationMenu`, `Breadcrumb`, `Tabs`, `Pagination` |
| Overlays | `Dialog` (modal), `Sheet` (side panel), `Drawer` (bottom sheet), `AlertDialog` (confirmation) |
| Feedback | `sonner` (toast), `Alert`, `Progress`, `Skeleton`, `Spinner` |
| Command palette | `Command` inside `Dialog` |
| Charts | `Chart` (wraps Recharts) |
| Layout | `Card`, `Separator`, `Resizable`, `ScrollArea`, `Accordion`, `Collapsible` |
| Empty states | `Empty` |
| Menus | `DropdownMenu`, `ContextMenu`, `Menubar` |
| Tooltips/info | `Tooltip`, `HoverCard`, `Popover` |

## Key Fields

The injected project context contains these key fields:

* **`aliases`** → use the actual alias prefix for imports (e.g. `@/`, `~/`), never hardcode.
* **`isRSC`** → when `true`, components using `useState`, `useEffect`, event handlers, or browser APIs need `"use client"` at the top of the file.
* **`tailwindVersion`** → `"v4"` uses `@theme inline` blocks; `"v3"` uses `tailwind.config.js`.
* **`tailwindCssFile`** → the global CSS file where custom CSS variables are defined.
* **`style`** → component visual treatment (e.g. `nova`, `vega`).
* **`base`** → primitive library (`radix` or `base`).
* **`iconLibrary`** → determines icon imports. Use `lucide-react` for `lucide`, `@tabler/icons-react` for `tabler`, etc.
* **`resolvedPaths`** → exact file-system destinations for components, utils, hooks, etc.
* **`framework`** → routing and file conventions (e.g. Next.js App Router vs Vite SPA).
* **`packageManager`** → use this for any non-shadcn dependency installs.

## Workflow

1. **Get project context** — run `npx shadcn@latest info`.
2. **Check installed components first** — check the `components` list from project context.
3. **Find components** — `npx shadcn@latest search`.
4. **Get docs and examples** — run `npx shadcn@latest docs <component>` to get URLs.
5. **Install or update** — `npx shadcn@latest add <component>`.
6. **Fix imports in third-party components** — check and rewrite imports if needed.
7. **Review added components** — verify files are correct after adding.

## Quick Reference

```bash
# Create a new project
npx shadcn@latest init --name my-app --preset base-nova

# Add a component
npx shadcn@latest add button

# Add multiple components
npx shadcn@latest add button card input

# Search for components
npx shadcn@latest search

# Get component docs
npx shadcn@latest docs button

# Check installed components
npx shadcn@latest info

# Update a component
npx shadcn@latest add button --overwrite

# Preview changes before updating
npx shadcn@latest add button --dry-run
npx shadcn@latest add button --diff
```
