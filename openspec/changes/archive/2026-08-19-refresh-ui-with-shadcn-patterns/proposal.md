# Refresh UI with shadcn patterns

## Why

The current interface is functional but its styles are monolithic, its visual states are inconsistent, and it has no theme preference. Adopting shadcn/ui's semantic token and component patterns will make the product more cohesive and accessible without forcing a React migration or adding runtime dependencies.

## What changes

- Introduce semantic color, radius, shadow, focus-ring, and sidebar tokens modeled on shadcn/ui theming.
- Restyle the shell, cards, tabs, inputs, buttons, dialogs, message rows, contacts, and help center consistently.
- Add light, dark, and system theme behavior with a persistent user choice.
- Improve hover, focus-visible, selected, unread, empty, and destructive states.
- Improve mobile spacing and navigation behavior.
- Keep the existing HTML and JavaScript behavior and the zero-build static asset model.

## Capabilities

### New capabilities

- `ui-system`: semantic theming and consistent interactive component behavior.

### Modified capabilities

- None. Mailbox, message, contact, and help-center behavior is unchanged.

## Impact

- Adds one CSS theme layer and a small theme-preference controller.
- Updates the application shell markup with a theme control and accessibility metadata.
- Does not add React, Tailwind, Radix, package-manager, build, or Python runtime dependencies.

## Out of scope

- Importing shadcn/ui React source components.
- Migrating the browser application to React/Vite.
- Changing API or mailbox behavior.
