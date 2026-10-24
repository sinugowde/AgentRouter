export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ContentBlock {
  type: string;
  text: string;
}

export interface Usage {
  input_tokens?: number;
  output_tokens?: number;
  cache_creation_input_tokens?: number;
  cache_read_input_tokens?: number;
}

export interface MessageResponse {
  id: string;
  model: string;
  role: string;
  content: ContentBlock[];
  text: string;
  stop_reason?: string;
  usage: Usage;
  raw: any;
}

export interface CreateMessageOptions {
  messages: Message[];
  model?: string;
  system?: string;
  max_tokens?: number;
  temperature?: number;
}

export interface ChatOptions {
  model?: string;
  system?: string;
  max_tokens?: number;
  temperature?: number;
}

export interface AgentRouterOptions {
  apiKey?: string;
  baseUrl?: string;
  defaultModel?: string;
  userAgent?: string;
}

export interface ConversationSession {
  history: Message[];
  clear(): void;
  send(prompt: string): Promise<MessageResponse>;
  stream(prompt: string): AsyncGenerator<string>;
}

export class AgentRouterError extends Error {
  status?: number;
  responseBody?: any;
}

export class AgentRouter {
  apiKey: string;
  baseUrl: string;
  defaultModel: string;
  userAgent: string;

  messages: {
    create(params: CreateMessageOptions): Promise<MessageResponse>;
    stream(params: CreateMessageOptions): AsyncGenerator<string>;
  };

  models: {
    list(): Promise<any[]>;
  };

  constructor(options?: AgentRouterOptions);
  chat(prompt: string, options?: ChatOptions): Promise<string>;
  stream(prompt: string, options?: ChatOptions): AsyncGenerator<string>;
  conversation(options?: ChatOptions): ConversationSession;
}

export default AgentRouter;
