import type { Metadata } from "next";
import { Archivo, JetBrains_Mono } from "next/font/google";
import { CookieConsentBanner } from "@/components/marketing/CookieConsentBanner";
import { ServiceWorkerRegistration } from "@/components/ServiceWorkerRegistration";
import { WebVitalsReporter } from "@/components/WebVitalsReporter";
import { organizationSchema } from "@/lib/structured-data";
import "./globals.css";

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://koboandcents.com"),
  title: "Kobo & Cents",
  description:
    "Nigerian and US stock research. Understand a stock before you decide anything about it.",
  icons: {
    apple: "/pwa/apple-touch-icon-180.png",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${archivo.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-bg text-text">
        <script
          type="application/ld+json"
          // eslint-disable-next-line react/no-danger
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema()) }}
        />
        {children}
        <CookieConsentBanner />
        <WebVitalsReporter />
        <ServiceWorkerRegistration />
      </body>
    </html>
  );
}
