import React from "react";
import { Box, Text } from "ink";
import SelectInput from "ink-select-input";

interface CommandOverlayProps {
  onSelect: (item: { label: string; value: string }) => void;
  onCancel?: () => void;
}

const COMMANDS = [
  {
    label: "/config   Manage configuration (API keys, etc.)",
    value: "/config",
  },
  { label: "/status   Show current application status", value: "/status" },
  { label: "/model    Switch AI model", value: "/model" },
  { label: "/think    Toggle explain-mode", value: "/think" },
  { label: "/agent    Manage subagents or delegate tasks", value: "/agent" },
  { label: "/clear    Clear conversation history", value: "/clear" },
  { label: "/jobs     Monitor running jobs", value: "/jobs" },
  { label: "/skills   Manage skills", value: "/list" },
  { label: "/help     Show help", value: "/help" },
];

export const CommandOverlay: React.FC<CommandOverlayProps> = ({ onSelect }) => {
  return (
    <Box
      borderStyle="single"
      borderColor="cyan"
      flexDirection="column"
      paddingX={1}
      width="100%"
    >
      <SelectInput<any> items={COMMANDS} onSelect={onSelect} limit={6} />
      <Box
        marginTop={1}
        borderStyle="single"
        borderTop
        borderBottom={false}
        borderLeft={false}
        borderRight={false}
        borderColor="gray"
      >
        <Text color="gray" dimColor>
          ↑/↓ navigate • Enter run • Esc close
        </Text>
      </Box>
    </Box>
  );
};
