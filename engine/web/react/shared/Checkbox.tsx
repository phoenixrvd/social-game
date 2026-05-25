type CheckboxProps = {
  label: string
  checked: boolean
  disabled?: boolean
  onChange: (checked: boolean) => void
}

export function Checkbox({ label, checked, disabled = false, onChange }: CheckboxProps) {
  return (
    <label className="sg-settings-checkbox">
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.currentTarget.checked)}
      />
      <span>{label}</span>
    </label>
  )
}
