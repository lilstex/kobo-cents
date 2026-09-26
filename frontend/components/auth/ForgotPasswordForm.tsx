"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button, Input } from "@/components/ui";
import { apiClient } from "@/lib/api/client";

const schema = z.object({ email: z.string().email("Enter a real email address") });
type FormValues = z.infer<typeof schema>;

export function ForgotPasswordForm() {
  const [sent, setSent] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    // Same response whether or not the account exists, per
    // docs/backend-architecture/00.md, the frontend mirrors that: no
    // branch here reveals whether the email was found.
    await apiClient.POST("/api/v1/auth/forgot-password", { body: values });
    setSent(true);
  }

  if (sent) {
    return (
      <div className="flex flex-col gap-3 text-center">
        <h1 className="text-xl font-bold text-text">Check your email</h1>
        <p className="text-sm text-muted">
          If that account exists, a reset link is on its way.
        </p>
        <Link href="/login" className="text-xs text-muted underline">
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <h1 className="text-xl font-bold text-text">Reset your password</h1>
      <Input
        label="Email"
        type="email"
        autoComplete="email"
        error={errors.email?.message}
        {...register("email")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Sending…" : "Send reset link"}
      </Button>
      <Link href="/login" className="text-center text-xs text-muted underline">
        Back to sign in
      </Link>
    </form>
  );
}
