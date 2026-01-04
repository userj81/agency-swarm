# Agency Swarm - Web UI Implementation

**Autor:** Claude Code (Anthropic)
**Data:** 4 de Janeiro de 2026
**Versão:** 1.0.0
**Repositório:** https://github.com/userj81/agency-swarm

---

## Resumo Executivo

Foi implementada uma **interface web completa** para o Agency Swarm, portando **todas as funcionalidades** da interface terminal para uma aplicação web moderna usando Next.js, React, TypeScript e FastAPI.

### Commits Realizados

| Commit | Hash | Descrição |
|--------|------|-----------|
| 1 | `c1ec503` | Add complete web UI for Agency Swarm |
| 2 | `7910595` | Add missing config files for Next.js |

---

## O Que Foi Implementado

### 1. Frontend (Next.js + React + TypeScript)

#### Estrutura de Arquivos

```
src/agency_swarm/ui/demos/web/
├── app/                           # Next.js App Router
│   ├── layout.tsx                 # Root layout com tema dark
│   ├── page.tsx                   # Página principal do chat
│   ├── globals.css                # Estilos globais + Tailwind
│   └── api/                       # API Routes (proxy para Python)
│       ├── chat/route.ts          # POST /api/chat (SSE streaming)
│       ├── command/route.ts       # POST /api/command
│       ├── agents/route.ts        # GET /api/agents
│       └── chats/
│           ├── route.ts           # GET/POST /api/chats
│           └── [chatId]/route.ts  # GET/POST/DELETE /api/chats/{id}
│
├── components/                    # Componentes React
│   ├── ChatContainer.tsx          # Display de mensagens com Markdown
│   ├── InputArea.tsx              # Input de chat com auto-resize
│   ├── Sidebar.tsx                # Histórico de chats
│   ├── CommandMenu.tsx            # Paleta de comandos (Ctrl+K)
│   ├── UsagePanel.tsx             # Painel de custos/tokens
│   └── AgentSelector.tsx          # Dropdown de seleção de agentes
│
├── hooks/                         # Custom React Hooks
│   ├── useChat.ts                 # Estado do chat + streaming SSE
│   └── useChats.ts                # Lista de chats + persistência
│
├── types/index.ts                 # Definições TypeScript
├── utils/format.ts                # Utilitários de formatação
│
├── package.json                   # Dependências Node.js
├── tsconfig.json                  # Config TypeScript
├── next.config.ts                 # Config Next.js
├── tailwind.config.ts             # Config Tailwind CSS
├── postcss.config.mjs             # Config PostCSS
├── .gitignore                     # Arquivos ignorados
├── .env.example                   # Variáveis de ambiente exemplo
└── README.md                      # Documentação
```

#### Funcionalidades do Frontend

| Funcionalidade | Descrição |
|----------------|-----------|
| **Streaming em tempo real** | Server-Sent Events (SSE) para respostas streaming |
| **Markdown rendering** | Suporte completo a Markdown com syntax highlighting |
| **Multi-agentes** | Seleção de agentes + menção @agent |
| **Comandos slash** | `/help`, `/new`, `/compact`, `/resume`, `/status`, `/cost` |
| **Persistência** | Histórico de chats com metadados |
| **Usage tracking** | Painel com custos e estatísticas de tokens |
| **Teclas de atalho** | `Ctrl+K` comandos, `Ctrl+/` focus input, `ESC` cancelar |
| **Design responsivo** | Funciona em desktop e mobile |
| **Dark theme** | Tema escuro moderno com Tailwind CSS |

---

### 2. Backend (FastAPI + Python)

#### Estrutura de Arquivos

```
src/agency_swarm/ui/demos/web/backend/
├── main.py                        # Servidor FastAPI
└── requirements.txt               # Dependências Python
```

#### Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/agents` | Lista todos os agentes |
| POST | `/chat` | Envia mensagem e retorna stream SSE |
| POST | `/command` | Executa comandos slash |
| GET | `/chats` | Lista todos os chats salvos |
| POST | `/chats/new` | Cria novo chat |
| GET | `/chats/{id}` | Retorna detalhes do chat |
| POST | `/chats/{id}/resume` | Retoma um chat específico |
| DELETE | `/chats/{id}` | Deleta um chat |

#### Funcionalidades do Backend

- Integração completa com Agency Swarm
- Streaming de eventos via Server-Sent Events
- Gerenciamento de sessões de chat
- Execução de comandos slash
- Tracking de usage e custos
- Persistência de chats em JSON

---

## Mapeamento: Terminal → Web

