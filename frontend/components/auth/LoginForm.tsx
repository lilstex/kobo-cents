"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { FormError } from "@/components/auth/FormError";
import { Button, Input } from "@/components/ui";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";

const schema = z.object({
  email: z.string().email("Enter a real email address"),
  password: z.string().min(1, "Enter your password"),
});

type FormValues = z.infer<typeof schema>;

export function LoginForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setServerError(null);
    const { data, error } = await apiClient.POST("/api/v1/auth/login", { body: values });
    if (error) {
      setServerError(extractErrorMessage(error, "Could not sign you in, try again."));
      return;
    }
    if (data?.status === "unverified") {
      // Not a generic auth failure, per docs/01_product.md: redirect
      // to the same verification screen a fresh signup lands on,
      // with a resend option, not an error message.
      router.push(`/verify?email=${encodeURIComponent(values.email)}`);
      return;
    }
    router.push("/app");
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <h1 className="text-xl font-bold text-text">Sign in</h1>
      <FormError message={serverError} />
      <Input
        label="Email"
        type="email"
        autoComplete="email"
        error={errors.email?.message}
        {...register("email")}
      />
      <Input
        label="Password"
        type="password"
        autoComplete="current-password"
        error={errors.password?.message}
        {...register("password")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Signing in…" : "Sign in"}
      </Button>
      <div className="flex justify-between text-xs">
        <Link href="/forgot-password" className="text-muted underline">
          Forgot password?
        </Link>
        <Link href="/signup" className="text-text underline">
          Create an account
        </Link>
      </div>
    </form>
  );
}
