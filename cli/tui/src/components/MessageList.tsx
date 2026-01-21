import React from "react";
import { Box, Text } from "ink";

interface Message {
  id: string;
  role: string;
  content: string;
  thinking_type?: string;
  timestamp?: string;
  step?: number;
}

interface MessageListProps {
  messages: Message[];
}

export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  // Use column-reverse to keep content anchored to the bottom ("sticky scrolldown")
  // We must reverse the messages array so the newest (last in array) becomes the first in the reversed column (bottom)
  const reversedMessages = [...messages].reverse();

  return (
    <Box flexDirection="column-reverse" flexGrow={1} overflow="hidden">
      {reversedMessages.map((msg) => {
        if (msg.role === "thinking") {
          // Format thinking like qlaus-code:
          // Indented, gray.
          // If content starts with "Observation:", bold it.
          const content = msg.content;
          const isBlockHeader =
            content.includes("Observation:") ||
            content.includes("Approach:") ||
            content.includes("Steps:") ||
            content.includes("FINAL ANSWER");

          return (
            <Box key={msg.id} marginLeft={2} marginBottom={0}>
              <Text color="gray" dimColor={!isBlockHeader} bold={isBlockHeader}>
                {msg.content}
              </Text>
            </Box>
          );
        }

        const isUser = msg.role === "user";
        const isAssistant = msg.role === "assistant";
        const isSystem = msg.role === "system";

        return (
          <Box key={msg.id} flexDirection="column" marginBottom={1}>
            {/* Header */}
            {!isSystem && (
              <Box marginBottom={0}>
                <Text color={isUser ? "cyan" : "green"} bold>
                  {isUser ? "You" : "AI"}
                </Text>
                <Text color="gray" dimColor>
                  {" "}
                  • {msg.timestamp || new Date().toLocaleTimeString()}{" "}
                </Text>
                {isAssistant && (
                  <Text color="gray" dimColor>
                    {" "}
                    • Gemini 3 Flash Preview
                  </Text>
                )}
              </Box>
            )}

            {/* Content */}
            <Box marginLeft={isSystem ? 0 : 0}>
              <Text color={isSystem ? "magenta" : isUser ? "white" : "white"}>
                {msg.content}
              </Text>
            </Box>
          </Box>
        );
      })}
    </Box>
  );
};
