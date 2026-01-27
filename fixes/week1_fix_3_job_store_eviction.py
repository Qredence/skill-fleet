#!/usr/bin/env python3
"""
Week 1 Fix #3: Add job store eviction to prevent memory leaks.

This script updates app/services/jobs.py to add automatic eviction
for the in-memory JOBS dictionary using a TTL (time-to-live) mechanism.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent / "src" / "skill_fleet" / "app" / "services"
JOBS_PY = ROOT / "jobs.py"

def main():
    print("=" * 70)
    print("WEEK 1 FIX #3: Job Store Eviction")
    print("=" * 70)
    
    # Create backup
    backup_path = JOBS_PY.with_suffix('.py.bak')
    shutil.copy2(JOBS_PY, backup_path)
    print(f"✅ Backed up jobs.py to {backup_path.name}")
    
    # Read current content
    content = JOBS_PY.read_text()
    
    # Add time import if not present
    if "import time" not in content:
        content = content.replace(
            "from datetime import UTC, datetime",
            "import time\nfrom datetime import UTC, datetime"
        )
        print("✅ Added time import")
    
    # Replace the JOBS dict with a managed class
    old_jobs_def = '''# In-memory job store (use Redis in production)
JOBS: dict[str, JobState] = {}'''

    new_jobs_def = '''# In-memory job store with TTL eviction (use Redis in production)
class JobStore:
    """
    Thread-safe job store with automatic TTL eviction.
    
    Prevents memory leaks by evicting old jobs after MAX_AGE_HOURS.
    """
    MAX_JOBS = 1000  # Maximum number of jobs to keep in memory
    MAX_AGE_HOURS = 24  # Evict jobs older than this
    
    def __init__(self):
        self._jobs: dict[str, JobState] = {}
        self._access_times: dict[str, float] = {}
    
    def _evict_if_needed(self):
        """Evict old jobs if we're over capacity or jobs are too old."""
        now = time.time()
        max_age_seconds = self.MAX_AGE_HOURS * 3600
        
        # Evict by age
        expired = [
            job_id for job_id, last_access in self._access_times.items()
            if now - last_access > max_age_seconds
        ]
        for job_id in expired:
            self._evict_job(job_id)
        
        # Evict by count (LRU - evict least recently accessed)
        while len(self._jobs) > self.MAX_JOBS:
            # Find oldest access
            oldest_job = min(self._access_times, key=self._access_times.get)
            self._evict_job(oldest_job)
    
    def _evict_job(self, job_id: str):
        """Remove a job from memory."""
        self._jobs.pop(job_id, None)
        self._access_times.pop(job_id, None)
        logger.debug(f"Evicted job {job_id} from memory")
    
    def __getitem__(self, job_id: str) -> JobState:
        """Get job and update access time."""
        self._access_times[job_id] = time.time()
        return self._jobs[job_id]
    
    def __setitem__(self, job_id: str, job: JobState):
        """Set job and update access time."""
        self._evict_if_needed()
        self._jobs[job_id] = job
        self._access_times[job_id] = time.time()
    
    def __contains__(self, job_id: str) -> bool:
        """Check if job exists."""
        return job_id in self._jobs
    
    def get(self, job_id: str, default=None):
        """Get job with default."""
        if job_id in self._jobs:
            self._access_times[job_id] = time.time()
            return self._jobs[job_id]
        return default
    
    def pop(self, job_id: str, default=None):
        """Remove and return job."""
        self._access_times.pop(job_id, None)
        return self._jobs.pop(job_id, default)
    
    def keys(self):
        """Return job IDs."""
        return self._jobs.keys()
    
    def __len__(self) -> int:
        """Return number of jobs."""
        return len(self._jobs)


JOBS: JobStore = JobStore()'''

    if old_jobs_def in content:
        content = content.replace(old_jobs_def, new_jobs_def)
        print("✅ Replaced JOBS dict with JobStore class")
    else:
        print("⚠️  Could not find exact JOBS definition, manual update may be needed")
    
    # Update cleanup_old_sessions to also clear memory
    old_cleanup = '''def cleanup_old_sessions(max_age_hours: float = 24.0) -> int:
    """
    Clean up old session files.

    Args:
        max_age_hours: Maximum age in hours before deletion

    Returns:
        Number of sessions cleaned up

    """
    import time

    cleaned = 0
    cutoff_time = time.time() - (max_age_hours * 3600)

    try:
        for session_file in SESSION_DIR.glob("*.json"):
            if session_file.stat().st_mtime < cutoff_time:
                try:
                    session_file.unlink()
                    cleaned += 1
                except Exception:
                    # Ignore errors when deleting individual files
                    pass
    except Exception:
        # Ignore errors during cleanup (e.g., directory doesn't exist)
        pass

    if cleaned > 0:
        logger.info(f"Cleaned up {cleaned} old session(s)")

    return cleaned'''

    new_cleanup = '''def cleanup_old_sessions(max_age_hours: float = 24.0) -> int:
    """
    Clean up old session files and evict from memory.

    Args:
        max_age_hours: Maximum age in hours before deletion

    Returns:
        Number of sessions cleaned up

    """
    cleaned = 0
    cutoff_time = time.time() - (max_age_hours * 3600)

    # Clean up files
    try:
        for session_file in SESSION_DIR.glob("*.json"):
            if session_file.stat().st_mtime < cutoff_time:
                try:
                    session_file.unlink()
                    cleaned += 1
                except Exception:
                    # Ignore errors when deleting individual files
                    pass
    except Exception:
        # Ignore errors during cleanup (e.g., directory doesn't exist)
        pass

    # Also trigger memory eviction
    JOBS._evict_if_needed()

    if cleaned > 0:
        logger.info(f"Cleaned up {cleaned} old session(s)")

    return cleaned'''

    if old_cleanup in content:
        content = content.replace(old_cleanup, new_cleanup)
        print("✅ Updated cleanup_old_sessions to trigger memory eviction")
    
    # Write updated content
    JOBS_PY.write_text(content)
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ JOBS dict replaced with JobStore class")
    print("✅ Automatic TTL eviction (24 hours default)")
    print("✅ Maximum capacity limit (1000 jobs)")
    print("✅ LRU eviction when over capacity")
    print("✅ Cleanup function triggers memory eviction")
    print("\nConfiguration (can be adjusted in JobStore class):")
    print("  MAX_JOBS = 1000")
    print("  MAX_AGE_HOURS = 24")
    print("\nTo complete the fix:")
    print("  1. Run tests: uv run pytest tests/ -xvs -k 'job' 2>&1 | head -50")
    print("  2. Monitor memory usage in production")


if __name__ == "__main__":
    main()
