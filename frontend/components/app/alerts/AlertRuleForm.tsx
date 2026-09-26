"use client";

import { type FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";

type SearchResultItem = components["schemas"]["SearchResultItem"];
type RuleType = "score_change" | "price_threshold";

/** The alert-type segmented control from docs/frontend-architecture/
 * 06-design.md's mockup: score_change has nothing to configure (it
 * fires on any bucket transition, per app/services/alerts.py), only
 * price_threshold asks for a direction and a level. */
export function AlertRuleForm({ onCreated }: { onCreated: () => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [selected, setSelected] = useState<SearchResultItem | null>(null);
  const [ruleType, setRuleType] = useState<RuleType>("score_change");
  const [direction, setDirection] = useState<"above" | "below">("above");
  const [price, setPrice] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (selected || query.trim().length === 0) {
      setResults([]);
      return;
    }
    let cancelled = false;
    const timer = setTimeout(async () => {
      const { data } = await apiClient.GET("/api/v1/search", { params: { query: { q: query } } });
      if (!cancelled) setResults(data?.items ?? []);
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, selected]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    setError(null);

    if (ruleType === "price_threshold" && (!price || Number(price) <= 0)) {
      setError("Enter a price above zero.");
      return;
    }

    setSubmitting(true);
    const { error: apiError } = await apiClient.POST("/api/v1/alerts", {
      body: {
        ticker: selected.ticker,
        market: selected.market,
        rule_type: ruleType,
        rule_config: ruleType === "price_threshold" ? { direction, price: Number(price) } : {},
      },
    });
    setSubmitting(false);
    if (apiError) {
      setError(extractErrorMessage(apiError, "Could not create this alert."));
      return;
    }
    setSelected(null);
    setQuery("");
    setPrice("");
    setRuleType("score_change");
    onCreated();
  }

  return (
    <form onSubmit={handleSubmit} className="mb-6 flex flex-col gap-4 rounded-lg border border-border bg-surface p-4">
      <div>
        <label className="mb-1.5 block font-mono text-[11px] font-semibold uppercase tracking-wider text-muted">
          Stock
        </label>
        {selected ? (
          <div className="flex items-center justify-between rounded-lg border border-border bg-bg px-3 py-2.5 text-sm">
            <span className="font-semibold text-text">{selected.ticker}</span>
            <button
              type="button"
              onClick={() => setSelected(null)}
              className="text-xs text-muted underline"
            >
              Change
            </button>
          </div>
        ) : (
          <div className="relative">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search for a stock"
              className="w-full rounded-lg border border-border bg-bg px-3 py-2.5 text-sm text-text outline-none placeholder:text-muted focus:border-brand"
            />
            {results.length > 0 ? (
              <div className="absolute inset-x-0 top-full z-10 mt-1 rounded-lg border border-border bg-surface shadow-lg">
                {results.map((item) => (
                  <button
                    key={`${item.market}-${item.ticker}`}
                    type="button"
                    onClick={() => {
                      setSelected(item);
                      setResults([]);
                    }}
                    className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-bg"
                  >
                    <span className="font-semibold text-text">{item.ticker}</span>
                    <span className="text-xs text-muted">{item.company_name}</span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        )}
      </div>

      <div>
        <label className="mb-1.5 block font-mono text-[11px] font-semibold uppercase tracking-wider text-muted">
          Alert type
        </label>
        <div className="flex overflow-hidden rounded-lg border border-border">
          {(["score_change", "price_threshold"] as RuleType[]).map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setRuleType(type)}
              className={`flex-1 border-r border-border py-2 text-xs font-semibold last:border-r-0 ${
                ruleType === type ? "bg-brand text-bg" : "bg-surface text-muted"
              }`}
            >
              {type === "score_change" ? "Score change" : "Price threshold"}
            </button>
          ))}
        </div>
      </div>

      {ruleType === "price_threshold" ? (
        <div className="flex gap-2">
          <div className="flex overflow-hidden rounded-lg border border-border">
            {(["above", "below"] as const).map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDirection(d)}
                className={`px-3 py-2.5 text-xs font-semibold ${
                  direction === d ? "bg-brand text-bg" : "bg-surface text-muted"
                }`}
              >
                {d === "above" ? "Above" : "Below"}
              </button>
            ))}
          </div>
          <input
            value={price}
            onChange={(event) => setPrice(event.target.value)}
            type="number"
            min="0"
            step="0.01"
            placeholder="Price"
            className="flex-1 rounded-lg border border-border bg-bg px-3 py-2.5 text-sm text-text outline-none placeholder:text-muted focus:border-brand"
          />
        </div>
      ) : (
        <p className="text-xs text-muted">Notified whenever this stock's bucket changes.</p>
      )}

      {error ? <p className="text-xs text-down">{error}</p> : null}

      <Button type="submit" disabled={!selected || submitting}>
        {submitting ? "Creating…" : "Create alert"}
      </Button>
    </form>
  );
}