| Terminal | Web UI | Status |
|----------|--------|--------|
| Chat interativo | Chat com streaming SSE | ✅ |
| `@agent` menção | Agent selector + @ syntax | ✅ |
| `/help` | Command menu + /help | ✅ |
| `/new` | Botão "New Chat" + /new | ✅ |
| `/compact` | /compact command | ✅ |
| `/resume` | Sidebar + /resume | ✅ |
| `/status` | /status command | ✅ |
| `/cost` | Usage panel + /cost | ✅ |
| `/exit` | Fechar aba/janela | ✅ |
| Hot reload | Next.js dev mode | ✅ |
| Autocompletar | Command palette | ✅ |
| Cancelamento (ESC) | Botão ESC | ✅ |
| Reasoning toggle | Renderizado no chat | ✅ |
| Usage display | Painel de custos | ✅ |
| Persistência JSON | API de persistência | ✅ |
| Rich terminal | UI moderna React | ✅ |

---

## Como Usar

### Pré-requisitos

- **Node.js** 18+ (frontend)
- **Python** 3.12+ (backend)
- **npm** ou **yarn** (frontend)
- **pip** (backend)

### Instalação

#### 1. Clonar o Repositório

```bash
git clone https://github.com/userj81/agency-swarm.git
cd agency-swarm
```

#### 2. Instalar Frontend

```bash
cd src/agency_swarm/ui/demos/web
npm install
```

#### 3. Instalar Backend

```bash
cd backend
pip install -r requirements.txt
```

#### 4. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env.local

# Editar se necessário
# PYTHON_BACKEND_URL=http://localhost:8000
```

### Executar

#### Terminal 1 - Backend Python

```bash
cd src/agency_swarm/ui/demos/web/backend
python main.py
```

O backend estará rodando em `http://localhost:8000`

#### Terminal 2 - Frontend Next.js

```bash
cd src/agency_swarm/ui/demos/web
npm run dev
```

A UI estará disponível em `http://localhost:3000`

### Configurar Sua Agency

Edite `backend/main.py` na função `create_agency()`:

```python
def create_agency() -> Agency:
    # Configure seus agentes aqui
    ceo = Agent(
        name="CEO",
        description="Agency coordinator",
        instructions="...",
        model="gpt-4o-mini",
    )

    developer = Agent(
        name="Developer",
        description="Code specialist",
        instructions="...",
        model="gpt-4o-mini",
    )

    return Agency(
        agents=[ceo, developer],
        default_agent=ceo,
    )
```

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                         │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Chat UI     │  │ Sidebar     │  │ Commands    │        │
│  │ Components  │  │ Components  │  │ Components  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         ↓                  ↓                  ↓             │
│  ┌───────────────────────────────────────────────────┐    │
│  │              API Routes (Next.js)                  │    │
│  │  /api/chat, /api/chats, /api/agents, /api/command  │    │
│  └───────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP/SSE
┌─────────────────────────────────────────────────────────────┐
│                    Python Backend (FastAPI)                  │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Agency Swarm Integration                │   │
│  │  - Multi-agent orchestration                        │   │
│  │  - Streaming responses                              │   │
│  │  - Chat persistence                                 │   │
│  │  - Usage tracking                                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Dependências

### Frontend (package.json)

```json
{
  "dependencies": {
    "next": "^15.1.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "marked": "^15.0.0",
    "dompurify": "^3.2.0"
  },
  "devDependencies": {
    "tailwindcss": "^4.0.0",
    "typescript": "^5.7.0"
  }
}
```

### Backend (requirements.txt)

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.0.0
```

---

## Teclas de Atalho

| Tecla | Ação |
|-------|------|
| `Ctrl+K` | Abrir menu de comandos |
| `Ctrl+/` | Focar no input de chat |
| `Enter` | Enviar mensagem |
| `Shift+Enter` | Nova linha no input |
| `ESC` | Cancelar streaming / Fechar modais |

---

## Estrutura de Dados

### Mensagem (Message)

```typescript
type Message = TextMessage | ReasoningMessage | FunctionCallMessage | FunctionOutputMessage;

interface TextMessage {
  type: "message";
  role: "system" | "user" | "assistant";
  content: string;
  agent?: string;
  callerAgent?: string;
}

interface ReasoningMessage {
  type: "reasoning";
  summary?: Array<{ text: string }>;
}

interface FunctionCallMessage {
  type: "function";
  name: string;
  arguments: string;
  call_id?: string;
  agent?: string;
}

