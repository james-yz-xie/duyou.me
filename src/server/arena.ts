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
  origin: ['http://localhost:4321', 'http://127.0.0.1:4321', 'http://localhost:9876', 'http://127.0.0.1:9876'],
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

// --- Debate Summary Helper ---
// Call a lightweight model to summarize a debate response
async function summarizeResponse(text: string, model: string): Promise<string> {
  try {
    const res = await fetch(`${LM_STUDIO_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        messages: [
          { role: 'system', content: '你是一个摘要生成器。请用一句话（不超过60字）总结以下辩论发言的核心论点。只输出摘要内容，不要加任何前缀或格式标记。' },
          { role: 'user', content: text },
        ],
        temperature: 0.3,
        max_tokens: 128,
        stream: false,
      }),
    });

    if (!res.ok) return text.slice(0, 200);
    const data = await res.json() as any;
    const summary = data.choices?.[0]?.message?.content?.trim();
    return summary || text.slice(0, 200);
  } catch {
    return text.slice(0, 200);
  }
}

// --- Judge Helper ---
// Generate a verdict after debate rounds
async function judgeDebate(topic: string, history: { round: number; pro: string; con: string }[], model: string): Promise<{ winner: 'pro' | 'con' | 'draw'; reasoning: string }> {
  try {
    const formattedHistory = history.map(h =>
      `第${h.round}轮：\n正方：${h.pro}\n反方：${h.con}`
    ).join('\n\n');

    const res = await fetch(`${LM_STUDIO_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        messages: [
          {
            role: 'system',
            content: '你是一位公正的辩论裁判。请根据以下辩论记录，从论证逻辑、论据质量、反驳力度三个维度评判胜负。\n\n请严格按以下格式输出：\nWINNER: [pro/con/draw]\nREASON: [你的评判理由，100字以内]'
          },
          {
            role: 'user',
            content: `辩题：${topic}\n\n${formattedHistory}\n\n请给出裁判结果。`
          },
        ],
        temperature: 0.5,
        max_tokens: 512,
        stream: false,
      }),
    });

    if (!res.ok) return { winner: 'draw', reasoning: '裁判服务暂时不可用' };
    const data = await res.json() as any;
    const content = data.choices?.[0]?.message?.content || '';

    const winnerMatch = content.match(/WINNER:\s*(pro|con|draw)/i);
    const reasonMatch = content.match(/REASON:\s*(.+)/is);

    return {
      winner: (winnerMatch?.[1]?.toLowerCase() as 'pro' | 'con' | 'draw') || 'draw',
      reasoning: reasonMatch?.[1]?.trim() || content.slice(0, 200),
    };
  } catch {
    return { winner: 'draw', reasoning: '裁判服务暂时不可用' };
  }
}

apiApp.post('/api/compare', async (c) => {
  const { modelA, modelB, messagesA, messagesB, temperature, maxTokens } = await c.req.json().catch(() => ({}));

  if (!modelA || !modelB || (!messagesA && !messagesB)) {
    return c.json({ error: '需要提供 modelA, modelB, 和 messagesA/messagesB' }, 400);
  }

  const chatBody = {
    model: '',
    messages: [] as any[],
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
        fetchModelResponse(modelA, { ...chatBody, messages: messagesA || [] }, send, 'A'),
        fetchModelResponse(modelB, { ...chatBody, messages: messagesB || [] }, send, 'B'),
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

// --- Summarize endpoint ---
apiApp.post('/api/summarize', async (c) => {
  const { text, model } = await c.req.json().catch(() => ({}));
  if (!text || !model) {
    return c.json({ error: '需要提供 text 和 model' }, 400);
  }
  const summary = await summarizeResponse(text, model);
  return c.json({ summary });
});

// --- Judge endpoint ---
apiApp.post('/api/judge', async (c) => {
  const { topic, history, model } = await c.req.json().catch(() => ({}));
  if (!topic || !history || !model) {
    return c.json({ error: '需要提供 topic, history 和 model' }, 400);
  }
  const result = await judgeDebate(topic, history, model);
  return c.json(result);
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
