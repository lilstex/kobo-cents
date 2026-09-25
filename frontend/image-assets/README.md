# Image assets

Logo, favicon, and app icon files for Kobo & Cents, generated from real
vector paths extracted from the Archivo ExtraBold font, not from live
text. Full design reasoning is in
`docs/frontend-architecture/02.md` and `docs/frontend-architecture/01.md`
(wordmark section); this file is only about which asset goes where.

Two identities, used in different places: the **wordmark** ("Kobo &
Cents" set in Archivo, green ampersand) wherever there's horizontal
room, and the **icon mark** (the ampersand alone, on a solid
brand-green square) wherever the space is small and square, a
favicon, a home-screen icon, an app-store listing.

## source-svgs/

The masters everything else is rendered from. Keep these; regenerate
PNGs from them if a size is ever missing rather than hand-editing a PNG.

| File | What it is |
|---|---|
| `icon-mark-safezone.svg` | Icon mark, 512x512, brand-green background, dark ampersand at 46% scale. Generous padding so the mark survives any mask shape. Source for the favicon, PWA icons, and Android legacy launcher icons. |
| `icon-mark-fullbleed.svg` | Icon mark, 1024x1024, same colors, ampersand at 64% scale. No safe-zone padding, iOS applies its own mask and expects content closer to the edge. Source for every iOS size. |
| `icon-mark-foreground-transparent.svg` | Icon mark, 432x432, transparent background, dark ampersand only. Android adaptive icon foreground layer. |
| `icon-background-layer.svg` | Flat brand-green square, 432x432, no glyph. Android adaptive icon background layer. |
| `wordmark-for-dark-surfaces.svg` | "Kobo & Cents", light text, green ampersand. For dark backgrounds. |
| `wordmark-for-light-surfaces.svg` | "Kobo & Cents", dark text, emerald ampersand (deepened for contrast on light, not the same green as dark mode). For light backgrounds. |

## favicon/

Browser tab icon.

| File | Use |
|---|---|
| `favicon-16.png` | Standard browser tab size |
| `favicon-32.png` | Retina browser tab, taskbar shortcuts |
| `favicon-48.png` | Windows site icons, some bookmark bars |
| `favicon.ico` | Multi-resolution ICO (16/32/48 bundled together), for browsers that still ask for `.ico` specifically. Reference this one from `<link rel="icon">`. |

## pwa/

Progressive web app manifest icons (`manifest.json` / `manifest.webmanifest`).

| File | Use |
|---|---|
| `icon-192-any.png` | `sizes: "192x192", purpose: "any"` |
| `icon-192-maskable.png` | `sizes: "192x192", purpose: "maskable"` (same image as `any`; the safe-zone mark already respects maskable safe-zone requirements, so no separate crop was needed) |
| `icon-512-any.png` | `sizes: "512x512", purpose: "any"` |
| `icon-512-maskable.png` | `sizes: "512x512", purpose: "maskable"` |
| `apple-touch-icon-180.png` | `<link rel="apple-touch-icon">`, used when the PWA is added to an iOS home screen before any native app exists |

## ios/

Native iOS app icon set (for the future React Native + Expo build, see
`docs/frontend-architecture/00.md`). Not needed for web or PWA launch.
All rendered from the full-bleed mark, iOS masks these into a squircle
itself.

| File | Use |
|---|---|
| `ios-appicon-1024.png` | App Store Connect listing |
| `ios-appicon-180.png` | iPhone home screen, @3x |
| `ios-appicon-167.png` | iPad Pro home screen, @2x |
| `ios-appicon-152.png` | iPad home screen, @2x |
| `ios-appicon-120.png` | iPhone home screen, @2x |

## android/

Native Android app icon set (same future-build note as iOS).

| File | Use |
|---|---|
| `adaptive-icon-foreground-432.png` | Adaptive icon foreground layer (transparent background, dark ampersand). Android composites this over the background layer and masks the result itself. |
| `adaptive-icon-background-432.png` | Adaptive icon background layer (flat brand green, no glyph) |
| `launcher-icon-192.png` | Legacy launcher icon, xxxhdpi |
| `launcher-icon-144.png` | Legacy launcher icon, xxhdpi |
| `launcher-icon-96.png` | Legacy launcher icon, xhdpi |
| `launcher-icon-72.png` | Legacy launcher icon, hdpi |
| `launcher-icon-48.png` | Legacy launcher icon, mdpi |

Legacy sizes exist for older tooling and Play Console targeting that
still asks for pre-adaptive-icon assets. The adaptive two-layer files
are the ones that matter for any current Android device.

## general/

Not tied to one specific platform manifest.

| File | Use |
|---|---|
| `icon-512.png` | General square icon, social previews, README badges, anywhere a plain square mark is needed at a decent resolution |
| `icon-256.png` | Same, smaller |

## wordmark/

Full "Kobo & Cents" wordmark, flat PNG (rasterized from the SVGs above)
for contexts that do not render SVG, mainly email.

| File | Use |
|---|---|
| `wordmark-dark-surface-800.png` | Email header, dark-themed surfaces, standard resolution |
| `wordmark-dark-surface-1600.png` | Same, @2x for retina email clients |
| `wordmark-light-surface-800.png` | Email header, light-themed surfaces, standard resolution |
| `wordmark-light-surface-1600.png` | Same, @2x |

For the website header and in-app nav, use the SVG wordmark directly
(`source-svgs/wordmark-for-dark-surfaces.svg` or
`wordmark-for-light-surfaces.svg`) rather than these PNGs, SVG stays
sharp at any size and follows the current theme.

## What's deliberately not here yet

Nothing. Every size this plan calls for is generated. The one item
still pending is a possible **monochrome** variant (single-color mark,
no fill) for contexts like a notification-bar icon or a dark PDF
export, not needed until a concrete feature calls for it.
