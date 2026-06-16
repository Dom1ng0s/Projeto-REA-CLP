# Nexos REA

Aplicação web para descoberta e curadoria de Recursos Educacionais Abertos (REA).

## Stack

- **TanStack Start** (React 19) com SSR
- **Vite 7** + **TypeScript**
- **Tailwind CSS** + **shadcn/ui**
- **Supabase** (banco Postgres, Auth e API)

## Pré-requisitos

- **Node.js 20+** e npm

## Configuração

1. Clone o repositório e instale as dependências:

   ```bash
   git clone https://github.com/ErickMascarenhas/nexos-rea.git
   cd nexos-rea
   npm install
   ```

2. Crie o arquivo de variáveis de ambiente a partir do exemplo:

   ```bash
   cp .env.example .env      # Windows (cmd): copy .env.example .env
   ```

3. Preencha o `.env` com os valores do seu projeto Supabase. Pegue em **Dashboard → Project Settings → API**:

   | Variável | Onde encontrar |
   | --- | --- |
   | `VITE_SUPABASE_URL` / `SUPABASE_URL` | Project URL (apenas o domínio base, ex.: `https://SEU-REF.supabase.co`) |
   | `VITE_SUPABASE_PUBLISHABLE_KEY` / `SUPABASE_PUBLISHABLE_KEY` | **Publishable key** (`sb_publishable_...`) — pública, usada no cliente |
   | `SUPABASE_SERVICE_ROLE_KEY` | **Secret key** (`sb_secret_...`) — secreta, só no servidor; ignora RLS |
   | `SUPABASE_DB_PASSWORD` | Senha do banco (usada só pelo Supabase CLI) |

   > O `.env` **não** é versionado (está no `.gitignore`). Guarde os valores em local seguro para reutilizar em outra máquina.

## Rodando localmente

```bash
npm run dev
```

A aplicação sobe em modo de desenvolvimento (com SSR). Abra a URL que o Vite imprimir no terminal (geralmente `http://localhost:3000`).
