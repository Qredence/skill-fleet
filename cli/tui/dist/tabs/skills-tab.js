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
export const SkillsTab = ({ apiUrl, isActive }) => {
    const [skills, setSkills] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedSkill, setSelectedSkill] = useState(null);
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
        }
        catch (err) {
            setError(err instanceof Error ? err.message : String(err));
            setLoading(false);
        }
    };
    const handleSelect = (item) => {
        const skill = skills.find((s) => s.path === item.value);
        setSelectedSkill(skill || null);
    };
    if (!isActive) {
        return null;
    }
    if (loading) {
        return (React.createElement(Box, { flexDirection: "column", paddingX: 2 },
            React.createElement(Text, { color: "blue", bold: true }, "\uD83D\uDCDA Skills Manager"),
            React.createElement(Box, { marginTop: 1 },
                React.createElement(Text, { color: "cyan" },
                    React.createElement(Spinner, { type: "dots" })),
                React.createElement(Text, { color: "gray" }, " Loading skills..."))));
    }
    if (error) {
        return (React.createElement(Box, { flexDirection: "column", paddingX: 2 },
            React.createElement(Text, { color: "blue", bold: true }, "\uD83D\uDCDA Skills Manager"),
            React.createElement(Box, { marginTop: 1 },
                React.createElement(Text, { color: "red" },
                    "\u274C Error: ",
                    error)),
            React.createElement(Box, { marginTop: 1 },
                React.createElement(Text, { color: "gray" }, "Make sure the API server is running: uv run skill-fleet serve"))));
    }
    if (skills.length === 0) {
        return (React.createElement(Box, { flexDirection: "column", paddingX: 2 },
            React.createElement(Text, { color: "blue", bold: true }, "\uD83D\uDCDA Skills Manager"),
            React.createElement(Box, { marginTop: 1 },
                React.createElement(Text, { color: "yellow" }, "No skills found.")),
            React.createElement(Box, { marginTop: 1 },
                React.createElement(Text, { color: "gray" }, "Create your first skill: /create or switch to Chat tab"))));
    }
    const skillItems = skills.map((skill) => ({
        label: `${skill.path} - ${skill.description || 'No description'}`,
        value: skill.path,
    }));
    return (React.createElement(Box, { flexDirection: "column", paddingX: 2, height: 20 },
        React.createElement(Text, { color: "blue", bold: true },
            "\uD83D\uDCDA Skills Manager (",
            skills.length,
            " skills)"),
        React.createElement(Box, { marginTop: 1, flexDirection: "column" }, selectedSkill ? (React.createElement(Box, { flexDirection: "column" },
            React.createElement(Text, { color: "green", bold: true },
                "Selected: ",
                selectedSkill.path),
            React.createElement(Text, { color: "gray" }, selectedSkill.description),
            React.createElement(Box, { marginTop: 1 },
                React.createElement(Text, { color: "cyan" },
                    "Actions: /validate ",
                    selectedSkill.path,
                    " | /promote | [Esc] to deselect")))) : (React.createElement(Box, { flexDirection: "column" },
            React.createElement(Text, { color: "gray" }, "Select a skill:"),
            React.createElement(Box, { marginTop: 1 },
                React.createElement(SelectInput, { items: skillItems, onSelect: handleSelect }))))),
        React.createElement(Box, { marginTop: 2, borderStyle: "single", borderColor: "gray", paddingX: 1 },
            React.createElement(Text, { color: "gray" }, "\uD83D\uDCA1 Commands: /list [--filter cat] | /validate path | /promote job_id"))));
};
//# sourceMappingURL=skills-tab.js.map