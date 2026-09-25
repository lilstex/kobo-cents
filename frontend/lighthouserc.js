// Fails a PR that regresses the landing page's performance, per
// docs/frontend-architecture/07-phases.md's Sub-phase 1.6. Lighthouse
// is a lab tool, a single synthetic run, so it measures LCP and CLS
// directly but estimates responsiveness via Total Blocking Time
// rather than true field INP, which needs real user sessions, that's
// what WebVitalsReporter feeds into PostHog for, confirming these lab
// numbers against real traffic, not a second way of measuring the
// same thing.
module.exports = {
  ci: {
    collect: {
      staticDistDir: undefined,
      url: ["http://localhost:3000/"],
      numberOfRuns: 3,
      startServerCommand: "npm run start",
      startServerReadyPattern: "Ready in",
    },
    assert: {
      assertions: {
        "largest-contentful-paint": ["error", { maxNumericValue: 2500 }],
        "cumulative-layout-shift": ["error", { maxNumericValue: 0.1 }],
        "total-blocking-time": ["error", { maxNumericValue: 300 }],
      },
    },
    upload: {
      target: "temporary-public-storage",
    },
  },
};
