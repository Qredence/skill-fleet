/**
 * Optimization Tab - Configure and run optimizers
 *
 * Features:
 * - Reflection Metrics highlighted (4400x faster, $0.01 cost)
 * - Optimizer comparison table
 * - Quick-start optimization
 * - Training data selection
 */
import React, { useState } from "react";
import { Box, Text } from "ink";
import SelectInput from "ink-select-input";
const OPTIMIZERS = [
    {
        label: "⚡ Reflection Metrics (RECOMMENDED) - <1s, $0.01",
        value: "reflection_metrics",
    },
    {
        label: "🔬 MIPROv2 - Medium speed, $5-10",
        value: "mipro",
    },
    {
        label: "🎯 Bootstrap Few-Shot - Fast, $0.50",
        value: "bootstrap",
    },
];
const TRAINSETS = [
    {
        label: "📊 trainset_v4.json (50 examples) - Recommended",
        value: "trainset_v4.json",
    },
    {
        label: "📊 trainset_v3.json (24 examples)",
        value: "trainset_v3.json",
    },
];
export const OptimizationTab = ({ apiUrl, isActive, onOptimize, }) => {
    const [step, setStep] = useState("optimizer");
    const [selectedOptimizer, setSelectedOptimizer] = useState("");
    const [selectedTrainset, setSelectedTrainset] = useState("");
    const handleOptimizerSelect = (item) => {
        setSelectedOptimizer(item.value);
        setStep("trainset");
    };
    const handleTrainsetSelect = (item) => {
        setSelectedTrainset(item.value);
        setStep("confirm");
    };
    const handleConfirm = () => {
        if (onOptimize && selectedOptimizer && selectedTrainset) {
            onOptimize(selectedOptimizer, selectedTrainset);
            // Reset
            setStep("optimizer");
            setSelectedOptimizer("");
            setSelectedTrainset("");
        }
    };
    if (!isActive) {
        return null;
    }
    return (React.createElement(Box, { flexDirection: "column", paddingX: 2, flexGrow: 1 },
        React.createElement(Text, { color: "blue", bold: true }, "\uD83D\uDE80 Optimization Control"),
        React.createElement(Box, { marginTop: 1, marginBottom: 1, borderStyle: "round", borderColor: "green", paddingX: 1, paddingY: 1 },
            React.createElement(Box, { flexDirection: "column", gap: 1 },
                React.createElement(Text, { color: "green", bold: true }, "\u26A1 Reflection Metrics - FASTEST OPTIMIZER"),
                React.createElement(Text, { color: "gray", wrap: "wrap" }, "\u2022 4400x faster than MIPROv2 (<1 second)"),
                React.createElement(Text, { color: "gray", wrap: "wrap" }, "\u2022 Cost: $0.01-0.05 (vs $5-10 for MIPROv2)"),
                React.createElement(Text, { color: "gray", wrap: "wrap" }, "\u2022 Quality: +1.5% improvement over baseline"),
                React.createElement(Text, { color: "cyan", wrap: "wrap" }, "Quick start: /optimize reflection_metrics trainset_v4.json"))),
        step === "optimizer" && (React.createElement(Box, { flexDirection: "column", gap: 1 },
            React.createElement(Text, { color: "cyan" }, "Step 1: Select Optimizer"),
            React.createElement(SelectInput, { items: OPTIMIZERS, onSelect: handleOptimizerSelect }))),
        step === "trainset" && (React.createElement(Box, { flexDirection: "column", gap: 1 },
            React.createElement(Text, { color: "green" },
                "\u2713 Optimizer: ",
                selectedOptimizer),
            React.createElement(Text, { color: "cyan" }, "Step 2: Select Training Data"),
            React.createElement(SelectInput, { items: TRAINSETS, onSelect: handleTrainsetSelect }))),
        step === "confirm" && (React.createElement(Box, { flexDirection: "column", gap: 1 },
            React.createElement(Text, { color: "green" },
                "\u2713 Optimizer: ",
                selectedOptimizer),
            React.createElement(Text, { color: "green" },
                "\u2713 Trainset: ",
                selectedTrainset),
            React.createElement(Box, { marginTop: 1, borderStyle: "double", borderColor: "yellow", paddingX: 2, paddingY: 1 },
                React.createElement(Box, { flexDirection: "column", gap: 1 },
                    React.createElement(Text, { color: "yellow", bold: true }, "Ready to optimize!"),
                    React.createElement(Box, { flexDirection: "column" },
                        React.createElement(Text, { color: "gray" }, "This will:"),
                        React.createElement(Text, { color: "gray", wrap: "wrap" },
                            "\u2022 Train on ",
                            selectedTrainset.includes('v4') ? '50' : '24',
                            " examples"),
                        React.createElement(Text, { color: "gray", wrap: "wrap" },
                            "\u2022 Use ",
                            selectedOptimizer,
                            " algorithm"),
                        React.createElement(Text, { color: "gray", wrap: "wrap" }, "\u2022 Save results to config/optimized/")),
                    React.createElement(Text, { color: "cyan", wrap: "wrap" }, "Press Enter to confirm, or Esc to cancel"))))),
        React.createElement(Box, { marginTop: 2, borderStyle: "single", borderColor: "gray", paddingX: 1, paddingY: 1 },
            React.createElement(Box, { flexDirection: "column", gap: 1 },
                React.createElement(Text, { color: "gray", bold: true }, "Optimizer Comparison:"),
                React.createElement(Text, { color: "gray", wrap: "wrap" }, "reflection_metrics: <1s, $0.01, +1.5% quality"),
                React.createElement(Text, { color: "gray", wrap: "wrap" }, "mipro: 4-6min, $5-10, +10-15% quality"),
                React.createElement(Text, { color: "gray", wrap: "wrap" }, "bootstrap: 30s, $0.50, +5-8% quality")))));
};
//# sourceMappingURL=optimization-tab.js.map