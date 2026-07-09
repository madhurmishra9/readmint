# Template: Mobile App

`backend/templates/mobile-app.yaml` — for an iOS/Android application.

| Section | Required |
|---|---|
| Overview | yes |
| Screenshots | no |
| Requirements | yes |
| Installation | yes |
| Building & Running | yes |
| Architecture | no |
| Testing | no |
| Release Process | no |
| License | no |

## Example README that passes this template

```markdown
# TrailLog

A mobile app for logging hikes offline and syncing them when you're back
in range.

## Overview

TrailLog records GPS tracks, photos, and notes for a hike, storing
everything locally with SQLite and syncing to the cloud when connectivity
returns. Built with React Native for iOS and Android.

## Screenshots

| Track view | Hike summary |
|---|---|
| ![track](docs/screenshots/track.png) | ![summary](docs/screenshots/summary.png) |

## Requirements

- Node.js 20+
- Xcode 16+ (iOS) / Android Studio Ladybug+ (Android)
- CocoaPods 1.15+ (iOS)

## Installation

    git clone https://github.com/example/traillog.git
    cd traillog
    npm install
    npx pod-install ios

## Building & Running

    npx react-native run-ios
    npx react-native run-android

Release builds are produced with `npx react-native run-ios --configuration
Release` and `./gradlew assembleRelease`.

## Architecture

A local SQLite store is the source of truth; a background sync worker
pushes new hikes to the API and pulls shared hikes down.

## Testing

    npm test          # Jest unit tests
    npm run e2e:ios    # Detox end-to-end suite

## Release Process

Tag `vX.Y.Z` on `main` to trigger Fastlane lanes that build and submit to
TestFlight and the Play Store internal track.

## License

MIT
```
