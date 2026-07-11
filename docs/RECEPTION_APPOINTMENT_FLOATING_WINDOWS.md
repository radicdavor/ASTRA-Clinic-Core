# Reception and Appointment Floating Windows

Status: implemented for Reception and Appointments.

## Behavior

- New Appointment opens as a floating route modal when launched from Reception or Appointments.
- Appointment Detail opens as a floating route modal from the appointment list or reception selection.
- The originating screen remains rendered beneath the modal.
- The URL changes to the real appointment route.
- Direct route access and browser refresh still render the full-page fallback.
- Saving a new appointment can continue into floating Appointment Detail while preserving the original background.

## Accessibility and Safety

- semantic `role=dialog` and `aria-modal=true`
- explicit dialog title and close control
- initial focus moves to Close
- Tab and Shift+Tab remain inside the dialog
- Escape closes the dialog
- clicking the backdrop closes the dialog
- focus returns to the previous control
- background document scrolling is locked
- modal content has its own bounded scroll area
- mobile layout uses an almost full-screen panel without page-level horizontal overflow

## Scope Decision

Floating routes are applied only to short-lived create/detail work launched from Reception and Appointments. Core workspaces and unrelated modules remain full pages until their workflows are reviewed individually.

## Browser Validation

- appointment-list New Appointment modal: pass
- originating Appointments page preserved: pass
- reception empty-slot modal: pass
- date/start-time prefill: pass
- Escape close and scroll restoration: pass
- mobile 390 x 844 layout: pass
- console errors: none observed

