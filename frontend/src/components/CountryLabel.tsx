import { getCountryFlagUrl } from '../utils/country';

interface CountryLabelProps {
  country: string;
}

export function CountryLabel({ country }: CountryLabelProps) {
  const flagUrl = getCountryFlagUrl(country);
  return (
    <span className="country-label">
      {flagUrl && (
        <img
          className="country-flag-img"
          src={flagUrl}
          alt={`${country} flag`}
          width={20}
          height={15}
          loading="lazy"
        />
      )}
      <span>{country}</span>
    </span>
  );
}
