import type { Metadata } from "next";
import { ForgotPasswordForm } from "@/components/auth/ForgotPasswordForm";

export const metadata: Metadata = { title: "Forgot password — Kobo & Cents" };

export default function ForgotPasswordPage() {
  return <ForgotPasswordForm />;
}
