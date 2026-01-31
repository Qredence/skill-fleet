import React from 'react';
import { Box, Text } from 'ink';

interface HeaderProps {
  model?: string;
  explainMode?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  model = "Gemini 3 Flash Preview (gemini)",
  explainMode = false
}) => {
  return (
    <Box
      borderStyle="single"
      borderColor="blue"
      paddingX={1}
      paddingY={0}
      flexDirection="row"
      justifyContent="space-between"
      marginBottom={1}
    >
      <Text bold color="cyan">AI Agent CLI</Text>
      <Text>
        <Text color="gray">Model: </Text>
        <Text color="blue">{model}</Text>
        <Text color="gray"> | </Text>
        <Text color="gray">Explain: </Text>
        <Text color={explainMode ? "green" : "gray"}>
          {explainMode ? "ON" : "OFF"}
        </Text>
      </Text>
    </Box>
  );
};
