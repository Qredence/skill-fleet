/**
 * Command Executor - Parses and executes explicit commands
 *
 * Supports:
 * - /optimize [optimizer] [trainset] - Run optimization
 * - /list [--filter category] - List skills
 * - /validate [path] - Validate skill
 * - /promote [job_id] - Promote draft to taxonomy
 * - /status [job_id] - Check job status
 * - /help - Show help
 */
export interface CommandResult {
    success: boolean;
    message: string;
    data?: any;
    jobId?: string;
}
export interface ExecutorOptions {
    apiUrl: string;
    onProgress?: (message: string) => void;
}
export declare class CommandExecutor {
    private apiUrl;
    private onProgress?;
    constructor(options: ExecutorOptions);
    /**
     * Parse command from user input
     */
    parseCommand(input: string): {
        command: string;
        args: string[];
    } | null;
    /**
     * Execute a command and return result
     */
    execute(input: string): Promise<CommandResult>;
    /**
     * Execute /optimize command
     */
    private executeOptimize;
    /**
     * Execute /list command
     */
    private executeList;
    /**
     * Execute /validate command
     */
    private executeValidate;
    /**
     * Execute /promote command
     */
    private executePromote;
    /**
     * Execute /status command
     */
    private executeStatus;
    /**
     * Execute /help command
     */
    private executeHelp;
}
