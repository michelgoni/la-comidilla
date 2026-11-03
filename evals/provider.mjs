/**
 * promptfoo provider for La Comidilla.
 *
 * It repeats the request of src/extract.py, because the endpoint rejects
 * anything that does not look like the browser client: the two custom headers
 * (X-Session-Id and x-opencode-session) and the browser user agent are not
 * sent by promptfoo's built-in OpenAI provider.
 *
 * The system prompt is read from prompts/prompt_v4.txt on every call, so the
 * project keeps a single copy of it. Copying it here would leave two versions
 * and the comparison with the 2 November pass would mean nothing.
 */
import { randomBytes } from 'node:crypto';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PROMPT_PATH = path.resolve(HERE, '..', 'prompts', 'prompt_v4.txt');
const SECRETS_PATH = path.join(
  process.env.HOME || '',
  '.hermes',
  'secrets',
  'comidilla.env',
);
const TIMEOUT_MS = 120_000;
const PREVIEW = 400;

/** Read the three settings: the environment wins, the secrets file is the fallback. */
function loadConfig() {
  const read = {
    baseUrl: process.env.COMIDILLA_BASE_URL || '',
    model: process.env.COMIDILLA_MODEL || '',
    apiKey: process.env.COMIDILLA_API_KEY || '',
  };

  let secrets = '';
  try {
    secrets = readFileSync(SECRETS_PATH, 'utf-8');
  } catch {
    secrets = '';
  }
  for (const rawLine of secrets.split('\n')) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const index = line.indexOf('=');
    const name = line.slice(0, index).trim().replace(/^export\s+/, '');
    const key = {
      COMIDILLA_BASE_URL: 'baseUrl',
      COMIDILLA_MODEL: 'model',
      COMIDILLA_API_KEY: 'apiKey',
    }[name];
    if (key && !read[key]) {
      read[key] = line.slice(index + 1).trim().replace(/^["']|["']$/g, '');
    }
  }

  const missing = Object.keys(read).filter((key) => !read[key]);
  if (missing.length) {
    throw new Error(`Missing model configuration: ${missing.join(', ')}`);
  }
  return read;
}

/** Read the prompt; an empty one would let the model improvise. */
function loadPrompt() {
  const prompt = readFileSync(PROMPT_PATH, 'utf-8');
  if (!prompt.trim()) {
    throw new Error(`The prompt ${PROMPT_PATH} is empty.`);
  }
  return prompt;
}

/** Build the request body the same way src/extract.py does. */
function buildPayload(model, prompt, reviewText) {
  return {
    model,
    temperature: 0,
    messages: [
      { role: 'system', content: prompt },
      { role: 'user', content: `Reseña:\n"""\n${reviewText}\n"""` },
    ],
  };
}

/** Keep the token counts when the server reports them; invent nothing when it does not. */
function tokenUsageOf(usage) {
  if (!usage || typeof usage !== 'object') return undefined;
  const { total_tokens: total, prompt_tokens: prompt, completion_tokens: completion } = usage;
  if (typeof total !== 'number' || typeof prompt !== 'number' || typeof completion !== 'number') {
    return undefined;
  }
  return { total, prompt, completion };
}

export default class ComidillaProvider {
  constructor(options = {}) {
    this.providerId = options.id || 'comidilla';
  }

  id() {
    return this.providerId;
  }

  async callApi(prompt, context) {
    let config;
    let systemPrompt;
    try {
      config = loadConfig();
      systemPrompt = loadPrompt();
    } catch (error) {
      return { error: error.message };
    }

    const review = context?.vars?.texto;
    if (typeof review !== 'string' || !review.trim()) {
      return { error: 'The test case has no texto.' };
    }

    const url = `${config.baseUrl.replace(/\/+$/, '')}/chat/completions`;
    let response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${config.apiKey}`,
          'X-Session-Id': randomBytes(8).toString('hex'),
          'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
          'x-opencode-session': 'comidilla',
        },
        body: JSON.stringify(buildPayload(config.model, systemPrompt, review)),
        signal: AbortSignal.timeout(TIMEOUT_MS),
      });
    } catch (error) {
      return { error: `Could not reach the model: ${error.message}` };
    }

    const text = await response.text();
    if (!response.ok) {
      return { error: `The model returned error ${response.status}: ${text.slice(0, PREVIEW)}` };
    }

    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return { error: `The response is not JSON: ${text.slice(0, PREVIEW)}` };
    }

    const answer = data?.choices?.[0]?.message?.content;
    if (typeof answer !== 'string') {
      return { error: `The response has no text: ${text.slice(0, PREVIEW)}` };
    }

    const result = { output: answer, metadata: { model: config.model } };
    const tokenUsage = tokenUsageOf(data.usage);
    if (tokenUsage) result.tokenUsage = tokenUsage;
    return result;
  }
}
