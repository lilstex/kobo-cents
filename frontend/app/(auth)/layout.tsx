import Image from "next/image";
import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-full flex-1 flex-col items-center justify-center px-6 py-12">
      <Link href="/" className="mb-8">
        <Image
          src="/wordmark-dark.svg"
          alt="Kobo & Cents"
          width={140}
          height={26}
          className="theme-dark-only w-36"
        />
        <Image
          src="/wordmark-light.svg"
          alt="Kobo & Cents"
          width={140}
          height={26}
          className="theme-light-only w-36"
        />
      </Link>
      <div className="w-full max-w-sm">{children}</div>
    </main>
  );
}
