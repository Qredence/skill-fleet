import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";

export interface FileNode {
  name: string;
  path: string;
  isDirectory: boolean;
  children?: FileNode[];
  isOpen?: boolean;
}

export class FileSystemService {
  async readDir(dirPath: string): Promise<FileNode[]> {
    try {
      const entries = await readdir(dirPath, { withFileTypes: true });
      
      const nodes: FileNode[] = entries
        .filter(entry => !entry.name.startsWith(".")) // Skip hidden files
        .map((entry) => ({
          name: entry.name,
          path: path.join(dirPath, entry.name),
          isDirectory: entry.isDirectory(),
        }))
        .sort((a, b) => {
          // Folders first, then files
          if (a.isDirectory && !b.isDirectory) return -1;
          if (!a.isDirectory && b.isDirectory) return 1;
          return a.name.localeCompare(b.name);
        });

      return nodes;
    } catch (error) {
      console.error(`Error reading directory ${dirPath}:`, error);
      return [];
    }
  }

  async readFile(filePath: string): Promise<string> {
    try {
      return await readFile(filePath, "utf-8");
    } catch (error) {
      console.error(`Error reading file ${filePath}:`, error);
      return "";
    }
  }
}

export const fsService = new FileSystemService();
