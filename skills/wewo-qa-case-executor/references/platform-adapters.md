# Platform adapters

Read only the section for each selected target.

## Web

Prefer Playwright CLI or Playwright MCP when available. Use structured accessibility snapshots and stable semantic locators before screenshots or raw coordinates. Keep one controlled browser context per isolation boundary, verify navigation and user-visible state, and capture a screenshot or saved snapshot for failures and required pass evidence.

Use general computer control only when browser automation cannot reach a required browser-owned surface such as a native picker, and record the route change.

## Android and iOS mobile apps

Execute only when the selected target identifies the OS, build, and device mode, and an authorized mobile automation or device-control capability is available. A simulator/emulator result does not prove real-device behavior when the requirement names physical hardware, sensors, push delivery, permissions, biometrics, camera, or platform services.

Do not substitute Android execution for iOS or the reverse. Record OS version, device or simulator model, application build, and automation route. If the environment lacks an iOS-capable host/device or required signing/access, mark the iOS pair blocked.

## Windows, macOS, or Linux desktop apps

Distinguish a native desktop client from a website opened on that operating system. Use an authorized desktop automation or computer-control tool and record application build plus OS version. Prefer semantic accessibility identifiers; use coordinates only when stable semantics are unavailable and corroborate the final state.

Do not treat a browser run as evidence for the native client unless the case and project profile explicitly define that equivalence.

## Mini-program or other surfaces

Use only a project-approved host, device, and control capability. Record the host application and version. If no reliable route can perform both the interaction and oracle, mark the pair conditional/blocked or manual/not-run according to the manifest; do not improvise a different platform.
