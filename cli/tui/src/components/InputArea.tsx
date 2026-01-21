import React, { useRef, useEffect } from "react";
import { Box, Text } from "ink";
import TextInput from "ink-text-input";

interface InputAreaProps {
  input: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  isReady?: boolean;
}

export const InputArea: React.FC<InputAreaProps> = ({
  input,
  onChange,
  onSubmit,
  isReady = true,
}) => {
  return (
    <Box flexDirection="column" marginTop={0}>
      <Box
        borderStyle="single"
        borderColor={isReady ? "gray" : "blue"}
        paddingX={1}
      >
        <Box marginRight={1}>
          <Text color={isReady ? "green" : "blue"}>❯</Text>
        </Box>
        <TextInput
          value={input}
          onChange={onChange}
          onSubmit={onSubmit}
          placeholder={
            isReady ? "Type a message or /command..." : "Processing..."
          }
        />
      </Box>
      <Box marginTop={0} marginLeft={1}>
        <Text color="gray" dimColor>
          {isReady ? "Ready" : "Thinking..."}
        </Text>
      </Box>
    </Box>
  );
};
