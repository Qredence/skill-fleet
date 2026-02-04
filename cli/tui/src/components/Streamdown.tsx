import { MarkdownView } from "./MarkdownView";

type Props = {
  content: string;
  streaming: boolean;
};

export function Streamdown({ content, streaming }: Props) {
  return <MarkdownView content={content} streaming={streaming} />;
}
