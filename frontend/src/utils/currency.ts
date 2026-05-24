// TODO: Multi-currency — when the backend stores salaries in local currencies,
//       add per-country currency codes to ALLOWED_COUNTRIES in types/api.ts,
//       expose them from /api/employees/countries/, and update insights
//       aggregation to convert all values to a base currency (USD) before
//       comparison. The formatSalary helper below already handles arbitrary
//       currency codes once the symbol map is extended.
const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  INR: '₹',
  GBP: '£',
  EUR: '€',
  AUD: 'A$',
  CAD: 'C$',
};

export function formatSalary(
  amount: number | string,
  currency?: string,
): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  const formatted = new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 0,
  }).format(num);
  const symbol = currency
    ? CURRENCY_SYMBOLS[currency] ?? currency
    : '$';
  return `${symbol}${formatted}`;
}
