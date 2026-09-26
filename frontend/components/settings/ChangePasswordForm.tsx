"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { FormError } from "@/components/auth/FormError";
import { Button, Input } from "@/components/ui";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";

// Built here, standalone, per docs/frontend-architecture/07-phases.md's
// Sub-phase 2.2, ready to mount inside /app/settings once that phase
// exists, not wired into any route yet.
const schema = z.object({
  current_password: z.string().min(1, "Enter your current password"),
  new_password: z.string().min(8, "Password must be at least 8 characters"),
});
type FormValues = z.infer<typeof schema>;

export function ChangePasswordForm() {
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setServerError(null);
    setSuccess(false);
    const { error } = await apiClient.POST("/api/v1/auth/change-password", { body: values });
    if (error) {
      setServerError(extractErrorMessage(error, "Could not change your password."));
      return;
    }
    setSuccess(true);
    reset();
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <FormError message={serverError} />
      {success ? <p className="text-sm text-brand">Password changed.</p> : null}
      <Input
        label="Current password"
        type="password"
        autoComplete="current-password"
        error={errors.current_password?.message}
        {...register("current_password")}
      />
      <Input
        label="New password"
        type="password"
        autoComplete="new-password"
        error={errors.new_password?.message}
        {...register("new_password")}
      />
      <Button type="submit" disabled={isSubmitting} className="self-start">
        {isSubmitting ? "Saving…" : "Change password"}
      </Button>
    </form>
  );
}
