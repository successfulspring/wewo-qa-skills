# Live surface discovery and test implementation

Choose the actual target surface and available supported tools. Discover operations and observation locations from the deployed system and supplied documentation. Product source is not required. Reconnaissance tools help implement durable tests; formal automation still requires running those tests with original evidence.

## Browser UI

Use available browser automation and semantic accessibility/DOM locators. Check that locators identify the correct visible subject and wait for the specified state. Use screenshots for relevant visual checks and failure evidence. General computer control is suitable only when a required surface is inaccessible to browser control, with a justified repeatable adapter.

## Interface

Use supplied API/interface documentation, authorized specifications or observed requests to identify real endpoints, authentication, payloads and response contracts. Never guess undocumented operations or derive expected behavior from a successful response. Observe the confirmed externally visible result at the required timing; an accepted asynchronous request does not prove completion.

Interface setup may support UI journeys without replacing their UI observations. Preserve non-sensitive request/response evidence. The Designer's api route and api target surface allow interface-defined cases to reach this path.

## Mobile, desktop and other clients

Use the actual installed build, operating system, device/host and available mature automation adapter. Prefer stable accessibility identifiers. Record limitations of emulators/simulators when physical hardware behavior is required. A browser result does not prove a native client or a different OS.

If the necessary device, host, signing/access or control capability is unavailable, record a specific blocker for that target and continue independent ready pairs. Merely listing a platform does not establish tested support.
