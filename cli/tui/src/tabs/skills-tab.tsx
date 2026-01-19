/**
 * Skills Tab - Browse, validate, and manage skills
 * 
 * Features:
 * - List all skills with category filtering
 * - Select and validate skills
 * - Promote drafts
 * - Quick actions menu
 */

import React, { useEffect, useState } from "react";
import { Box, Text } from "ink";
import SelectInput from "ink-select-input";
import Spinner from "ink-spinner";

interface SkillsTabProps {
  apiUrl: string;
  isActive: boolean;
}

interface Skill {
  path: string;
  name: string;
  category?: string;
  description?: string;
}

interface SelectItem {
  label: string;
  value: string;
}

export const SkillsTab: React.FC<SkillsTabProps> = ({ apiUrl, isActive }) => {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);

  useEffect(() => {
    if (isActive) {
      loadSkills();
    }
  }, [isActive]);

  const loadSkills = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/api/v2/skills`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch skills: ${response.status}`);
      }

      const data = await response.json();
      setSkills(Array.isArray(data) ? data : []);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setLoading(false);
    }
  };

  const handleSelect = (item: SelectItem) => {
    const skill = skills.find((s) => s.path === item.value);
    setSelectedSkill(skill || null);
  };

  if (!isActive) {
    return null;
  }

  if (loading) {
    return (
      <Box flexDirection="column" paddingX={2}>
        <Text color="blue" bold>
          📚 Skills Manager
        </Text>
        <Box marginTop={1}>
          <Text color="cyan">
            <Spinner type="dots" />
          </Text>
          <Text color="gray"> Loading skills...</Text>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box flexDirection="column" paddingX={2}>
        <Text color="blue" bold>
          📚 Skills Manager
        </Text>
        <Box marginTop={1}>
          <Text color="red">❌ Error: {error}</Text>
        </Box>
        <Box marginTop={1}>
          <Text color="gray">
            Make sure the API server is running: uv run skill-fleet serve
          </Text>
        </Box>
      </Box>
    );
  }

  if (skills.length === 0) {
    return (
      <Box flexDirection="column" paddingX={2}>
        <Text color="blue" bold>
          📚 Skills Manager
        </Text>
        <Box marginTop={1}>
          <Text color="yellow">No skills found.</Text>
        </Box>
        <Box marginTop={1}>
          <Text color="gray">
            Create your first skill: /create or switch to Chat tab
          </Text>
        </Box>
      </Box>
    );
  }

  const skillItems: SelectItem[] = skills.map((skill) => ({
    label: `${skill.path} - ${skill.description || 'No description'}`,
    value: skill.path,
  }));

  return (
    <Box flexDirection="column" paddingX={2} flexGrow={1}>
      <Text color="blue" bold>
        📚 Skills Manager ({skills.length} skills)
      </Text>

      <Box marginTop={1} flexDirection="column" flexGrow={1}>
        {selectedSkill ? (
          <Box flexDirection="column" gap={1}>
            <Text color="green" bold>
              Selected: {selectedSkill.path}
            </Text>
            <Text color="gray" wrap="wrap">{selectedSkill.description}</Text>
            
            <Box marginTop={1}>
              <Text color="cyan" wrap="wrap">
                Actions: /validate {selectedSkill.path} | /promote | [Esc] to deselect
              </Text>
            </Box>
          </Box>
        ) : (
          <Box flexDirection="column" gap={1}>
            <Text color="gray">Select a skill:</Text>
            <Box marginTop={1}>
              <SelectInput items={skillItems} onSelect={handleSelect} />
            </Box>
          </Box>
        )}
      </Box>

      <Box marginTop={2} borderStyle="single" borderColor="gray" paddingX={1} paddingY={1}>
        <Text color="gray" wrap="wrap">
          💡 Commands: /list [--filter cat] | /validate path | /promote job_id
        </Text>
      </Box>
    </Box>
  );
};
