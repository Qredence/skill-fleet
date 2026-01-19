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

interface OptimizationTabProps {
  apiUrl: string;
  isActive: boolean;
  onOptimize?: (optimizer: string, trainset: string) => void;
}

interface SelectItem {
  label: string;
  value: string;
}

const OPTIMIZERS: SelectItem[] = [
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

const TRAINSETS: SelectItem[] = [
  {
    label: "📊 trainset_v4.json (50 examples) - Recommended",
    value: "trainset_v4.json",
  },
  {
    label: "📊 trainset_v3.json (24 examples)",
    value: "trainset_v3.json",
  },
];

export const OptimizationTab: React.FC<OptimizationTabProps> = ({
  apiUrl,
  isActive,
  onOptimize,
}) => {
  const [step, setStep] = useState<"optimizer" | "trainset" | "confirm">("optimizer");
  const [selectedOptimizer, setSelectedOptimizer] = useState<string>("");
  const [selectedTrainset, setSelectedTrainset] = useState<string>("");

  const handleOptimizerSelect = (item: SelectItem) => {
    setSelectedOptimizer(item.value);
    setStep("trainset");
  };

  const handleTrainsetSelect = (item: SelectItem) => {
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

  return (
    <Box flexDirection="column" paddingX={2} height={20}>
      <Text color="blue" bold>
        🚀 Optimization Control
      </Text>

      {/* Reflection Metrics Highlight */}
      <Box
        marginTop={1}
        marginBottom={1}
        borderStyle="round"
        borderColor="green"
        paddingX={1}
      >
        <Box flexDirection="column">
          <Text color="green" bold>
            ⚡ Reflection Metrics - FASTEST OPTIMIZER
          </Text>
          <Text color="gray">
            • 4400x faster than MIPROv2 (&lt;1 second)
          </Text>
          <Text color="gray">
            • Cost: $0.01-0.05 (vs $5-10 for MIPROv2)
          </Text>
          <Text color="gray">
            • Quality: +1.5% improvement over baseline
          </Text>
          <Text color="cyan">
            Quick start: /optimize reflection_metrics trainset_v4.json
          </Text>
        </Box>
      </Box>

      {/* Optimizer Selection */}
      {step === "optimizer" && (
        <Box flexDirection="column">
          <Text color="cyan">Step 1: Select Optimizer</Text>
          <Box marginTop={1}>
            <SelectInput items={OPTIMIZERS} onSelect={handleOptimizerSelect} />
          </Box>
        </Box>
      )}

      {/* Trainset Selection */}
      {step === "trainset" && (
        <Box flexDirection="column">
          <Text color="green">
            ✓ Optimizer: {selectedOptimizer}
          </Text>
          <Box marginTop={1}>
            <Text color="cyan">
              Step 2: Select Training Data
            </Text>
          </Box>
          <Box marginTop={1}>
            <SelectInput items={TRAINSETS} onSelect={handleTrainsetSelect} />
          </Box>
        </Box>
      )}

      {/* Confirmation */}
      {step === "confirm" && (
        <Box flexDirection="column">
          <Text color="green">
            ✓ Optimizer: {selectedOptimizer}
          </Text>
          <Text color="green">
            ✓ Trainset: {selectedTrainset}
          </Text>
          
          <Box marginTop={2} borderStyle="double" borderColor="yellow" paddingX={1}>
            <Box flexDirection="column">
              <Text color="yellow" bold>
                Ready to optimize!
              </Text>
              <Box marginTop={1}>
                <Text color="gray">
                  This will:
                  - Train on {selectedTrainset.includes('v4') ? '50' : '24'} examples
                  - Use {selectedOptimizer} algorithm
                  - Save results to config/optimized/
                </Text>
              </Box>
              <Box marginTop={1}>
                <Text color="cyan">
                  Press Enter to confirm, or Esc to cancel
                </Text>
              </Box>
            </Box>
          </Box>
        </Box>
      )}

      {/* Comparison Table */}
      <Box marginTop={2} borderStyle="single" borderColor="gray" paddingX={1}>
        <Box flexDirection="column">
          <Text color="gray" bold>
            Optimizer Comparison:
          </Text>
          <Text color="gray">
            reflection_metrics: &lt;1s, $0.01, +1.5% quality
          </Text>
          <Text color="gray">
            mipro: 4-6min, $5-10, +10-15% quality
          </Text>
          <Text color="gray">
            bootstrap: 30s, $0.50, +5-8% quality
          </Text>
        </Box>
      </Box>
    </Box>
  );
};
