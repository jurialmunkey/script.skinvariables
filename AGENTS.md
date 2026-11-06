# Coding conventions

These guidelines apply throughout this repository. Match the existing architecture
when adding or extending functionality.

## Commit messages

- Prefix every commit subject with an appropriate emoji shortcode, matching the
  existing history (for example, `:bug:` for fixes, `:sparkles:` for new features,
  `:zap:` for improvements, `:bookmark:` for version bumps, and `:robot:` for
  agent instructions).
- Follow the shortcode with a space and a concise description of the change.
- Commit messages are always a single line: the emoji shortcode and the
  description only. Never add a body, bullet points, extended description,
  `Co-Authored-By` or other attribution trailers, or any other lines.

## Organization and reuse

- Use hanging indents only when the single-line form exceeds the applicable
  line-length limit. Leave the opening delimiter's line empty of arguments or
  entries, then put one argument, parameter, collection element, or dictionary
  key-value pair per line. Use four-space continuation indents. Put closing
  parentheses, brackets, and braces on separate lines aligned with the opening
  line's indentation. Use trailing commas where valid. Apply the same rules to
  nested collections that require wrapping.
- In wrapped comprehensions and generator expressions, put the result
  expression and each `for` or `if` clause on separate lines at the same
  hanging-indent level.
- Always use explicitly named absolute imports. Relative imports and wildcard
  (`from ... import *`) imports are not permitted.
- Keep distinct features in appropriately named modules.
- Update affected imports and references when moving or renaming classes or
  modules. Remove unused imports and obsolete references.
- Reuse existing helpers and abstractions where applicable.
- Implement object oriented programming (OOP) practices where practical. Create
  classes with properties. Use abstractions, inheritance, and subclassing.
- Prefer small subclasses for variations. Override the differing behavior and
  inherit shared logic.
- Encapsulate related data transformation and result assembly in a focused
  helper class. Initialise it with the source data and required configuration.
- Expose derived values and the assembled result through named properties.
  Build results from those properties, keeping intermediate calculations on
  the instance rather than passing the same data between helper functions.
- Keep each calculation small and single-purpose. Put calculation logic in
  `get_x()` methods, with the corresponding properties returning their results.
- Use `cached_property` for derived values that remain valid for the configured
  instance and benefit from reuse; use `property` for values that must reflect
  changing state. Configure attributes before accessing cached properties.
  Create a new instance when changing inputs would invalidate cached results.
- Follow EAFP programming principles. Avoid using guards to deal with errors
  arising from unexpected or misconfigured data. Investigate the underlying
  cause instead of masking the error.
- Prefer flat structures. Avoid nesting loops. Prefer comprehensions if possible.
- Keep methods simple and single-purpose. Avoid god functions or classes. Break
  complex code into smaller abstracted parts.

## Changes to shared classes

- Inspect the affected data flow, relevant base classes, and callers before
  changing behavior. Identify which layer and class should own each part of
  the change.
- Put feature-specific behavior in the appropriate concrete class or subclass.
  Modify a shared base class only when the behavior belongs to all affected
  subclasses; use existing extension points for variations.
- Before changing a shared class, inspect its subclasses, overrides, and callers.
  Confirm that the behavior belongs in the shared abstraction and consider how
  it affects existing consumers.
- Preserve the shared class's contract. Do not add feature-specific branches to
  shared infrastructure to avoid implementing the appropriate subclass behavior.

## Verification

- Before reporting completion, review the completed diff. Check that each change
  belongs to its owning layer and follows the existing architecture and extension
  points.
- Review affected imports, references, and cache configuration order. Confirm
  that attributes are configured before cached properties are accessed.
- For shared-class changes, review the effect on existing subclasses, overrides,
  and callers, including consumers outside the requested feature.
- Correct architectural violations before reporting completion. Briefly report
  the review and any unresolved limitations alongside the verification results.
- Check syntax, whitespace, and imports for affected modules. Use in-memory
  compilation when bytecode writes are unavailable.
- Verify meaningful edge cases relevant to the change, including empty or missing
  data, zero totals, and range boundaries where applicable.
- Preserve existing behavior unless the requested change calls for altering it.
  State which checks ran and distinguish isolated checks from testing in Kodi.
- Never write tests in files in the codebase.
