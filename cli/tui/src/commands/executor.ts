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

export class CommandExecutor {
  private apiUrl: string;
  private onProgress?: (message: string) => void;

  constructor(options: ExecutorOptions) {
    this.apiUrl = options.apiUrl;
    this.onProgress = options.onProgress;
  }

  /**
   * Parse command from user input
   */
  parseCommand(input: string): { command: string; args: string[] } | null {
    if (!input.startsWith('/')) {
      return null;
    }

    const parts = input.slice(1).trim().split(/\s+/);
    return {
      command: parts[0],
      args: parts.slice(1),
    };
  }

  /**
   * Execute a command and return result
   */
  async execute(input: string): Promise<CommandResult> {
    const parsed = this.parseCommand(input);
    
    if (!parsed) {
      return {
        success: false,
        message: "Not a command. Commands start with /",
      };
    }

    const { command, args } = parsed;

    try {
      switch (command) {
        case 'optimize':
          return await this.executeOptimize(args);
        case 'list':
          return await this.executeList(args);
        case 'validate':
          return await this.executeValidate(args);
        case 'promote':
          return await this.executePromote(args);
        case 'status':
          return await this.executeStatus(args);
        case 'help':
          return this.executeHelp();
        default:
          return {
            success: false,
            message: `Unknown command: /${command}\nTry /help for available commands`,
          };
      }
    } catch (error) {
      return {
        success: false,
        message: `Command failed: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  }

  /**
   * Execute /optimize command
   */
  private async executeOptimize(args: string[]): Promise<CommandResult> {
    const optimizer = args[0] || 'reflection_metrics';
    const trainset = args[1] || 'trainset_v4.json';

    this.onProgress?.(`Starting optimization with ${optimizer}...`);

    const response = await fetch(`${this.apiUrl}/api/v1/optimization/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        optimizer_type: optimizer,
        trainset_path: `config/training/${trainset}`,
        auto_level: 'medium',
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json() as any;
    
    return {
      success: true,
      message: `✅ Optimization started!\n\nJob ID: ${data.job_id}\nOptimizer: ${optimizer}\nTrainset: ${trainset}\n\nCheck status with: /status ${data.job_id}`,
      jobId: data.job_id,
      data,
    };
  }

  /**
   * Execute /list command
   */
  private async executeList(args: string[]): Promise<CommandResult> {
    const filterIdx = args.indexOf('--filter');
    const filter = filterIdx !== -1 && args[filterIdx + 1] ? args[filterIdx + 1] : undefined;

    this.onProgress?.('Fetching skills...');

    const url = filter
      ? `${this.apiUrl}/api/v1/taxonomy?category=${filter}`
      : `${this.apiUrl}/api/v1/taxonomy/`;

    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const skills = await response.json() as any;
    
    const skillList = Array.isArray(skills) 
      ? skills.map((s: any) => `  • ${s.path || s.name}`).join('\n')
      : `  • ${(skills as any).length || 0} skills found`;

    return {
      success: true,
      message: `📚 Skills${filter ? ` (${filter})` : ''}:\n\n${skillList}`,
      data: skills,
    };
  }

  /**
   * Execute /validate command
   */
  private async executeValidate(args: string[]): Promise<CommandResult> {
    const skillPath = args[0];

    if (!skillPath) {
      return {
        success: false,
        message: 'Usage: /validate <skill_path>\nExample: /validate skills/python/async',
      };
    }

    this.onProgress?.(`Validating ${skillPath}...`);

    const response = await fetch(
      `${this.apiUrl}/api/v1/quality/validate?skill_path=${encodeURIComponent(skillPath)}`
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json() as any;

    const status = result.passed ? '✅ PASS' : '❌ FAIL';
    const score = result.score ? ` (score: ${result.score})` : '';
    
    return {
      success: result.passed,
      message: `${status}${score}\n\nSkill: ${skillPath}\n${result.message || ''}`,
      data: result,
    };
  }

  /**
   * Execute /promote command
   */
  private async executePromote(args: string[]): Promise<CommandResult> {
    const jobId = args[0];

    if (!jobId) {
      return {
        success: false,
        message: 'Usage: /promote <job_id>\nExample: /promote job-abc123',
      };
    }

    this.onProgress?.(`Promoting draft ${jobId}...`);

    const response = await fetch(`${this.apiUrl}/api/v1/drafts/${jobId}/promote`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json() as any;

    return {
      success: true,
      message: `✅ Draft promoted!\n\nPath: ${result.path || 'Unknown'}\nJob ID: ${jobId}`,
      data: result,
    };
  }

  /**
   * Execute /status command
   */
  private async executeStatus(args: string[]): Promise<CommandResult> {
    const jobId = args[0];

    if (!jobId) {
      return {
        success: false,
        message: 'Usage: /status <job_id>\nExample: /status job-abc123',
      };
    }

    this.onProgress?.(`Checking status for ${jobId}...`);

    const response = await fetch(`${this.apiUrl}/api/v1/jobs/${jobId}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const job = await response.json() as any;

    const statusIcon = job.status === 'completed' ? '✅' : job.status === 'failed' ? '❌' : '⏳';
    
    return {
      success: true,
      message: `${statusIcon} Job Status\n\nID: ${jobId}\nStatus: ${job.status}\nProgress: ${job.progress || 'N/A'}`,
      data: job,
    };
  }

  /**
   * Execute /help command
   */
  private executeHelp(): CommandResult {
    return {
      success: true,
      message: `📖 Available Commands:

/optimize [optimizer] [trainset] - Run optimization
  Example: /optimize reflection_metrics trainset_v4.json
  Optimizers: reflection_metrics, mipro, bootstrap

/list [--filter category] - List skills
  Example: /list --filter python

/validate <path> - Validate a skill
  Example: /validate skills/python/async

/promote <job_id> - Promote draft to taxonomy
  Example: /promote job-abc123

/status <job_id> - Check job status
  Example: /status job-abc123

/help - Show this help

💡 Tip: You can also use natural language!
   "optimize my skill with reflection metrics"
   "show me python skills"
   "validate the async skill"`,
    };
  }
}
