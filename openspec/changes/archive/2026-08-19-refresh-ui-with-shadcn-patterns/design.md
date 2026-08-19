# Design: shadcn-inspired UI refresh

## Decision

Adopt shadcn/ui's design-system principles, not its React implementation. The app remains static HTML/CSS/JavaScript served by Python.

Official shadcn/ui installation targets supported component frameworks such as React with Vite, and the generated components depend on Tailwind plus a React primitive layer. Migrating this small frontend solely for styling would add a build pipeline and conflict with the project's zero-runtime-dependency goal. The valuable reusable layer is its semantic token convention and consistent component anatomy.

## Token model

Add `shadcn-theme.css` after existing styles so it becomes the intentional theme/normalization layer. Define paired semantic tokens:

- `--background` / `--foreground`
- `--card` / `--card-foreground`
- `--popover` / `--popover-foreground`
- `--primary` / `--primary-foreground`
- `--secondary` / `--secondary-foreground`
- `--muted` / `--muted-foreground`
- `--accent` / `--accent-foreground`
- `--destructive` / `--destructive-foreground`
- `--border`, `--input`, `--ring`, `--radius`
- sidebar-specific surface, foreground, accent, border, and ring tokens

Use OKLCH values where supported, with the existing green brand retained as `primary`.

## Theme controller

Store `open-agent-mail-theme` as `light`, `dark`, or absent/system. The header control cycles system-derived current state to the opposite explicit theme. Apply `.dark` to `document.documentElement`, update `color-scheme`, button label, and `aria-pressed`. Listen for system changes only when no explicit preference exists.

## Component mapping

| Existing UI | shadcn pattern |
| --- | --- |
| Application navigation | Sidebar / SidebarInset |
| Mailbox header and content | Card |
| Inbox/Sent | Tabs |
| Compose, Contacts, Help, Message | Dialog |
| Message and contact rows | Item |
| Search and form fields | Input / Textarea |
| LOCAL and inbox count | Badge |
| Toast | Toast |
| Empty inbox/help search | Empty |
| Theme control | Button, ghost/icon variant |

No new data or interaction component is introduced.

## Accessibility

- Add `aria-label` and `aria-pressed` to theme control.
- Use `:focus-visible` rings rather than removing outlines globally.
- Maintain readable foreground/background contrast in both themes.
- Keep native dialogs for focus containment and Escape behavior.
- Respect reduced motion.

## Verification

- JavaScript syntax check.
- Static asset and application-shell tests.
- Existing API/integration suite.
- Live HTTP check.
- Manual desktop and 360-pixel viewport review when browser control is available.

## References

- [shadcn/ui theming](https://ui.shadcn.com/docs/theming)
- [shadcn/ui components](https://ui.shadcn.com/docs/components)
- [shadcn/ui Sidebar](https://ui.shadcn.com/docs/components/radix/sidebar)
- [shadcn/ui Vite installation](https://ui.shadcn.com/docs/installation/vite)
