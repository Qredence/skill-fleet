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

interface JobsTabProps {
  apiUrl: string;
  isActive: boolean;
}

interface Job {
  id: string;
  status: "pending" | "running" | "completed" | "failed";
  type: string;
  progress?: number;
  result?: any;
  error?: string;
  created_at?: string;
}

export const JobsTab: React.FC<JobsTabProps> = ({ apiUrl, isActive }) => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (!isActive) {
      return;
    }

    loadJobs();
    
    // Auto-refresh every 2 seconds
    const interval = autoRefresh ? setInterval(loadJobs, 2000) : undefined;
    return () => {
      if (interval) clearInterval(interval);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setLoading(false);
    }
  };

  if (!isActive) {
    return null;
  }

  if (loading && jobs.length === 0) {
    return (
      <Box flexDirection="column" paddingX={2}>
        <Text color="blue" bold>
          ⚙️ Job Monitor
        </Text>
        <Box marginTop={1}>
          <Text color="cyan">
            <Spinner type="dots" />
          </Text>
          <Text color="gray"> Loading jobs...</Text>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box flexDirection="column" paddingX={2}>
        <Text color="blue" bold>
          ⚙️ Job Monitor
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

  const runningJobs = jobs.filter((j) => j.status === "running" || j.status === "pending");
  const completedJobs = jobs.filter((j) => j.status === "completed");
  const failedJobs = jobs.filter((j) => j.status === "failed");

  return (
    <Box flexDirection="column" paddingX={2} flexGrow={1}>
      <Box flexDirection="row" justifyContent="space-between" marginBottom={1}>
        <Text color="blue" bold>
          ⚙️ Job Monitor ({jobs.length} total)
        </Text>
        <Text color="gray">
          {autoRefresh ? "🔄 Auto-refresh: ON" : "⏸️  Auto-refresh: OFF"}
        </Text>
      </Box>

      {/* Running Jobs */}
      {runningJobs.length > 0 && (
        <Box flexDirection="column" marginTop={1} gap={1}>
          <Text color="cyan" bold>
            ⏳ Running ({runningJobs.length})
          </Text>
          {runningJobs.map((job) => (
            <Box key={job.id} flexDirection="column" gap={0}>
              <Box flexDirection="row" gap={1}>
                <Text color="cyan">
                  <Spinner type="dots" />
                </Text>
                <Text color="white">{job.id}</Text>
              </Box>
              <Text color="gray" wrap="wrap">
                  {job.type} - {job.progress || 0}% complete
              </Text>
            </Box>
          ))}
        </Box>
      )}

      {/* Completed Jobs */}
      {completedJobs.length > 0 && (
        <Box flexDirection="column" marginTop={1} gap={1}>
          <Text color="green" bold>
            ✅ Completed ({completedJobs.length})
          </Text>
          {completedJobs.slice(0, 3).map((job) => (
            <Box key={job.id} flexDirection="row" gap={1}>
              <Text color="green">✓</Text>
              <Text color="white">{job.id}</Text>
              <Text color="gray">- {job.type}</Text>
            </Box>
          ))}
        </Box>
      )}

      {/* Failed Jobs */}
      {failedJobs.length > 0 && (
        <Box flexDirection="column" marginTop={1} gap={1}>
          <Text color="red" bold>
            ❌ Failed ({failedJobs.length})
          </Text>
          {failedJobs.slice(0, 2).map((job) => (
            <Box key={job.id} flexDirection="column" gap={0}>
              <Box flexDirection="row" gap={1}>
                <Text color="red">✗</Text>
                <Text color="white">{job.id}</Text>
              </Box>
              {job.error && (
                <Text color="gray" wrap="wrap">  Error: {job.error.substring(0, 80)}...</Text>
              )}
            </Box>
          ))}
        </Box>
      )}

      {/* No Jobs */}
      {jobs.length === 0 && (
        <Box marginTop={1}>
          <Text color="yellow">No jobs yet.</Text>
        </Box>
      )}

      <Box marginTop={2} borderStyle="single" borderColor="gray" paddingX={1} paddingY={1}>
        <Text color="gray" wrap="wrap">
          💡 Commands: /status job_id | /optimize | Press R to refresh
        </Text>
      </Box>
    </Box>
  );
};
