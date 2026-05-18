import { useEffect, useRef, useState } from "react";
import type { SelectOption } from "../../types";
import "./CustomSelect.css";

type CustomSelectProps = {
  id: string;
  labelId: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  scroll?: boolean;
  centered?: boolean;
};

export function CustomSelect({
  id,
  labelId,
  value,
  options,
  onChange,
  scroll = false,
  centered = false,
}: CustomSelectProps) {
  const [open, setOpen] = useState(false);
  const [opensUp, setOpensUp] = useState(false);
  const [activeValue, setActiveValue] = useState(value);
  const searchRef = useRef({ term: "", at: 0 });
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const selected = options.find((option) => option.value === value) ?? options[0];
  const activeIndex = Math.max(
    0,
    options.findIndex((option) => option.value === activeValue),
  );
  const activeOptionId = options[activeIndex] ? optionId(id, activeIndex) : undefined;

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

  useEffect(() => {
    if (!open) {
      setOpensUp(false);
      return;
    }

    function updateMenuDirection() {
      const root = rootRef.current;
      const trigger = root?.querySelector<HTMLElement>(".custom-select-trigger");
      const menu = root?.querySelector<HTMLElement>(".custom-select-menu");
      if (!trigger || !menu) {
        return;
      }

      const triggerRect = trigger.getBoundingClientRect();
      const gap = 8;
      const availableBelow = window.innerHeight - triggerRect.bottom;
      const availableAbove = triggerRect.top;
      const menuHeight = menu.offsetHeight || menu.scrollHeight;
      setOpensUp(scroll && availableBelow < menuHeight + gap && availableAbove > availableBelow);
    }

    const frame = window.requestAnimationFrame(updateMenuDirection);
    window.addEventListener("resize", updateMenuDirection);
    window.addEventListener("scroll", updateMenuDirection, true);
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("resize", updateMenuDirection);
      window.removeEventListener("scroll", updateMenuDirection, true);
    };
  }, [open, options.length, scroll]);

  function handleKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
      triggerRef.current?.focus();
      return;
    }

    if (event.key === "Tab") {
      setOpen(false);
      return;
    }

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const direction = event.key === "ArrowDown" ? 1 : -1;
      setOpen(true);
      setActiveByIndex(open ? activeIndex + direction : activeIndex);
      return;
    }

    if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      setOpen(true);
      setActiveByIndex(event.key === "Home" ? 0 : options.length - 1);
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (!open) {
        setOpen(true);
        setActiveValue(value);
        scrollActiveIntoView(value);
        return;
      }

      selectValue(activeValue);
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
      scrollActiveIntoView(match.value);
    }
  }

  function setActiveByIndex(index: number) {
    if (!options.length) {
      return;
    }

    const nextIndex = (index + options.length) % options.length;
    const nextValue = options[nextIndex].value;
    setActiveValue(nextValue);
    scrollActiveIntoView(nextValue);
  }

  function selectValue(nextValue: string) {
    onChange(nextValue);
    setActiveValue(nextValue);
  }

  function scrollActiveIntoView(nextValue: string) {
    requestAnimationFrame(() =>
      rootRef.current
        ?.querySelector(`[data-value="${CSS.escape(nextValue)}"]`)
        ?.scrollIntoView({ block: "nearest" }),
    );
  }

  return (
    <div
      ref={rootRef}
      className={`custom-select${open ? " is-open" : ""}${opensUp ? " custom-select--open-up" : ""}${centered ? " custom-select--centered" : ""}`}
      id={id}
      data-value={value}
      onKeyDown={handleKeyDown}
    >
      <button
        ref={triggerRef}
        type="button"
        className="custom-select-trigger"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={`${id}-listbox`}
        aria-labelledby={`${labelId} ${id}-value`}
        aria-activedescendant={open ? activeOptionId : undefined}
        onClick={(event) => {
          event.stopPropagation();
          setOpen((current) => !current);
          setActiveValue(value);
        }}
      >
        <span className="custom-select-value" id={`${id}-value`}>
          {selected?.label ?? ""}
        </span>
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
      <div
        className={`custom-select-menu${scroll ? " custom-select-menu--scroll" : ""}`}
        id={`${id}-listbox`}
        role="listbox"
        aria-labelledby={labelId}
        aria-hidden={!open}
      >
        {options.map((option, index) => (
          <div
            key={option.value}
            id={optionId(id, index)}
            className={`custom-select-option${option.value === value ? " is-selected" : ""}${
              option.value === activeValue ? " is-active" : ""
            }`}
            data-value={option.value}
            role="option"
            aria-selected={option.value === value}
            tabIndex={-1}
            onMouseEnter={() => setActiveValue(option.value)}
            onClick={(event) => {
              event.stopPropagation();
              selectValue(option.value);
              setOpen(false);
              triggerRef.current?.focus();
            }}
          >
            {option.label}
          </div>
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

function optionId(selectId: string, index: number): string {
  return `${selectId}-option-${index}`;
}
