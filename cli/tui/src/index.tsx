import { createCliRenderer } from "@opentui/core";
import { createRoot } from "@opentui/react";
import { AppShell } from "./app/AppShell";

const renderer = await createCliRenderer({ exitOnCtrlC: true });
createRoot(renderer).render(<AppShell />);
