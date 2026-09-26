import { Footer } from "@/components/marketing/Footer";
import { Header } from "@/components/marketing/Header";

// Public and unauthenticated per docs/frontend-architecture/05-app-
// plan.md, but structurally outside `/app` rather than inside the
// `(marketing)` route group: this is product surface, not the
// marketing site, even though the auth rule happens to match.
export default function ShareLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Header />
      <div className="min-h-[60vh]">{children}</div>
      <Footer />
    </>
  );
}
