#!/usr/bin/env node
// Jarvis family-chat bridge.
// A tiny LAN-only HTTP service that turns a family chat message into a reply
// from Claude Code (Rob's subscription, already logged in on this LXC), so the
// Mission Control site can offer real conversation without a separate API key.
//
// It runs `claude -p` headless with NO tools and a neutral cwd, so it's a pure
// text generator — the family (incl. the kids) can't reach the filesystem or
// any tool through it. Auth to the bridge itself is a shared token.
//
// POST /chat  { name, role, context, message }  ->  { reply }
// Env: JARVIS_BRIDGE_TOKEN (required), JARVIS_BRIDGE_MODEL, PORT (default 3040)

import http from 'node:http'
import { execFile } from 'node:child_process'

const TOKEN = process.env.JARVIS_BRIDGE_TOKEN
const MODEL = process.env.JARVIS_BRIDGE_MODEL || 'claude-sonnet-5'
const PORT = parseInt(process.env.PORT || '3040', 10)
const CLAUDE = process.env.CLAUDE_BIN || '/home/jarvis/.local/bin/claude'
if (!TOKEN) { console.error('JARVIS_BRIDGE_TOKEN not set'); process.exit(1) }

function systemPrompt({ name, role, context }) {
  return [
    "You are Jarvis, the Stokes family's friendly home assistant, chatting inside the family's Mission Control web app.",
    `You are talking to ${name || 'someone in the family'} (${role || 'family member'}).`,
    'Be warm, brief, and genuinely helpful. Plain, everyday language. A little humour is welcome. No corporate tone.',
    'Answer ONLY from the family context below and general knowledge. Do not invent specific family facts (times, chores, money, plans) that are not in the context — if you do not know, say so.',
    role === 'child'
      ? 'This is one of the kids. You can answer questions and help plan. If they ask to do or buy something that needs a grown-up\'s yes (spending money, screen time, going out, having friends over), tell them warmly that you\'ll pass it to Mum or Dad — do not promise it yourself.'
      : 'This is a parent. You can help them plan and answer freely.',
    'Never discuss anything beyond family life, the home, and this app. Keep replies to a few sentences unless asked for more.',
    '',
    "Today's family context:",
    context || '(no extra context available)',
  ].join('\n')
}

function runClaude(message, sys) {
  return new Promise((resolve, reject) => {
    execFile(
      CLAUDE,
      ['-p', message, '--system-prompt', sys, '--allowedTools', '', '--model', MODEL],
      { cwd: '/tmp', timeout: 90_000, maxBuffer: 1024 * 1024, env: process.env },
      (err, stdout, stderr) => {
        if (err) return reject(new Error(stderr?.toString().slice(0, 300) || err.message))
        resolve(stdout.toString().trim())
      }
    )
  })
}

const server = http.createServer((req, res) => {
  const send = (code, obj) => { res.writeHead(code, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(obj)) }
  if (req.method === 'GET' && req.url === '/health') return send(200, { ok: true, model: MODEL })
  if (req.method !== 'POST' || req.url !== '/chat') return send(404, { error: 'not found' })
  if (req.headers['x-bridge-token'] !== TOKEN) return send(401, { error: 'unauthorized' })

  let body = ''
  req.on('data', (c) => { body += c; if (body.length > 20_000) req.destroy() })
  req.on('end', async () => {
    let data
    try { data = JSON.parse(body) } catch { return send(400, { error: 'bad json' }) }
    const message = (data.message || '').toString().slice(0, 2000).trim()
    if (!message) return send(400, { error: 'message required' })
    try {
      const reply = await runClaude(message, systemPrompt(data))
      send(200, { reply })
    } catch (e) {
      send(502, { error: 'jarvis unavailable', detail: e.message })
    }
  })
})

server.listen(PORT, '0.0.0.0', () => console.log(`jarvis chat bridge on :${PORT} (model ${MODEL})`))
