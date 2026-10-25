/**
 * AgentRouter JavaScript / Node.js Client
 * Zero dependencies - uses native fetch and streams.
 */

export const DEFAULT_BASE_URL = "https://agentrouter.org";
export const DEFAULT_USER_AGENT = "claude-cli/2.0.0 (external, cli)";
export const DEFAULT_MODEL = "gpt-6.1-sol";

export class AgentRouterError extends Error {
  constructor(message, status = null, responseBody = null) {
    super(status ? `[${status}] ${message}` : message);
    this.name = "AgentRouterError";
    this.status = status;
    this.responseBody = responseBody;
  }
}

export class AgentRouter {
  /**
   * @param {Object} [options]
   * @param {string} [options.apiKey]
   * @param {string} [options.baseUrl]
   * @param {string} [options.defaultModel]
   * @param {string} [options.userAgent]
   */
  constructor(options = {}) {
    this.apiKey = options.apiKey || (typeof process !== "undefined" ? process.env.AGENTROUTER_API_KEY : null);
    if (!this.apiKey) {
      throw new AgentRouterError(
        "No API key provided. Pass apiKey in options or set AGENTROUTER_API_KEY environment variable."
      );
    }
    this.baseUrl = (options.baseUrl || DEFAULT_BASE_URL).replace(/\/$/, "");
    this.defaultModel = options.defaultModel || DEFAULT_MODEL;
    this.userAgent = options.userAgent || DEFAULT_USER_AGENT;

    this.messages = {
      create: this._createMessage.bind(this),
      stream: this._streamMessage.bind(this),
    };

    this.models = {
      raw: this._rawModels.bind(this),
      list: this._listModels.bind(this),
      get: this._getModel.bind(this),
      ids: this._listModelIds.bind(this),
    };
  }

  /**
   * Simple one-liner chat method.
   * @param {string} prompt
   * @param {Object} [options]
   * @returns {Promise<string>}
   */
  async chat(prompt, options = {}) {
    const res = await this._createMessage({
      messages: [{ role: "user", content: prompt }],
      model: options.model || this.defaultModel,
      system: options.system,
      max_tokens: options.max_tokens,
      temperature: options.temperature,
    });
    return res.text;
  }

  /**
   * Stream text tokens for a prompt.
   * @param {string} prompt
   * @param {Object} [options]
   * @returns {AsyncGenerator<string>}
   */
  async *stream(prompt, options = {}) {
    yield* this._streamMessage({
      messages: [{ role: "user", content: prompt }],
      model: options.model || this.defaultModel,
      system: options.system,
      max_tokens: options.max_tokens,
      temperature: options.temperature,
    });
  }

  /**
   * Create a stateful multi-turn conversation.
   * @param {Object} [options]
   */
  conversation(options = {}) {
    const client = this;
    const history = [];
    const model = options.model || this.defaultModel;
    const system = options.system;

    return {
      history,
      clear() {
        history.length = 0;
      },
      async send(prompt) {
        history.push({ role: "user", content: prompt });
        const res = await client.messages.create({
          messages: [...history],
          model,
          system,
          ...options,
        });
        history.push({ role: "assistant", content: res.text });
        return res;
      },
      async *stream(prompt) {
        history.push({ role: "user", content: prompt });
        let accumulated = "";
        for await (const chunk of client.messages.stream({
          messages: [...history],
          model,
          system,
          ...options,
        })) {
          accumulated += chunk;
          yield chunk;
        }
        history.push({ role: "assistant", content: accumulated });
      },
    };
  }

  async _createMessage(params) {
    const body = {
      model: params.model || this.defaultModel,
      messages: params.messages,
    };
    if (params.system) body.system = params.system;
    if (params.max_tokens) body.max_tokens = params.max_tokens;
    if (params.temperature !== undefined) body.temperature = params.temperature;

    const data = await this._request("/v1/messages", "POST", body);
    const content = data.content || [];
    const text = content.map((c) => c.text || "").join("");
    return {
      id: data.id,
      model: data.model,
      role: data.role || "assistant",
      content,
      text,
      stop_reason: data.stop_reason,
      usage: data.usage || {},
      raw: data,
    };
  }

  async *_streamMessage(params) {
    const body = {
      model: params.model || this.defaultModel,
      messages: params.messages,
      stream: true,
    };
    if (params.system) body.system = params.system;
    if (params.max_tokens) body.max_tokens = params.max_tokens;
    if (params.temperature !== undefined) body.temperature = params.temperature;

    const response = await fetch(`${this.baseUrl}/v1/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "User-Agent": this.userAgent,
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new AgentRouterError(errText, response.status);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith("event:")) continue;
        if (trimmed.startsWith("data:")) {
          const dataStr = trimmed.substring(5).trim();
          if (dataStr === "[DONE]") return;
          try {
            const parsed = JSON.parse(dataStr);
            const delta = parsed.delta;
            if (delta && delta.text) {
              yield delta.text;
            } else if (parsed.type === "content_block_delta" && parsed.delta?.text) {
              yield parsed.delta.text;
            } else if (parsed.choices?.[0]?.delta?.content) {
              yield parsed.choices[0].delta.content;
            }
          } catch (_) {
            // Ignore parse errors on malformed chunks
          }
        }
      }
    }
  }

  async _rawModels() {
    return await this._request("/v1/models", "GET");
  }

  async _listModels() {
    const data = await this._rawModels();
    return data.data || [];
  }

  async _getModel(modelId) {
    const models = await this._listModels();
    return models.find((m) => m.id.toLowerCase() === modelId.toLowerCase()) || null;
  }

  async _listModelIds() {
    const models = await this._listModels();
    return models.map((m) => m.id);
  }

  async _request(path, method, body = null) {
    const headers = {
      "Content-Type": "application/json",
      "User-Agent": this.userAgent,
      Authorization: `Bearer ${this.apiKey}`,
    };

    const res = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      let msg = res.statusText;
      try {
        const errJson = await res.json();
        msg = errJson.error?.message || JSON.stringify(errJson);
      } catch (_) {
        msg = await res.text();
      }
      throw new AgentRouterError(msg, res.status);
    }

    return await res.json();
  }
}

export default AgentRouter;
