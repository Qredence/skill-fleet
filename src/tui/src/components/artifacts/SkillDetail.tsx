// @ts-nocheck
/** @jsxImportSource @opentui/react */
import { TextAttributes } from "@opentui/core";
import { useEffect, useState } from "react";
import path from "node:path";
import { fsService } from "../../services/fileSystem";
import { SKILLS_FLEET_THEME } from "../../themes";

interface SkillDetailProps {
  skillPath: string; // Absolute path to the skill directory or file
}

export function SkillDetail({ skillPath }: SkillDetailProps) {
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const colors = SKILLS_FLEET_THEME;

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        // If it's a directory, look for SKILL.md
        let targetFile = skillPath;
        if (!skillPath.endsWith(".md") && !skillPath.endsWith(".json")) {
            // Assume directory
            targetFile = path.join(skillPath, "SKILL.md");
        }
        
        const text = await fsService.readFile(targetFile);
        setContent(text || "(Empty or unable to read file)");
      } finally {
        setLoading(false);
      }
    }
    if (skillPath) load();
  }, [skillPath]);

  return (
    <box flexDirection="column" flexGrow={1} height="100%">
      <box
        style={{
          borderBottom: true as any,
          borderColor: colors.border,
          paddingBottom: 1,
          marginBottom: 1,
        }}
      >
        <text
          content="SKILL PREVIEW"
          style={{ fg: colors.text.accent, attributes: TextAttributes.BOLD }}
        />
        <text
          content={path.basename(skillPath)}
          style={{ fg: colors.text.dim, attributes: TextAttributes.DIM }}
        />
      </box>

      <box flexGrow={1} flexDirection="column">
        {loading ? (
          <text content="Loading..." style={{ fg: colors.text.dim }} />
        ) : (
          <text
            content={content}
            style={{ fg: colors.text.primary }}
          />
        )}
      </box>
    </box>
  );
}
