import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { fetch } from 'undici';

const LM_STUDIO_URL = process.env.LM_STUDIO_URL || 'http://localhost:1234';

// Check LM Studio
async function checkLmStudio(): Promise<boolean> {
  try {
    const res = await fetch(`${LM_STUDIO_URL}/v1/models`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

// Hono API app
export const apiApp = new Hono();
apiApp.use('/*', cors({
  origin: ['http://localhost:4321', 'http://127.0.0.1:4321'],
  allowHeaders: ['Content-Type', 'Accept'],
  allowMethods: ['GET', 'POST', 'OPTIONS'],
  exposeHeaders: ['Content-Type'],
}));

apiApp.get('/api/models', async (c) => {
  try {
    const res = await fetch(`${LM_STUDIO_URL}/v1/models`);
    const data = await res.json();
    return c.json(data);
  } catch (err) {
    return c.json({ error: '无法连接 LM Studio', detail: String(err) }, 503);
  }
});

apiApp.post('/api/compare', async (c) => {
  const { modelA, modelB, prompt, messages, systemPrompt, temperature, maxTokens } = await c.req.json().catch(() => ({}));

  if (!modelA || !modelB || (!prompt && !messages)) {
    return c.json({ error: '需要提供 modelA, modelB, 和 prompt/messages' }, 400);
  }

  const chatBody = {
    model: '',
    messages: messages || [
      ...(systemPrompt ? [{ role: 'system', content: systemPrompt }] : []),
      { role: 'user', content: prompt },
    ],
    temperature: temperature ?? 0.7,
    max_tokens: maxTokens ?? 4096,
    stream: true,
  };

  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();
      const send = (data: any) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
      };
      const done = () => {
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      };

      const [promiseA, promiseB] = await Promise.allSettled([
        fetchModelResponse(modelA, chatBody, send, 'A'),
        fetchModelResponse(modelB, chatBody, send, 'B'),
      ]);

      send({ type: 'complete', model: 'A', status: promiseA.status === 'fulfilled' ? 'ok' : 'error', error: promiseA.status === 'rejected' ? String(promiseA.reason) : undefined });
      send({ type: 'complete', model: 'B', status: promiseB.status === 'fulfilled' ? 'ok' : 'error', error: promiseB.status === 'rejected' ? String(promiseB.reason) : undefined });
      send({ type: 'done' });
      done();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
});

async function fetchModelResponse(model: string, body: any, send: (data: any) => void, label: 'A' | 'B') {
  try {
    const res = await fetch(`${LM_STUDIO_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, model }),
    });

    if (!res.ok) {
      send({ type: 'error', model: label, error: `HTTP ${res.status}: ${res.statusText}` });
      return;
    }

    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data: ')) continue;
        const jsonStr = trimmed.slice(6);
        if (jsonStr === '[DONE]') continue;

        try {
          const parsed = JSON.parse(jsonStr);
          const content = parsed.choices?.[0]?.delta?.content;
          if (content) {
            send({ type: 'chunk', model: label, content });
          }
        } catch {
          // ignore
        }
      }
    }
  } catch (err) {
    send({ type: 'error', model: label, error: String(err) });
  }
}

apiApp.post('/api/chat', async (c) => {
  const { model, messages, temperature, maxTokens } = await c.req.json().catch(() => ({}));

  if (!model || !messages?.length) {
    return c.json({ error: '需要提供 model 和 messages' }, 400);
  }

  const body = {
    model,
    messages,
    temperature: temperature ?? 0.7,
    max_tokens: maxTokens ?? 4096,
    stream: true,
  };

  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();
      const send = (data: any) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
      };
      const done = () => {
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      };

      try {
        const res = await fetch(`${LM_STUDIO_URL}/v1/chat/completions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          send({ type: 'error', error: `HTTP ${res.status}: ${res.statusText}` });
          send({ type: 'complete', status: 'error' });
          done();
          return;
        }

        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done: rd, value } = await reader.read();
          if (rd) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data: ')) continue;
            const jsonStr = trimmed.slice(6);
            if (jsonStr === '[DONE]') continue;

            try {
              const parsed = JSON.parse(jsonStr);
              const content = parsed.choices?.[0]?.delta?.content;
              if (content) {
                send({ type: 'chunk', content });
              }
            } catch {
              // ignore parse errors
            }
          }
        }

        send({ type: 'complete', status: 'ok' });
      } catch (err) {
        send({ type: 'error', error: String(err) });
        send({ type: 'complete', status: 'error' });
      }
      done();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
});

apiApp.get('/api/health', (c) => c.json({ status: 'ok', lmStudio: LM_STUDIO_URL }));
