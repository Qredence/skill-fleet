// @ts-nocheck
/** @jsxImportSource @opentui/react */
import { TextAttributes } from "@opentui/core";
import { useEffect, useState, useCallback } from "react";
import path from "node:path";
import { fsService, type FileNode } from "../../services/fileSystem";
import { SKILLS_FLEET_THEME } from "../../themes";

interface CatalogTreeProps {
  repoRoot: string;
  onSelect?: (path: string) => void;
}

interface TreeNodeProps {
  node: FileNode;
  depth: number;
  selectedPath: string | null;
  expandedPaths: Set<string>;
  onSelect: (node: FileNode) => void;
  onToggle: (node: FileNode) => void;
}

function TreeNode({ node, depth, selectedPath, expandedPaths, onSelect, onToggle }: TreeNodeProps) {
  const isSelected = selectedPath === node.path;
  const isExpanded = expandedPaths.has(node.path);
  const colors = SKILLS_FLEET_THEME;
  const indent = depth * 2;

  // Modern Icons (resembling Nerdfonts / VS Code)
  // ▼ for expanded, ▶ for collapsed
  // 📂 / 📄 for types
  const expandIcon = node.isDirectory ? (isExpanded ? "▼ " : "▶ ") : "  ";
  const typeIcon = node.isDirectory ? "📂" : "📄";
  
  return (
    <box flexDirection="column">
      <box
        style={{
          flexDirection: "row",
          height: 1,
          paddingLeft: indent,
          backgroundColor: isSelected ? colors.bg.hover : "transparent",
        }}
        selectable
        onMouseDown={() => {
          onSelect(node);
          if (node.isDirectory) onToggle(node);
        }}
        onKeyDown={(key) => {
          if (key.name === "return" || key.name === "space") {
            key.preventDefault();
            onSelect(node);
            if (node.isDirectory) onToggle(node);
          } else if (key.name === "right" && node.isDirectory && !isExpanded) {
            key.preventDefault();
            onSelect(node);
            onToggle(node);
          } else if (key.name === "left" && node.isDirectory && isExpanded) {
            key.preventDefault();
            onSelect(node);
            onToggle(node);
          }
        }}
      >
        <text
          content={`${expandIcon}${typeIcon} ${node.name}`}
          style={{
            fg: isSelected ? colors.text.accent : colors.text.primary,
            attributes: isSelected ? TextAttributes.BOLD : 0,
          }}
        />
      </box>
      {/* Only render children container if expanded and has non-empty children array */}
      {isExpanded && node.children && node.children.length > 0 && (
        <box flexDirection="column">
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              expandedPaths={expandedPaths}
              onSelect={onSelect}
              onToggle={onToggle}
            />
          ))}
        </box>
      )}
    </box>
  );
}

export function CatalogTree({ repoRoot, onSelect }: CatalogTreeProps) {
  const [rootNodes, setRootNodes] = useState<FileNode[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());
  const colors = SKILLS_FLEET_THEME;
  const skillsRoot = path.join(repoRoot, "skills");

  useEffect(() => {
    async function load() {
      // Load root
      const nodes = await fsService.readDir(skillsRoot);
      // Pre-populate children for expanded nodes (if any logic for auto-expand exists)
      // For now, simple load
      setRootNodes(nodes);
    }
    load();
  }, [repoRoot]);

  // Handle toggling directory expansion
  const toggleNode = useCallback(async (node: FileNode) => {
    if (!node.isDirectory) return;

    const newExpanded = new Set(expandedPaths);
    if (newExpanded.has(node.path)) {
      // Collapse already expanded node
      newExpanded.delete(node.path);
      setExpandedPaths(newExpanded);
      return;
    }

    // Expanding node: ensure children are loaded before marking as expanded
    if (!node.children) {
      try {
      // Collapse already expanded node
      newExpanded.delete(node.path);
      setExpandedPaths(newExpanded);
      return;
    }

    // Expanding node: ensure children are loaded before marking as expanded
    if (!node.children) {
      try {
        const children = await fsService.readDir(node.path);
        node.children = children;
      } catch (e) {
        // If we cannot read the directory, do not mark it as expanded
        return;
      }
    }

    newExpanded.add(node.path);

    newExpanded.add(node.path);
    setExpandedPaths(newExpanded);
  }, [expandedPaths]);

  // TODO: Add Keyboard navigation to select/toggle nodes (Up/Down/Enter/Right/Left)
  // This requires lifting state up or using a focus manager hook.
  // For this iteration, we'll assume visual update first.

  return (
    <box flexDirection="column" flexGrow={1}>
      <box
        style={{
          border: true, 
          height: 3,
          borderColor: colors.border,
          paddingBottom: 0,
          marginBottom: 1,
          flexDirection: "column",
        }}
      >
        <text
          content="SKILL CATALOG"
          style={{ fg: colors.text.secondary, attributes: TextAttributes.BOLD }}
        />
        <text
          content={skillsRoot}
          style={{ fg: colors.text.dim, attributes: TextAttributes.DIM }}
        />
      </box>

      <box flexDirection="column" flexGrow={1}>
        {rootNodes.map((node) => (
          <TreeNode
            key={node.path}
            node={node}
            depth={0}
            selectedPath={selectedPath}
            expandedPaths={expandedPaths}
            onSelect={(n) => {
                setSelectedPath(n.path);
                if (onSelect && !n.isDirectory) onSelect(n.path);
            }}
            onToggle={toggleNode}
          />
        ))}
      </box>
    </box>
  );
}
