# UI System Specification

## Purpose

Define consistent, accessible theming and component presentation for the Open Agent Mail browser client.

## Requirements

### Requirement: Semantic design tokens

The interface SHALL style surfaces, text, borders, controls, focus rings, status colors, radii, and shadows through semantic CSS custom properties.

#### Scenario: Brand palette changes

- **GIVEN** the semantic primary token is changed
- **WHEN** the interface renders
- **THEN** primary buttons, selected navigation, focus indicators, and status accents SHALL update without per-component color edits

### Requirement: Theme preference

The interface SHALL support system, light, and dark themes and SHALL persist an explicit user preference locally.

#### Scenario: First visit follows system

- **GIVEN** no saved preference exists
- **WHEN** the application loads
- **THEN** it SHALL follow `prefers-color-scheme`

#### Scenario: User changes theme

- **GIVEN** the application is open
- **WHEN** the user activates the theme control
- **THEN** the interface SHALL switch theme immediately
- **AND** SHALL use that preference on the next visit

### Requirement: Visible interaction states

Every interactive control SHALL provide visible hover, keyboard focus, active or selected, and disabled states as applicable.

#### Scenario: Keyboard navigation

- **GIVEN** a keyboard user tabs through the interface
- **WHEN** focus enters a button, input, tab, mailbox, or dialog control
- **THEN** a high-contrast focus ring SHALL be visible

### Requirement: Consistent component surfaces

Cards, dialogs, menus, rows, inputs, tabs, badges, and buttons SHALL use shared radius, border, spacing, type, and elevation conventions.

#### Scenario: Dialog opens

- **WHEN** Compose, Contacts, Message, or Help opens
- **THEN** it SHALL use the shared dialog surface and backdrop treatment
- **AND** destructive actions SHALL remain visually distinct from primary actions

### Requirement: Responsive application shell

The application SHALL remain usable without horizontal page scrolling at viewport widths from 360 pixels upward.

#### Scenario: Narrow viewport

- **GIVEN** a 360-pixel-wide viewport
- **WHEN** the mailbox interface renders
- **THEN** navigation, statistics, compose, message rows, contacts, and help content SHALL remain accessible

### Requirement: Reduced motion

The interface SHALL respect the user's reduced-motion preference.

#### Scenario: Reduced motion enabled

- **GIVEN** `prefers-reduced-motion: reduce`
- **WHEN** dialogs, toasts, hover states, or theme changes render
- **THEN** nonessential transitions and animations SHALL be disabled
