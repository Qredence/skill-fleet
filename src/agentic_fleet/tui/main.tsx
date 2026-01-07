#!/usr/bin/env bun
/** @jsxImportSource @opentui/react */

import { createCliRenderer, ConsolePosition, bold, fg, t, type KeyEvent } from "@opentui/core"
import { createRoot, useKeyboard, useRenderer } from "@opentui/react"
import { readFileSync } from "node:fs"
import path from "node:path"
import process from "node:process"
import { useCallback, useMemo, useState } from "react"
import YAML from "yaml"

// Import components
import { Header } from "./src/components/Header"
import { InputArea } from "./src/components/InputArea"
import { StatusLine } from "./src/components/StatusLine"
import { getTheme, type ThemeTokens } from "./src/themes"
import type { InputMode, AppSettings } from "./src/types"

type FleetConfig = {
  models?: {
    default?: string
    registry?: Record<string, { model?: string }>
  }
  tasks?: Record<string, { model?: string }>
}

type StatusState = {
  label: string
  color: string
}

// Skills Fleet specific theme
const SKILLS_FLEET_THEME: ThemeTokens = {
  bg: {
    primary: "#001122",
    secondary: "#0f172a",
    panel: "#0b1220",
    hover: "#1f2937",
  },
  text: {
    primary: "#e2e8f0",
    secondary: "#cbd5e1",
    tertiary: "#94a3b8",
    dim: "#64748b",
    accent: "#22c55e",
  },
  border: "#334155",
  success: "#22c55e",
  error: "#ef4444",
}

function loadFleetConfig(configPath: string): FleetConfig {
  const raw = readFileSync(configPath, "utf-8")
  return YAML.parse(raw) as FleetConfig
}

function formatModelSummary(config: FleetConfig): string {
  const tasks = config.tasks ?? {}
  const lines = [
    "Skill workflow models (from config.yaml):",
    `- default: ${config.models?.default ?? "(unset)"}`,
    `- skill_understand: ${tasks.skill_understand?.model ?? "(unset)"}`,
    `- skill_plan: ${tasks.skill_plan?.model ?? "(unset)"}`,
    `- skill_initialize: ${tasks.skill_initialize?.model ?? "(unset)"}`,
    `- skill_edit: ${tasks.skill_edit?.model ?? "(unset)"}`,
    `- skill_package: ${tasks.skill_package?.model ?? "(unset)"}`,
    `- skill_validate: ${tasks.skill_validate?.model ?? "(unset)"}`,
    "",
    "Controls:",
    "- Enter: run create-skill",
    "- Ctrl+L: toggle logs console",
    "- Esc / Ctrl+C: quit",
  ]
  return lines.join("\n")
}

async function runCreateSkill(task: string, repoRoot: string): Promise<{ exitCode: number; stdout: string }> {
  const proc = Bun.spawn(
    [
      "uv",
      "run",
      "python",
      "-m",
      "agentic_fleet.agentic_skills_system.cli",
      "create-skill",
      "--task",
      task,
      "--cache-dir",
      cacheDir,
      "--json",
    ],
    {
      cwd: repoRoot,
      env: {
        ...process.env,
        UV_CACHE_DIR: ".uv-cache",
        DSPY_CACHEDIR: path.join(repoRoot, ".dspy_cache"),
      },
      stdin: "ignore",
      stdout: "pipe",
      stderr: "pipe",
    },
  )

  const decoder = new TextDecoder()
  let stdout = ""

  const readStdout = (async () => {
    for await (const chunk of proc.stdout) stdout += decoder.decode(chunk)
  })()
  const readStderr = (async () => {
    for await (const chunk of proc.stderr) console.log(decoder.decode(chunk).trimEnd())
  })()

  const exitCode = await proc.exited
  await Promise.all([readStdout, readStderr])
  return { exitCode, stdout }
}

const repoRoot = process.cwd()
const configPath = path.join(repoRoot, "src/agentic_fleet/config.yaml")
const cacheDir = path.join(repoRoot, ".context/cache")
const config = loadFleetConfig(configPath)
const summaryText = formatModelSummary(config)
const headerContent = t`${bold(fg("#e2e8f0")("skills-fleet"))} ${fg("#94a3b8")(
  `- model config: ${path.relative(repoRoot, configPath)}`,
)}`

