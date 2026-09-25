"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { FormError } from "@/components/auth/FormError";
import { Button, Input } from "@/components/ui";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";

const schema = z.object({
  new_password: z.string().min(8, "Password must be at least 8 characters"),
});
type FormValues = z.infer<typeof schema>;

export function ResetPasswordForm() {
  const router = useRouter();
  const token = useSearchParams().get("token");
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    if (!token) {
      setServerError("This reset link is missing its token.");
      return;
    }
    setServerError(null);
    const { error } = await apiClient.POST("/api/v1/auth/reset-password", {
      body: { token, new_password: values.new_password },
    });
    if (error) {
      setServerError(extractErrorMessage(error, "Could not reset your password."));
      return;
    }
    router.push("/login");
  }

  if (!token) {
    return (
      <div className="flex flex-col gap-3 text-center">
        <FormError message="This reset link is invalid or has expired." />
        <Link href="/forgot-password" className="text-xs text-muted underline">
          Request a new link
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <h1 className="text-xl font-bold text-text">Choose a new password</h1>
      <FormError message={serverError} />
      <Input
        label="New password"
        type="password"
        autoComplete="new-password"
        error={errors.new_password?.message}
        {...register("new_password")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving…" : "Reset password"}
      </Button>
    </form>
  );
}
