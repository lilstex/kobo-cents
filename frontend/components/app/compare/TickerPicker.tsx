"use client";

import { Search, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui";
import { apiClient } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type SearchResultItem = components["schemas"]["SearchResultItem"];

const MAX_TICKERS = 3;
const MIN_TICKERS = 2;

/** Search reuses the same trigram-backed /search endpoint the phases
 * doc built for Sub-phase 4.3, so "zenit" finding Zenith Bank works
 * here too, not a separate lookup mechanism. Two or three tickers,
 * per docs/backend-architecture/03-phases.md's Sub-phase 4.4. */
export function TickerPicker({
  selected,
  onChange,
  onCompare,
}: {
  selected: string[];
  onChange: (tickers: string[]) => void;
  onCompare: () => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);

  useEffect(() => {
    if (query.trim().length === 0) {
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
  }, [query]);

  function addTicker(ticker: string) {
    if (selected.includes(ticker) || selected.length >= MAX_TICKERS) return;
    onChange([...selected, ticker]);
    setQuery("");
    setResults([]);
  }

  function removeTicker(ticker: string) {
    onChange(selected.filter((t) => t !== ticker));
  }

  return (
    <div className="mb-4">
      <div className="mb-2 flex flex-wrap gap-2">
        {selected.map((ticker) => (
          <span
            key={ticker}
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1 text-xs font-semibold text-text"
          >
            {ticker}
            <button type="button" onClick={() => removeTicker(ticker)} aria-label={`Remove ${ticker}`}>
              <X className="h-3 w-3 text-muted" />
            </button>
          </span>
        ))}
      </div>

      {selected.length < MAX_TICKERS ? (
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Add a stock to compare"
            className="w-full rounded-lg border border-border bg-surface py-2.5 pl-9 pr-3 text-sm text-text outline-none placeholder:text-muted focus:border-brand"
          />
          {results.length > 0 ? (
            <div className="absolute inset-x-0 top-full z-10 mt-1 rounded-lg border border-border bg-surface shadow-lg">
              {results.map((item) => (
                <button
                  key={`${item.market}-${item.ticker}`}
                  type="button"
                  onClick={() => addTicker(item.ticker)}
                  className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-bg"
                >
                  <span className="font-semibold text-text">{item.ticker}</span>
                  <span className="text-xs text-muted">{item.company_name}</span>
                </button>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      {selected.length >= MIN_TICKERS ? (
        <Button onClick={onCompare} className="mt-3 w-full sm:w-auto">
          Compare
        </Button>
      ) : (
        <p className="mt-3 text-xs text-muted">Pick at least two stocks to compare.</p>
      )}
    </div>
  );
}
