"use client";

import { Lock } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AlertRow } from "@/components/app/alerts/AlertRow";
import { AlertRuleForm } from "@/components/app/alerts/AlertRuleForm";
import { PaywallSheet } from "@/components/app/PaywallSheet";
import { FormError } from "@/components/auth/FormError";
import { Button, EmptyState, Skeleton } from "@/components/ui";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";

type AlertRule = components["schemas"]["AlertRule"];

/** Free tier: the Lock-icon empty state plus the paywall sheet on the
 * one gated action here (creating an alert), per docs/frontend-
 * architecture/07-phases.md's Sub-phase 8.2. Paid tier: the real
 * alert list and creation form. Which one shows is decided up front
 * by GET /subscriptions/entitlement, not discovered only after a
 * failed POST, the same real prerequisite gap closed for this phase. */
export function AlertsView() {
  const router = useRouter();
  const [entitled, setEntitled] = useState<boolean | null>(null);
  const [alerts, setAlerts] = useState<AlertRule[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showPaywall, setShowPaywall] = useState(false);

  async function load() {
    const [entitlementResult, alertsResult] = await Promise.all([
      apiClient.GET("/api/v1/subscriptions/entitlement", { params: { query: { feature: "alerts" } } }),
      apiClient.GET("/api/v1/alerts"),
    ]);
    if (entitlementResult.response.status === 401) {
      router.push("/");
      return;
    }
    if (entitlementResult.error) {
      setError(extractErrorMessage(entitlementResult.error, "Could not load alerts."));
      return;
    }
    setEntitled(entitlementResult.data?.entitled ?? false);
    setAlerts(alertsResult.data?.items ?? []);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleDelete(alertId: string) {
    const { response } = await apiClient.DELETE("/api/v1/alerts/{alert_id}", {
      params: { path: { alert_id: alertId } },
    });
    if (response.status !== 204) return;
    setAlerts((current) => (current ?? []).filter((a) => a.id !== alertId));
  }

  if (error) {
    return (
      <div className="px-4 pt-4 sm:px-6 sm:pt-6">
        <FormError message={error} />
      </div>
    );
  }

  if (entitled === null || alerts === null) {
    return (
      <div className="px-4 pt-4 sm:px-6 sm:pt-6">
        <Skeleton className="h-8 w-32" />
      </div>
    );
  }

  return (
    <div className="px-4 pt-4 sm:px-6 sm:pt-6">
      <h1 className="mb-4 text-lg font-bold text-text">Alerts</h1>

      {!entitled ? (
        <>
          <EmptyState
            icon={Lock}
            title="Alerts are a paid feature"
            description="Get notified the moment a favorited stock's score changes or crosses a price you set."
            action={<Button onClick={() => setShowPaywall(true)}>See plans</Button>}
          />
          {showPaywall ? <PaywallSheet onClose={() => setShowPaywall(false)} /> : null}
        </>
      ) : (
        <>
          <AlertRuleForm onCreated={load} />
          {alerts.length === 0 ? (
            <p className="text-center text-sm text-muted">No alerts set yet.</p>
          ) : (
            alerts.map((alert) => (
              <AlertRow key={alert.id} alert={alert} onDelete={handleDelete} />
            ))
          )}
        </>
      )}
    </div>
  );
}
