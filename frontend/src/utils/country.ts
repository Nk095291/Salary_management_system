const COUNTRY_TO_ISO: Record<string, string> = {
  'United States': 'us',
  India: 'in',
  'United Kingdom': 'gb',
  Germany: 'de',
  Canada: 'ca',
  Australia: 'au',
};

/** Returns a lowercase ISO-3166-1 alpha-2 code or empty string. */
export function getCountryIso(countryName: string): string {
  return COUNTRY_TO_ISO[countryName] ?? '';
}

/** Returns a flagcdn.com URL for a 20×15 flag image, or empty string. */
export function getCountryFlagUrl(countryName: string): string {
  const iso = getCountryIso(countryName);
  return iso ? `https://flagcdn.com/20x15/${iso}.png` : '';
}
