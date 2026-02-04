import type { KeyBinding, TextareaRenderable } from "@opentui/core";
import { useEffect, useRef } from "react";

type Theme = {
  panelAlt: string;
  text: string;
  muted: string;
};

type Props = {
  theme: Theme;
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  focused: boolean;
  height: number;
  placeholder?: string;
  keyBindings?: KeyBinding[];
  wrapText?: boolean;
};

export function ControlledTextarea({
  theme,
  value,
  onChange,
  onSubmit,
  focused,
  height,
  placeholder,
  keyBindings,
  wrapText,
}: Props) {
  const ref = useRef<TextareaRenderable>(null);

  useEffect(() => {
    const current = ref.current?.plainText ?? "";
    if (current !== value) {
      ref.current?.setText(value);
    }
  }, [value]);

  return (
    <textarea
      ref={ref}
      initialValue={value}
      placeholder={placeholder || null}
      onContentChange={() => {
        const text = ref.current?.plainText ?? "";
        onChange(text);
      }}
      onSubmit={() => {
        if (onSubmit) onSubmit();
      }}
      keyBindings={keyBindings}
      height={height}
      wrapMode={wrapText ? "word" : "none"}
      focused={focused}
      backgroundColor={theme.panelAlt}
      textColor={theme.text}
      placeholderColor={theme.muted}
      focusedBackgroundColor={theme.panelAlt}
      focusedTextColor={theme.text}
    />
  );
}

// Export the ref type for external access
export type ControlledTextareaRef = TextareaRenderable;
