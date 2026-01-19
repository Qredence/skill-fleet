/**
 * Skills Tab - Browse, validate, and manage skills
 *
 * Features:
 * - List all skills with category filtering
 * - Select and validate skills
 * - Promote drafts
 * - Quick actions menu
 */
import React from "react";
interface SkillsTabProps {
    apiUrl: string;
    isActive: boolean;
}
export declare const SkillsTab: React.FC<SkillsTabProps>;
export {};
