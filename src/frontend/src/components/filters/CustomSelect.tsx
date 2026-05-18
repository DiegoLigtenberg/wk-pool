import { useEffect, useRef, useState } from "react";
import type { SelectOption } from "../../types";
import "./CustomSelect.css";

type CustomSelectProps = {
  id: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  scroll?: boolean;
  centered?: boolean;
};

export function CustomSelect({
  id,
  value,
  options,
  onChange,
  scroll = false,
  centered = false,
}: CustomSelectProps) {
  const [open, setOpen] = useState(false);
  const [activeValue, setActiveValue] = useState(value);
  const searchRef = useRef({ term: "", at: 0 });
  const rootRef = useRef<HTMLDivElement>(null);
  const selected = options.find((option) => option.value === value) ?? options[0];

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, []);

  useEffect(() => {
    setActiveValue(value);
  }, [value]);

  function handleKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Escape") {
      setOpen(false);
      return;
    }

    if (event.key === "Enter" && open) {
      onChange(activeValue);
      setOpen(false);
      return;
    }

    if (event.key.length !== 1 || event.key.trim() === "" || event.altKey || event.ctrlKey || event.metaKey) {
      return;
    }

    event.preventDefault();
    setOpen(true);

    const now = Date.now();
    const fresh = now - searchRef.current.at > 700;
    const term = normalize(fresh ? event.key : searchRef.current.term + event.key);
    searchRef.current = { term, at: now };

    const match = options.find((option) => normalize(option.label).startsWith(term));
    if (match) {
      setActiveValue(match.value);
      requestAnimationFrame(() =>
        rootRef.current
          ?.querySelector(`[data-value="${CSS.escape(match.value)}"]`)
          ?.scrollIntoView({ block: "nearest" }),
      );
    }
  }

  return (
    <div
      ref={rootRef}
      className={`custom-select${open ? " is-open" : ""}${centered ? " custom-select--centered" : ""}`}
      id={id}
      data-value={value}
      onKeyDown={handleKeyDown}
    >
      <button
        type="button"
        className="custom-select-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={(event) => {
          event.stopPropagation();
          setOpen((current) => !current);
          setActiveValue(value);
        }}
      >
        <span className="custom-select-value">{selected?.label ?? ""}</span>
        <span className="custom-select-chevron" aria-hidden="true">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path
              d="M2.5 4.5L6 8L9.5 4.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
      </button>
      <div className={`custom-select-menu${scroll ? " custom-select-menu--scroll" : ""}`} role="listbox">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`custom-select-option${option.value === value ? " is-selected" : ""}${
              option.value === activeValue ? " is-active" : ""
            }`}
            data-value={option.value}
            role="option"
            aria-selected={option.value === value}
            onMouseEnter={() => setActiveValue(option.value)}
            onClick={(event) => {
              event.stopPropagation();
              onChange(option.value);
              setOpen(false);
            }}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function normalize(value: string): string {
  return value
    .trim()
    .toLocaleLowerCase("nl-NL")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}
