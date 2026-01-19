/**
 * Jobs Tab - Monitor running optimization and creation jobs
 *
 * Features:
 * - Real-time job status polling
 * - Progress indicators with ink-spinner
 * - Job result display
 * - Quick actions (cancel, view results)
 */
import React from "react";
interface JobsTabProps {
    apiUrl: string;
    isActive: boolean;
}
export declare const JobsTab: React.FC<JobsTabProps>;
export {};
