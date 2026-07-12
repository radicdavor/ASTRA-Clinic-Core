# ASTRA Clinical Module SDK 1.0

Clinical Module SDK defines a safe, versioned, data-only contract for specialty modules.

Required manifest: `module.json` with `name`, `display_name`, `version`, `sdk_version`, `min_core_version`, `capabilities`, `permissions`, and `enabled`.

Allowed capabilities: services, material templates, workflows, patient instructions, and knowledge protocols. Every declared capability requires its corresponding JSON file. Unknown capabilities fail validation. Write/admin permissions produce a security-review warning.

The SDK never imports or executes Python, JavaScript, binaries, shell commands, migrations, or remote code from a module. Enable/disable actions require admin authority and are audited.

Registry API:

- `GET /api/modules/registry`
- `POST /api/modules/{key}/validate`
- `POST /api/modules/{key}/enable`
- `POST /api/modules/{key}/disable`

The `/modules` workspace shows compatibility, declared capabilities, permissions, validation findings, installation state, and controlled lifecycle actions.
