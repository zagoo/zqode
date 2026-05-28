// Placeholder — will be overwritten by `npm run openapi:gen`.
// Currently re-exports the bootstrap http helper to satisfy the
// CLAUDE.md "no raw fetch in modules" rule from module-level code.
export { http as client } from '@/api/http';
