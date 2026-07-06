import { ChangeEvent, FocusEvent, useEffect, useState } from "react";
import { parseDisplayDate, toDisplayDate } from "../utils/date";

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

  useEffect(() => {
    setDisplayValue(toDisplayDate(value));
    setError("");
  }, [value]);

  function update(event: ChangeEvent<HTMLInputElement>) {
    const next = event.target.value;
    setDisplayValue(next);
    const parsed = parseDisplayDate(next);
    if (parsed !== null) {
      setError("");
      event.target.setCustomValidity("");
      onChange(parsed);
      return;
    }
    const message = next.trim() ? "Datum mora biti u obliku dd/mm/yyyy." : "";
    setError(message);
    event.target.setCustomValidity(message);
  }

  function validate(event: FocusEvent<HTMLInputElement>) {
    const parsed = parseDisplayDate(event.target.value);
    const message = parsed === null ? "Datum mora biti u obliku dd/mm/yyyy." : "";
    setError(message);
    event.target.setCustomValidity(message);
  }

  return (
    <>
      <input
        id={id}
        className={className}
        type="text"
        inputMode="numeric"
        placeholder="dd/mm/yyyy"
        pattern="\d{2}/\d{2}/\d{4}"
        value={displayValue}
        required={required}
        onChange={update}
        onBlur={validate}
      />
      {error && <small className="field-error">{error}</small>}
    </>
  );
}
