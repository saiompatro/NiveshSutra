<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes -- APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# Frontend Agent Rules

- The frontend is a Next.js app that talks to a local FastAPI backend.
- API base URL is configured via the `NEXT_PUBLIC_API_BASE_URL` environment variable (default: `http://localhost:8000`).
- No authentication layer -- the backend serves a single local user.
- No Supabase client -- all data comes from FastAPI endpoints.
