// The exact two taxonomies from docs/01_product.md, kept verbatim:
// NG and US use different classification standards, not a
// simplification, and these strings have to match app.models.
// market_data.stocks.sector on the backend exactly for the sector
// filter to actually filter anything.
export const NG_SECTORS = [
  "Agriculture",
  "Conglomerates",
  "Construction and Real Estate",
  "Consumer Goods",
  "Financial Services",
  "Healthcare",
  "ICT",
  "Industrial Goods",
  "Natural Resources",
  "Oil and Gas",
  "Services",
];

export const US_SECTORS = [
  "Communication Services",
  "Consumer Discretionary",
  "Consumer Staples",
  "Energy",
  "Financials",
  "Health Care",
  "Industrials",
  "Information Technology",
  "Materials",
  "Real Estate",
  "Utilities",
];

export type Market = "ng" | "us";

export function sectorsForMarket(market: Market): string[] {
  return market === "ng" ? NG_SECTORS : US_SECTORS;
}
