"use client";

import { X } from "lucide-react";
import type { components } from "@/lib/api/schema";

type AlertRule = components["schemas"]["AlertRule"];

function describeRule(alert: AlertRule): string {
  if (alert.rule_type === "score_change") return "Notifies on any bucket change";
  const config = alert.rule_config as { direction?: string; price?: number };
  return `Notifies when price goes ${config.direction} ${config.price}`;
}

export function AlertRow({
  alert,
  onDelete,
}: {
  alert: AlertRule;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="flex items-center justify-between border-b border-border py-2.5">
      <div>
        <div className="text-sm font-bold text-text">{alert.ticker}</div>
        <div className="mt-0.5 text-[11.5px] text-muted">{describeRule(alert)}</div>
      </div>
      <button
        type="button"
        onClick={() => onDelete(alert.id)}
        aria-label={`Remove alert for ${alert.ticker}`}
        className="text-muted hover:text-down"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
