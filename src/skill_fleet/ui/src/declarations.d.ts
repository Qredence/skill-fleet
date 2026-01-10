import "@opentui/react";
import type React from "react";

// OpenTUI custom style properties
export interface OpenTUIStyle extends React.CSSProperties {
  fg?: string; // foreground color
  bg?: string; // background color
  attributes?: number;
  border?: boolean | string;
  borderColor?: string;
  [key: string]: any;
}

export interface OpenTUITextProps extends React.HTMLAttributes<HTMLDivElement> {
  content?: string;
  style?: OpenTUIStyle;
}

export interface OpenTUIBoxProps extends React.HTMLAttributes<HTMLDivElement> {
  style?: OpenTUIStyle;
}

declare global {
  namespace JSX {
    interface IntrinsicElements {
      box: OpenTUIBoxProps & { children?: React.ReactNode };
      text: OpenTUITextProps & { children?: React.ReactNode };
      input: any;
      button: any;
      scrollbox: any;
      code: any;
    }
  }
}
