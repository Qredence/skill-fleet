import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { testRender } from "@opentui/react/test-utils";
import { HitlManager } from "./HitlManager";
import type { HitlPrompt } from "../../lib/types";

describe("HitlManager", () => {
  let testSetup: Awaited<ReturnType<typeof testRender>>;

  afterEach(() => {
    if (testSetup) {
      testSetup.renderer.destroy();
    }
  });

  test("renders confirm prompt", async () => {
    const prompt: HitlPrompt = {
      status: "pending_hitl",
      type: "confirm",
      content: "Do you want to proceed?",
      validation_passed: false,
    };

    testSetup = await testRender(
      <HitlManager
        prompt={prompt}
        focused={true}
        onSubmit={() => {}}
      />,
      { width: 80, height: 24 }
    );

    await testSetup.renderOnce();
    const frame = testSetup.captureCharFrame();

    expect(frame).toContain("Do you want to proceed?");
    expect(frame).toContain("Revise");
    expect(frame).toContain("Make changes");
    expect(frame).toContain("Enter to select");
  });

  test("renders clarify prompt with questions", async () => {
    const prompt: HitlPrompt = {
      status: "pending_hitl",
      type: "clarify",
      questions: [
        {
          text: "What is your name?",
          options: [
            { id: "1", label: "Alice" },
            { id: "2", label: "Bob" },
          ],
          allows_multiple: false,
        },
      ],
    };

    testSetup = await testRender(
      <HitlManager
        prompt={prompt}
        focused={true}
        onSubmit={() => {}}
      />,
      { width: 80, height: 24 }
    );

    await testSetup.renderOnce();
    const frame = testSetup.captureCharFrame();

    expect(frame).toContain("What is your name?");
    expect(frame).toContain("Alice");
    expect(frame).toContain("[1/1]");
  });

  test("renders default fallback for unknown type", async () => {
    const prompt: HitlPrompt = {
      status: "pending_hitl",
      type: "unknown_type",
      content: "Please respond to this prompt",
    };

    testSetup = await testRender(
      <HitlManager
        prompt={prompt}
        focused={true}
        onSubmit={() => {}}
      />,
      { width: 80, height: 24 }
    );

    await testSetup.renderOnce();
    const frame = testSetup.captureCharFrame();

    expect(frame).toContain("Please respond to this prompt");
    expect(frame).toContain("Press Tab then Enter to continue");
  });

  test("renders clarify with rationale", async () => {
    const prompt: HitlPrompt = {
      status: "pending_hitl",
      type: "clarify",
      questions: [
        {
          text: "Choose an option",
          rationale: "This helps us understand your preference",
          options: [{ id: "1", label: "Option 1" }],
        },
      ],
    };

    testSetup = await testRender(
      <HitlManager
        prompt={prompt}
        focused={true}
        onSubmit={() => {}}
      />,
      { width: 80, height: 24 }
    );

    await testSetup.renderOnce();
    const frame = testSetup.captureCharFrame();

    expect(frame).toContain("Choose an option");
    expect(frame).toContain("This helps us understand your preference");
  });
});
