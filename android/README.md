# Android module (deferred)

This directory preserves the possible Android follow-up track. It is not part of the current web MVP milestones and must not be scaffolded until the user explicitly resumes it after the public web URL is stable. At that point, Kotlin, Jetpack Compose, Material 3, Hilt, Retrofit, Room, and DataStore will be re-evaluated against the existing `/api/v1` contract.

Local API addresses:

- Android Emulator: `http://10.0.2.2:8000`
- Physical device: configure the development machine's LAN address

No provider API or LLM secret may be stored in this module.
