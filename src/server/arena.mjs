import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { serve } from '@hono/node-server';

const app = new Hono();

app.use('/*', cors({
  origin: ['http://localhost:4321', 'http://127.0.0.1:4321'],
  allowHeaders: ['Content-Type', 'Accept'],
  allowMethods: ['GET', 'POST', 'OPTIONS'],
  exposeHeaders: ['Content-Type'],
}));

const LM_STUDIO_URL = process.env.LM_STUDIO_URL || 'http://localhost:1234';

// GET /api/models
app.get('/api/models', async (c) => {
  try {
    const res = await fetch(`${LM_STUDIO_URL}/v1/models`);
    const data = await res.json();
    return c.json(data);
  } catch (err) {
    return c.json({ error: '无法连接 LM Studio', detail: String(err) }, 503);
  }
});

// POST /api/compare — 并行请求两个模型，SSE 流式返回
app.post('/api/compare', async (c) => {
  const { modelA, modelB, prompt, messages, messagesA, messagesB, systemPrompt, temperature, maxTokens } = await c.req.json().catch(() => ({}));

  if (!modelA || !modelB || (!prompt && !messages && !messagesA && !messagesB)) {
    return c.json({ error: '需要提供 modelA, modelB, 和 prompt/messages' }, 400);
  }

  const defaultMessages = messages || [
    ...(systemPrompt ? [{ role: 'system', content: systemPrompt }] : []),
    { role: 'user', content: prompt },
  ];

  const chatBodyA = {
    model: '',
    messages: messagesA || defaultMessages,
    temperature: temperature ?? 0.7,
    max_tokens: maxTokens ?? 4096,
    stream: true,
  };

  const chatBodyB = {
    model: '',
    messages: messagesB || defaultMessages,
    temperature: temperature ?? 0.7,
    max_tokens: maxTokens ?? 4096,
    stream: true,
  };

  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();
      const send = (data) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
      };
      const done = () => {
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      };

      const [promiseA, promiseB] = await Promise.allSettled([
        fetchModelResponse(modelA, chatBodyA, send, 'A'),
        fetchModelResponse(modelB, chatBodyB, send, 'B'),
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

// POST /api/chat — 单模型聊天，SSE 流式返回
app.post('/api/chat', async (c) => {
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
      const send = (data) => {
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

        const reader = res.body.getReader();
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

// Health check
app.get('/api/health', (c) => c.json({ status: 'ok', lmStudio: LM_STUDIO_URL }));

async function fetchModelResponse(model, body, send, label) {
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

    const reader = res.body.getReader();
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

// Start server
const PORT = parseInt(process.env.PORT || '3456');
serve({ fetch: app.fetch, port: PORT }, (info) => {
  console.log(`\n🥊 AI 擂台赛 API 已启动`);
  console.log(`   访问: http://localhost:${PORT}/api/health`);
  console.log(`   LM Studio: ${LM_STUDIO_URL}\n`);
});
