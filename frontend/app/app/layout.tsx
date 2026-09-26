import { AppNav } from "@/components/app/AppNav";
import { InstallPrompt } from "@/components/app/InstallPrompt";
import { OfflineBanner } from "@/components/app/OfflineBanner";

// Everything an individual /app screen needs already in place before
// it exists, per docs/frontend-architecture/07-phases.md's Sub-phase
// 3.2: the nav shell, the offline banner, and the install prompt.
// Route protection itself is proxy.ts, a UX gate at the edge, not
// here; the real session check happens wherever a page under this
// layout actually fetches data, per 04-landing-page-indepth.md, kept
// out of this shared shell on purpose so it isn't duplicated per page.
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-full">
      <OfflineBanner />
      <AppNav />
      <main className="pb-20 sm:pb-0 sm:pl-56">{children}</main>
      <InstallPrompt />
    </div>
  );
}