function App() {
  const renderer = useRenderer()
  const [task, setTask] = useState("")
  const [running, setRunning] = useState(false)
  const [focused, setFocused] = useState(true)
  const [status, setStatus] = useState({ label: "idle", color: "#22c55e" })
  const [elapsedSec, setElapsedSec] = useState(0)
  const [cacheStats, setCacheStats] = useState("")
  
  const colors = SKILLS_FLEET_THEME
  const inputMode: InputMode = "chat"
  
  // Mock settings for StatusLine
  const settings: AppSettings = {
    theme: "dark",
    showTimestamps: false,
    autoScroll: true,
    version: 1,
    keybindings: {
      nextSuggestion: [],
      prevSuggestion: [],
      autocomplete: [],
    },
    provider: "deepinfra",
    model: "Nemotron-3-Nano-30B-A3B",
  }

  const statusContent = useMemo(
    () => t`${fg("#94a3b8")("status:")} ${fg(status.color)(status.label)}`,
    [status],
  )

  useKeyboard((key: KeyEvent) => {
    if (key.ctrl && key.name === "c") {
      renderer.stop()
      process.exit(0)
    }
    if (key.ctrl && key.name === "l") {
      renderer.console.toggle()
      if (renderer.console.visible) {
        setFocused(false)
      } else {
        setFocused(true)
      }
    }
    if (key.name === "escape") {
      renderer.stop()
      process.exit(0)
    }
  })

  const handleSubmit = useCallback(
    async (value: string) => {
      const nextTask = value.trim()
      if (!nextTask || running) return

      setRunning(true)
      setStatus({ label: "running", color: "#f59e0b" })
      setCacheStats("")

      try {
        const { exitCode, stdout } = await runCreateSkill(nextTask, repoRoot)
        let parsed: unknown = null
        try {
          parsed = JSON.parse(stdout)
        } catch {
          console.log(stdout.trimEnd())
        }

        if (exitCode === 0) {
          setStatus({ label: "done", color: "#22c55e" })
        } else {
          setStatus({ label: `failed (exit ${exitCode})`, color: "#ef4444" })
          renderer.console.show()
          renderer.console.blur()
          setFocused(true)
        }

        if (parsed && typeof parsed === "object") {
          const parsedRecord = parsed as Record<string, unknown>
          console.log(JSON.stringify(parsedRecord, null, 2))
          const stats = parsedRecord["cache_stats"] as
            | { hits?: number; misses?: number; hit_rate?: number }
            | undefined
          if (stats) {
            const hits = stats.hits ?? 0
            const misses = stats.misses ?? 0
            const hitRate = stats.hit_rate ?? 0
            setCacheStats(
              `cache hits: ${hits}  misses: ${misses}  hit_rate: ${(hitRate * 100).toFixed(1)}%`,
            )
          }
        }
      } catch (error) {
        setStatus({ label: "failed (spawn error)", color: "#ef4444" })
        console.error(error)
        renderer.console.show()
        renderer.console.blur()
        setFocused(true)
      } finally {
        setTask("")
        setRunning(false)
        setFocused(true)
        renderer.requestRender()
      }
    },
    [renderer, running],
  )

  return (
    <box 
      id="root" 
      width="auto" 
      height="auto" 
      flexDirection="column"
      backgroundColor={colors.bg.primary}
    >
      {/* Custom Skills Fleet Header */}
      <box
        id="header"
        width="auto"
        height={3}
        backgroundColor={colors.bg.panel}
        borderStyle="single"
        borderColor={colors.border}
        alignItems="center"
        paddingLeft={2}
        paddingRight={2}
        border
      >
        <text 
          id="header-text" 
          content={headerContent} 
          flexGrow={1} 
          flexShrink={1} 
        />
      </box>

      {/* Body with model summary and status */}
      <box
        id="body"
        width="auto"
        flexGrow={1}
        flexShrink={1}
        flexDirection="column"
        backgroundColor="transparent"
        paddingLeft={2}
        paddingRight={2}
        paddingTop={1}
      >
        <text 
          id="summary-text" 
          content={summaryText} 
          fg={colors.text.secondary} 
          flexGrow={0} 
          flexShrink={0} 
        />
        <text 
          id="status-text" 
          content={statusContent} 
          fg={status.color}
          flexGrow={0} 
          flexShrink={0} 
          marginTop={1} 
        />
        {cacheStats ? (
          <text
            id="cache-text"
            content={cacheStats}
            fg={colors.text.tertiary}
            flexGrow={0}
            flexShrink={0}
            marginTop={1}
          />
        ) : null}
      </box>

      {/* Input Area using component */}
      <InputArea
        input={task}
        inputMode={inputMode}
        isProcessing={running}
        isFocused={focused}
        placeholder="e.g., Create a Python async programming skill"
        hint="Enter: run create-skill • Ctrl+L: toggle logs • Esc: quit"
        colors={colors}
        onInput={setTask}
        onSubmit={() => handleSubmit(task)}
      />
      
      {/* Status Line */}
      <StatusLine
        isProcessing={running}
        elapsedSec={elapsedSec}
        mode="standard"
        settings={settings}
        inputMode={inputMode}
        suggestionFooter=""
        colors={colors}
      />
    </box>
  )
}

const renderer = await createCliRenderer({
  consoleOptions: {
    position: ConsolePosition.BOTTOM,
    sizePercent: 35,
    startInDebugMode: false,
  },
})
renderer.setBackgroundColor(SKILLS_FLEET_THEME.bg.primary)

createRoot(renderer).render(<App />)
renderer.start()
