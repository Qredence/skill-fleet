/**
 * Jobs Tab - Monitor running optimization and creation jobs
 *
 * Features:
 * - Real-time job status polling
 * - Progress indicators with ink-spinner
 * - Job result display
 * - Quick actions (cancel, view results)
 */
import React, { useEffect, useState } from "react";
import { Box, Text } from "ink";
import Spinner from "ink-spinner";
export const JobsTab = ({ apiUrl, isActive }) => {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [autoRefresh, setAutoRefresh] = useState(true);
    useEffect(() => {
        if (!isActive) {
            return;
        }
        loadJobs();
        // Auto-refresh every 2 seconds
        const interval = autoRefresh ? setInterval(loadJobs, 2000) : undefined;
        return () => {
            if (interval)
                clearInterval(interval);
        };
    }, [isActive, autoRefresh]);
    const loadJobs = async () => {
        try {
            const response = await fetch(`${apiUrl}/api/v2/jobs`);
            if (!response.ok) {
                throw new Error(`Failed to fetch jobs: ${response.status}`);
            }
            const data = await response.json();
            setJobs(Array.isArray(data) ? data : []);
            setLoading(false);
            setError(null);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : String(err));
            setLoading(false);
        }
    };
    if (!isActive) {
        return null;
    }
    if (loading && jobs.length === 0) {
        return (React.createElement(Box, { flexDirection: "column", paddingX: 2 },
            React.createElement(Text, { color: "blue", bold: true }, "\u2699\uFE0F Job Monitor"),
            React.createElement(Box, { marginTop: 1 },
                React.createElement(Text, { color: "cyan" },
                    React.createElement(Spinner, { type: "dots" })),
                React.createElement(Text, { color: "gray" }, " Loading jobs..."))));
    }
    if (error) {
        return (React.createElement(Box, { flexDirection: "column", paddingX: 2 },
            React.createElement(Text, { color: "blue", bold: true }, "\u2699\uFE0F Job Monitor"),
            React.createElement(Box, { marginTop: 1 },
                React.createElement(Text, { color: "red" },
                    "\u274C Error: ",
                    error)),
            React.createElement(Box, { marginTop: 1 },
                React.createElement(Text, { color: "gray" }, "Make sure the API server is running: uv run skill-fleet serve"))));
    }
    const runningJobs = jobs.filter((j) => j.status === "running" || j.status === "pending");
    const completedJobs = jobs.filter((j) => j.status === "completed");
    const failedJobs = jobs.filter((j) => j.status === "failed");
    return (React.createElement(Box, { flexDirection: "column", paddingX: 2, flexGrow: 1 },
        React.createElement(Box, { flexDirection: "row", justifyContent: "space-between", marginBottom: 1 },
            React.createElement(Text, { color: "blue", bold: true },
                "\u2699\uFE0F Job Monitor (",
                jobs.length,
                " total)"),
            React.createElement(Text, { color: "gray" }, autoRefresh ? "🔄 Auto-refresh: ON" : "⏸️  Auto-refresh: OFF")),
        runningJobs.length > 0 && (React.createElement(Box, { flexDirection: "column", marginTop: 1, gap: 1 },
            React.createElement(Text, { color: "cyan", bold: true },
                "\u23F3 Running (",
                runningJobs.length,
                ")"),
            runningJobs.map((job) => (React.createElement(Box, { key: job.id, flexDirection: "column", gap: 0 },
                React.createElement(Box, { flexDirection: "row", gap: 1 },
                    React.createElement(Text, { color: "cyan" },
                        React.createElement(Spinner, { type: "dots" })),
                    React.createElement(Text, { color: "white" }, job.id)),
                React.createElement(Text, { color: "gray", wrap: "wrap" },
                    job.type,
                    " - ",
                    job.progress || 0,
                    "% complete")))))),
        completedJobs.length > 0 && (React.createElement(Box, { flexDirection: "column", marginTop: 1, gap: 1 },
            React.createElement(Text, { color: "green", bold: true },
                "\u2705 Completed (",
                completedJobs.length,
                ")"),
            completedJobs.slice(0, 3).map((job) => (React.createElement(Box, { key: job.id, flexDirection: "row", gap: 1 },
                React.createElement(Text, { color: "green" }, "\u2713"),
                React.createElement(Text, { color: "white" }, job.id),
                React.createElement(Text, { color: "gray" },
                    "- ",
                    job.type)))))),
        failedJobs.length > 0 && (React.createElement(Box, { flexDirection: "column", marginTop: 1, gap: 1 },
            React.createElement(Text, { color: "red", bold: true },
                "\u274C Failed (",
                failedJobs.length,
                ")"),
            failedJobs.slice(0, 2).map((job) => (React.createElement(Box, { key: job.id, flexDirection: "column", gap: 0 },
                React.createElement(Box, { flexDirection: "row", gap: 1 },
                    React.createElement(Text, { color: "red" }, "\u2717"),
                    React.createElement(Text, { color: "white" }, job.id)),
                job.error && (React.createElement(Text, { color: "gray", wrap: "wrap" },
                    "  Error: ",
                    job.error.substring(0, 80),
                    "..."))))))),
        jobs.length === 0 && (React.createElement(Box, { marginTop: 1 },
            React.createElement(Text, { color: "yellow" }, "No jobs yet."))),
        React.createElement(Box, { marginTop: 2, borderStyle: "single", borderColor: "gray", paddingX: 1, paddingY: 1 },
            React.createElement(Text, { color: "gray", wrap: "wrap" }, "\uD83D\uDCA1 Commands: /status job_id | /optimize | Press R to refresh"))));
};
//# sourceMappingURL=jobs-tab.js.map