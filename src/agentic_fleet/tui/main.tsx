// @ts-nocheck
import { createCliRenderer, ConsolePosition, type KeyEvent } from "@opentui/core"
import { createRoot, useKeyboard, useRenderer } from "@opentui/react"
import { readFileSync } from "node:fs"
import path from "node:path"
import process from "node:process"
import { useCallback, useState, useEffect, useMemo } from "react"
import YAML from "yaml"

// Import components
import { AppShell } from "./src/components/layout/AppShell"
import { InputArea } from "./src/components/chat/InputArea"
import { MessageList } from "./src/components/chat/MessageList"
import { SuggestionList } from "./src/components/chat/SuggestionList"
import { CatalogTree } from "./src/components/artifacts/CatalogTree"
import { SkillDetail } from "./src/components/artifacts/SkillDetail"
import { WorkflowDashboard } from "./src/components/artifacts/WorkflowDashboard"
import { SKILLS_FLEET_THEME } from "./src/themes"
import { UIProvider, useUI } from "./src/hooks/useUI"
import { cli } from "./src/services/cliBridge"
import type { InputMode, AppSettings, Message, UISuggestion, WorkflowState } from "./src/types"

type FleetConfig = {
  models?: {
    default?: string
    registry?: Record<string, { model?: string }>
  }
  tasks?: Record<string, { model?: string }>
}

function loadFleetConfig(configPath: string): FleetConfig {
  try {
    const raw = readFileSync(configPath, "utf-8")
    return YAML.parse(raw) as FleetConfig
  } catch (e) {
    return {}
  }
}

const repoRoot = process.cwd()
const configPath = path.join(repoRoot, "src/agentic_fleet/config.yaml")
const config = loadFleetConfig(configPath)

const COMMANDS: UISuggestion[] = [
  { label: "create", description: "Create a new skill (e.g. /create async python)", kind: "command", requiresValue: true, score: 0 },
  { label: "catalog", description: "Browse skill catalog", kind: "command", score: 0 },
  { label: "validate", description: "Validate a skill path", kind: "command", requiresValue: true, score: 0 },
  { label: "optimize", description: "Run workflow optimization", kind: "command", score: 0 },
  { label: "help", description: "Show help", kind: "command", score: 0 },
  { label: "close", description: "Close artifact pane", kind: "command", score: 0 },
];

