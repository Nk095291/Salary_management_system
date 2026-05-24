import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';

interface MultiSelectProps {
  label: string;
  options: string[];
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  renderOption?: (option: string) => ReactNode;
}

export function MultiSelect({
  label,
  options,
  value,
  onChange,
  placeholder = 'All',
  searchPlaceholder = 'Search…',
  renderOption,
}: MultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const rootRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const listId = useId();

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return options;
    return options.filter((opt) => opt.toLowerCase().includes(q));
  }, [options, search]);

  useEffect(() => {
    if (!open) {
      setSearch('');
      return;
    }
    // Small delay so the dropdown is in the DOM before focusing
    const t = setTimeout(() => searchRef.current?.focus(), 10);
    function onDocMouseDown(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', onDocMouseDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      clearTimeout(t);
      document.removeEventListener('mousedown', onDocMouseDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open]);

  function toggleOption(option: string) {
    if (value.includes(option)) {
      onChange(value.filter((v) => v !== option));
    } else {
      onChange([...value, option]);
    }
  }

  function selectAll() {
    onChange([...options]);
  }

  function clearSelection() {
    onChange([]);
    setSearch('');
  }

  const hasSelection = value.length > 0;

  return (
    <div className="ms-root" ref={rootRef}>
      <span className="ms-label">{label}</span>

      <div className="ms-control">
        <div className={`ms-trigger-wrap${hasSelection ? ' ms-trigger-wrap--active' : ''}`}>
          <button
            type="button"
            className="ms-trigger"
            aria-expanded={open}
            aria-haspopup="listbox"
            aria-controls={listId}
            onClick={() => setOpen((o) => !o)}
          >
            <span className="ms-trigger-text">
              {value.length === 0
                ? placeholder
                : value.length === 1
                  ? (renderOption ? <span className="ms-trigger-single">{renderOption(value[0])}</span> : value[0])
                  : (
                    <span className="ms-trigger-count">
                      {value.length} selected
                    </span>
                  )}
            </span>
            <svg
              className={`ms-chevron${open ? ' ms-chevron--open' : ''}`}
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              aria-hidden
            >
              <path d="M2 4.5L7 9.5L12 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          {hasSelection && (
            <button
              type="button"
              className="ms-clear-btn"
              aria-label="Clear selection"
              onClick={clearSelection}
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden>
                <path d="M2 2L8 8M8 2L2 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
          )}
        </div>

        {open && (
        <div className="ms-dropdown" id={listId} role="listbox">
          {/* Search */}
          <div className="ms-search-wrap">
            <svg className="ms-search-icon" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
              <circle cx="6" cy="6" r="4" stroke="currentColor" strokeWidth="1.5" />
              <path d="M10 10L13 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <input
              ref={searchRef}
              type="text"
              className="ms-search"
              placeholder={searchPlaceholder}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label={`Search ${label}`}
            />
            {search && (
              <button type="button" className="ms-search-clear" onClick={() => setSearch('')} aria-label="Clear search">
                ×
              </button>
            )}
          </div>

          {/* Bulk actions — only when not searching */}
          {!search && options.length > 0 && (
            <div className="ms-bulk">
              <button type="button" className="ms-bulk-btn" onClick={selectAll}>
                Select all ({options.length})
              </button>
              {hasSelection && (
                <button type="button" className="ms-bulk-btn" onClick={clearSelection}>
                  Clear
                </button>
              )}
              {hasSelection && (
                <span className="ms-bulk-count">{value.length} of {options.length} selected</span>
              )}
            </div>
          )}

          {/* Options list */}
          <div className="ms-options" role="group">
            {filtered.length === 0 ? (
              <p className="ms-empty">No matches for "{search}"</p>
            ) : (
              filtered.map((option) => {
                const selected = value.includes(option);
                return (
                  <button
                    key={option}
                    type="button"
                    role="option"
                    aria-selected={selected}
                    className={`ms-option${selected ? ' ms-option--selected' : ''}`}
                    onClick={() => toggleOption(option)}
                  >
                    {renderOption ? renderOption(option) : option}
                  </button>
                );
              })
            )}
          </div>
        </div>
        )}
      </div>
    </div>
  );
}
