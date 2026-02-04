import { SyntaxStyle } from "@opentui/core";

const DEFAULT_SYNTAX_STYLE = SyntaxStyle.create();

type Props = {
  content: string;
  streaming?: boolean;
};

export function MarkdownView({ content, streaming }: Props) {
  // Prefer the core MarkdownRenderable (supports incremental parsing via `streaming`).
  return (
    <markdown
      content={content}
      streaming={Boolean(streaming)}
      syntaxStyle={DEFAULT_SYNTAX_STYLE}
    />
  );
}