function App() {
  const renderer = useRenderer()
  const { setArtifactMode, artifactMode } = useUI()
  
  const [task, setTask] = useState("")
  const [running, setRunning] = useState(false)
  const [focused, setFocused] = useState(true)
  const [status, setStatus] = useState({ label: "idle", color: "#22c55e" })
  const [elapsedSec, setElapsedSec] = useState(0)
  const [cacheStats, setCacheStats] = useState("")
  const [selectedSkillPath, setSelectedSkillPath] = useState<string | null>(null)
  
  const [workflowState, setWorkflowState] = useState<WorkflowState>({
    steps: {
        understand: "pending",
        plan: "pending",
        initialize: "pending",
        edit: "pending",
        package: "pending",
        validate: "pending"
    },
    activeStep: null,
    currentIteration: 0,
    maxIterations: 3
  });

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "system",
      content: "Welcome to Skills Fleet TUI. Type /create to build a new skill.",
      timestamp: new Date()
    }
  ])

  const [suggestionIndex, setSuggestionIndex] = useState(0);

  const suggestions = useMemo(() => {
    if (!task.startsWith("/")) return [];
    const query = task.slice(1).toLowerCase().split(" ")[0];
    return COMMANDS.filter(c => c.label.toLowerCase().startsWith(query));
  }, [task]);

  useEffect(() => {
    setSuggestionIndex(0);
  }, [suggestions.length]);
  
  const colors = SKILLS_FLEET_THEME
  const inputMode: InputMode = "chat"
  
  const settings: AppSettings = {
    theme: "dark",
    showTimestamps: false,
    autoScroll: true,
    version: 1,
    keybindings: {
        nextSuggestion: [],
        prevSuggestion: [],
        autocomplete: []
    },
    provider: "deepinfra",
    model: config.models?.default || "Gemini",
  }

  useKeyboard((key: KeyEvent) => {
    if (key.ctrl && key.name === "c") {
      renderer.stop()
      process.exit(0)
    }
    if (key.ctrl && key.name === "l") {
      renderer.console.toggle()
      setFocused(!renderer.console.visible)
    }
    if (key.name === "escape") {
        if (suggestions.length > 0) {
            if (task === "/") setTask("");
            return;
        }
      renderer.stop()
      process.exit(0)
    }

    if (suggestions.length > 0) {
        if (key.name === "up") {
          setSuggestionIndex(prev => Math.max(0, prev - 1));
          return; 
        }
        if (key.name === "down") {
          setSuggestionIndex(prev => Math.min(suggestions.length - 1, prev + 1));
          return;
        }
        if (key.name === "tab" || key.name === "enter") {
           const selected = suggestions[suggestionIndex];
           if (selected) {
               setTask("/" + selected.label + " ");
               return;
           }
        }
      }
  })

  useEffect(() => {
    let interval: Timer;
    if (running) {
      setElapsedSec(0);
      interval = setInterval(() => {
        setElapsedSec(s => s + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [running]);

  const handleSelectSkill = useCallback((path: string) => {
    setSelectedSkillPath(path);
    setArtifactMode("preview");
  }, [setArtifactMode]);

  const parseWorkflowLog = (text: string) => {
      if (text.includes("Step 1: UNDERSTAND")) {
          setWorkflowState(prev => ({ ...prev, activeStep: "understand", steps: { ...prev.steps, understand: "running" } }));
      } else if (text.includes("Step 2: PLAN")) {
          setWorkflowState(prev => ({ 
              ...prev, 
              activeStep: "plan", 
              steps: { ...prev.steps, understand: "completed", plan: "running" } 
          }));
      } else if (text.includes("Step 3: INITIALIZE")) {
          setWorkflowState(prev => ({ 
              ...prev, 
              activeStep: "initialize", 
              steps: { ...prev.steps, plan: "completed", initialize: "running" } 
          }));
      } else if (text.includes("Step 4: EDIT")) {
          setWorkflowState(prev => ({ 
              ...prev, 
              activeStep: "edit", 
              steps: { ...prev.steps, initialize: "completed", edit: "running" } 
          }));
      } else if (text.includes("Step 5: PACKAGE")) {
          setWorkflowState(prev => ({ 
              ...prev, 
              activeStep: "package", 
              steps: { ...prev.steps, edit: "completed", package: "running" } 
          }));
      } else if (text.includes("Validation Report")) {
           setWorkflowState(prev => ({ 
              ...prev, 
              activeStep: "validate", 
              steps: { ...prev.steps, package: "completed", validate: "running" } 
          }));
      } else if (text.includes("Skill approved")) {
           setWorkflowState(prev => ({ 
              ...prev, 
              activeStep: null, 
              steps: { ...prev.steps, validate: "completed" } 
          }));
      }
      
      const iterMatch = text.match(/Iteration (\d+)\/(\d+)/);
      if (iterMatch) {
          setWorkflowState(prev => ({
              ...prev,
              currentIteration: parseInt(iterMatch[1]),
              maxIterations: parseInt(iterMatch[2])
          }));
      }
  };

  const handleSubmit = useCallback(
    async (value: string) => {
      const input = value.trim()
      if (!input || running) return

      const userMsg: Message = {
        id: Date.now().toString(),
        role: "user",
        content: input,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, userMsg])
      setTask("")

      if (input.startsWith("/")) {
          const parts = input.split(" ");
          const cmd = parts[0];
          const args = parts.slice(1).join(" ");

          if (cmd === "/catalog") {
            setArtifactMode("catalog")
            return
          }
          if (cmd === "/close") {
            setArtifactMode("none")
            return
          }
          if (cmd === "/create") {
              if (!args) return; 
              setArtifactMode("log");
              setWorkflowState({
                  steps: {
                    understand: "pending", plan: "pending", initialize: "pending",
                    edit: "pending", package: "pending", validate: "pending"
                  },
                  activeStep: null,
                  currentIteration: 0,
                  maxIterations: 3
              });
          }
      }

      const isCreate = input.startsWith("/create") || !input.startsWith("/");
      const taskDescription = input.startsWith("/create") ? input.slice(7).trim() : input;
      let outputBuffer = ""
      let assistantMsgId: string | null = null

      try {
        if (!isCreate) {
          setStatus({ label: "idle", color: "#22c55e" })
          return
        }

        setRunning(true)
        setStatus({ label: "running", color: "#f59e0b" })
        setCacheStats("")

        assistantMsgId = (Date.now() + 1).toString()
        setMessages(prev => [...prev, {
          id: assistantMsgId,
          role: "assistant",
          content: "", 
          timestamp: new Date()
        }])

        if (isCreate) {
            const exitCode = await cli.createSkill(taskDescription, (event) => {
                if (event.type === "stdout" || event.type === "stderr") {
                   const text = event.data || ""
                   outputBuffer += text
                   parseWorkflowLog(text);
                   
                   setMessages(prev => prev.map(m => 
                     m.id === assistantMsgId 
                       ? { ...m, content: outputBuffer }
                       : m
                   ))
                }
            });
            if (exitCode === 0) setStatus({ label: "done", color: "#22c55e" })
            else setStatus({ label: `failed (exit ${exitCode})`, color: "#ef4444" })
        } 
      } catch (error) {
        setStatus({ label: "error", color: "#ef4444" })
        if (assistantMsgId) {
          outputBuffer += `\nError: ${String(error)}`
          setMessages(prev => prev.map(m => 
              m.id === assistantMsgId 
                ? { ...m, content: outputBuffer }
                : m
          ))
        }
      } finally {
        setRunning(false)
        setFocused(true)
        renderer.requestRender()
      }
    },
    [renderer, running, setArtifactMode],
  )

  const statusProps = {
    isProcessing: running,
    elapsedSec: elapsedSec,
    mode: "standard" as const,
    settings: settings,
    inputMode: inputMode,
    colors: colors,
  }

  let ArtifactContent = (
    <box>
        <text content="Empty Artifact" style={{fg: colors.text.dim}} />
    </box>
  )

  if (artifactMode === "catalog") {
      ArtifactContent = (
        <box flexDirection="column" flexGrow={1} height="100%">
            <CatalogTree repoRoot={repoRoot} onSelect={handleSelectSkill} />
        </box>
      )
  } else if (artifactMode === "preview" && selectedSkillPath) {
      ArtifactContent = <SkillDetail skillPath={selectedSkillPath} />
  } else if (artifactMode === "log") {
      ArtifactContent = <WorkflowDashboard state={workflowState} />
  }

  return (
    <AppShell 
        artifactPane={ArtifactContent}
        statusProps={statusProps}
    >
        <box flexDirection="column" height="100%">
            <box
              id="body"
              flexGrow={1}
              flexDirection="column"
              style={{ overflow: 'hidden' }}
            >
              <MessageList 
                messages={messages}
                isProcessing={running}
                spinnerFrame="⠋"
                colors={colors}
              />
            </box>

            <box flexShrink={0}>
                {suggestions.length > 0 && task.startsWith("/") && (
                    <SuggestionList 
                        suggestions={suggestions}
                        selectedIndex={suggestionIndex}
                        scrollOffset={0}
                        inputMode="command"
                        input={task}
                        colors={colors}
                    />
                )}

                <InputArea
                  input={task}
                  inputMode={inputMode}
                  isProcessing={running}
                  isFocused={focused}
                  placeholder="Type /create [task] or /catalog"
                  hint="Try /catalog, /create [task]"
                  colors={colors}
                  onInput={setTask}
                  onSubmit={() => handleSubmit(task)}
                />
            </box>
        </box>
    </AppShell>
  )
}

function Root() {
    return (
        <UIProvider>
            <App />
        </UIProvider>
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

createRoot(renderer).render(<Root />)
renderer.start()
