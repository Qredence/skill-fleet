/**
 * Optimization Tab - Configure and run optimizers
 *
 * Features:
 * - Reflection Metrics highlighted (4400x faster, $0.01 cost)
 * - Optimizer comparison table
 * - Quick-start optimization
 * - Training data selection
 */
import React from "react";
interface OptimizationTabProps {
    apiUrl: string;
    isActive: boolean;
    onOptimize?: (optimizer: string, trainset: string) => void;
}
export declare const OptimizationTab: React.FC<OptimizationTabProps>;
export {};
