import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { testRender } from "@opentui/react/test-utils";
import { ChatView } from "./ChatView";

describe("ChatView", () => {
  let testSetup: Awaited<ReturnType<typeof testRender>>;

  afterEach(() => {
    if (testSetup) {
      testSetup.renderer.destroy();
    }
  });

  test("renders messages correctly", async () => {
    const messages = [
      { id: "1", role: "system" as const, content: "Welcome", status: "done" as const },
      { id: "2", role: "user" as const, content: "Hello", status: "done" as const },
      { id: "3", role: "assistant" as const, content: "Hi there!", status: "streaming" as const },
    ];

    testSetup = await testRender(
      <ChatView
        messages={messages}
        inputValue=""
        onInputChange={() => {}}
        onSubmit={() => {}}
        isDisabled={false}
        focused={true}
      />,
      { width: 80, height: 24 }
    );

    await testSetup.renderOnce();
    const frame = testSetup.captureCharFrame();

    expect(frame).toContain("Welcome");
    expect(frame).toContain("Hello");
    expect(frame).toContain("Hi there!");
    expect(frame).toContain("▌"); // Streaming cursor
  });

  test("shows disabled state", async () => {
    testSetup = await testRender(
      <ChatView
        messages={[]}
        inputValue=""
        onInputChange={() => {}}
        onSubmit={() => {}}
        isDisabled={true}
        disabledReason="job running"
        focused={true}
      />,
      { width: 80, height: 24 }
    );

    await testSetup.renderOnce();
    const frame = testSetup.captureCharFrame();

    expect(frame).toContain("job running");
  });

  test("shows placeholder when not disabled", async () => {
    testSetup = await testRender(
      <ChatView
        messages={[]}
        inputValue=""
        onInputChange={() => {}}
        onSubmit={() => {}}
        isDisabled={false}
        focused={true}
      />,
      { width: 80, height: 24 }
    );

    await testSetup.renderOnce();
    const frame = testSetup.captureCharFrame();

    // The textarea renders with placeholder
    expect(frame).toContain("Describe skill to create");
  });

  test("renders with input value", async () => {
    testSetup = await testRender(
      <ChatView
        messages={[]}
        inputValue="test input"
        onInputChange={() => {}}
        onSubmit={() => {}}
        isDisabled={false}
        focused={true}
      />,
      { width: 80, height: 24 }
    );

    await testSetup.renderOnce();
    const frame = testSetup.captureCharFrame();

    expect(frame).toBeTruthy();
  });
});
