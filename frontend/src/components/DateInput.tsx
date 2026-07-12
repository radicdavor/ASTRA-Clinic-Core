import { ChangeEvent, FocusEvent, useEffect, useRef, useState } from "react";
import { CalendarDays } from "lucide-react";
import { formatTypedDate, parseDisplayDate, toDisplayDate } from "../utils/date";

type DateInputProps = {
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  className?: string;
  id?: string;
};

export function DateInput({ value, onChange, required, className, id }: DateInputProps) {
  const [displayValue, setDisplayValue] = useState(toDisplayDate(value));
  const [error, setError] = useState("");
  const calendarRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setDisplayValue(toDisplayDate(value));
    setError("");
  }, [value]);

  function update(event: ChangeEvent<HTMLInputElement>) {
    let raw = event.target.value;
    if (displayValue.endsWith(".") && raw === displayValue.slice(0, -1)) raw = raw.slice(0, -1);
    const next = formatTypedDate(raw);
    setDisplayValue(next);
    const parsed = parseDisplayDate(next);
    if (parsed !== null) {
      setError("");
      event.target.setCustomValidity("");
      onChange(parsed);
      return;
    }
    const message = next.trim() ? "Datum mora biti u obliku dd. mm. yyyy." : "";
    setError(message);
    event.target.setCustomValidity(message);
  }

  function validate(event: FocusEvent<HTMLInputElement>) {
    const parsed = parseDisplayDate(event.target.value);
    const message = parsed === null ? "Datum mora biti u obliku dd. mm. yyyy." : "";
    setError(message);
    event.target.setCustomValidity(message);
  }

  return (
    <>
      <span className="date-input-control">
        <input id={id} className={className} type="text" inputMode="numeric" placeholder="dd. mm. yyyy." pattern="\d{2}\.\s?\d{2}\.\s?\d{4}\.?" value={displayValue} required={required} onChange={update} onBlur={validate}/>
        <button type="button" aria-label="Odaberi datum iz kalendara" title="Odaberi datum iz kalendara" onClick={()=>calendarRef.current?.showPicker()}><CalendarDays size={17}/></button>
        <input ref={calendarRef} className="native-date-picker" type="date" value={value} tabIndex={-1} aria-hidden="true" onChange={event=>onChange(event.target.value)}/>
      </span>
      {error && <small className="field-error">{error}</small>}
    </>
  );
}