interface FunctionOutputMessage {
  type: "function_output";
  output: string;
  call_id?: string;
}
```

### UsageStats

```typescript
interface UsageStats {
  request_count: number;
  cached_tokens: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  total_cost: number;
  reasoning_tokens?: number;
  audio_tokens?: number;
}
```

### ChatMetadata

```typescript
interface ChatMetadata {
  chat_id: string;
  created_at: string;
  modified_at: string;
  msgs: number;
  branch: string;
  summary: string;
  usage?: UsageStats;
}
```

---

## Fluxo de Dados (Streaming)

```
1. Usuário digita mensagem
   ↓
2. Frontend chama POST /api/chat
   ↓
3. Next.js faz proxy para Python backend
   ↓
4. Agency Swarm processa mensagem
   ↓
5. Python retorna stream SSE
   ↓
6. Next.js repassa stream para frontend
   ↓
7. Hook useChat processa eventos
   ↓
8. ChatContainer atualiza UI em tempo real
```

### Eventos SSE

```typescript
// Text delta
{ "type": "text", "agent": "CEO", "delta": "Hello", "recipient": "user" }

// Reasoning delta
{ "type": "reasoning", "agent": "CEO", "delta": "Thinking..." }

// Function call
{ "type": "function", "agent": "Developer", "name": "write_file", "arguments": "{...}" }

// Function output
{ "type": "function_output", "output": "File written successfully" }

// Usage
{ "type": "usage", "data": { "total_tokens": 1234, "total_cost": 0.0234 } }

// Done
"data: [DONE]"
```

---

## Customização

### Tema

Edite `app/globals.css` para customizar cores:

```css
/* Exemplo: mudar cor primária */
.bg-indigo-600 {
  background-color: #seu-cor;
}
```

### Adicionar Comandos

1. Adicione em `types/index.ts`:
```typescript
export type SlashCommand =
  | "help"
  | "new"
  | "seu-comando";  // ← Adicione aqui
```

2. Adicione em `components/CommandMenu.tsx`:
```typescript
const COMMANDS: CommandDefinition[] = [
  // ...
  {
    name: "seu-comando",
    description: "Descrição do comando",
    usage: "/seu-comando [args]",
  },
];
```

3. Adicione handler em `backend/main.py`:
```python
case "seu-comando":
    # Sua lógica aqui
    return {"result": "ok"}
```

### Adicionar Componentes

Siga o padrão dos componentes existentes em `components/`:

```tsx
// components/SeuComponente.tsx
"use client";

import { type SeuComponenteProps } from "@/types";

export default function SeuComponente({ prop1, prop2 }: SeuComponenteProps) {
  return (
    <div className="...">
      {/* Seu JSX */}
    </div>
  );
}
```

---

## Troubleshooting

### CORS errors

**Problema:** Frontend não consegue se comunicar com backend

**Solução:**
- Verifique se o backend está rodando na porta correta (8000)
- Confirme `PYTHON_BACKEND_URL` em `.env.local`
- Verifique middleware CORS em `backend/main.py`

### Streaming não funciona

**Problema:** Mensagens não aparecem em tempo real

**Solução:**
- Abra o console do navegador para ver erros
- Verifique se backend retorna headers `text/event-stream`
- Tente desabilitar extensões do navegador

### Chat não salva

**Problema:** Chats não aparecem na sidebar

**Solução:**
- Verifique permissões de escrita no diretório
- Confirme que `AGENCY_SWARM_CHATS_DIR` é válido
- Cheque logs do backend para erros

---

## Deployment

### Frontend (Vercel)

```bash
cd src/agency_swarm/ui/demos/web
npm run build
vercel deploy
```

### Backend (Render, Railway, etc.)

1. Deploy do backend FastAPI
2. Configure `PYTHON_BACKEND_URL` no frontend
3. Configure CORS para o domínio do frontend

---

## Próximos Passos

Sugestões para evolução da UI:

- [ ] Autenticação de usuários
- [ ] Multi-tenancy (usuários isolados)
- [ ] Upload/download de arquivos
- [ ] Export de conversas (PDF, Markdown)
- [ ] Integração com outros provedores (Claude, Gemini)
- [ ] Modo de edição visual de agentes
- [ ] Testes E2E com Playwright
- [ ] Docker Compose para deploy fácil
- [ ] Websocket como alternativa ao SSE
- [ ] PWA para uso offline

---

## Links Úteis

- **Repositório:** https://github.com/userj81/agency-swarm
- **Agency Swarm:** https://github.com/userj81/agency-swarm
- **Next.js:** https://nextjs.org
- **FastAPI:** https://fastapi.tiangolo.com
- **Tailwind CSS:** https://tailwindcss.com

---

## Licença

MIT - Mesma licença do Agency Swarm

---

**Gerado por Claude Code (Anthropic)**
*Data: 4 de Janeiro de 2026*
