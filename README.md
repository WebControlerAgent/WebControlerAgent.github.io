# Web Controller Agent

Central GitHub Pages dashboard and GitHub Actions controller.

## Current foundation
- Mobile-friendly dashboard
- Hourly GitHub Actions trigger
- Manual workflow trigger
- Configuration file
- Server-side secret boundary
- Ready for authorized repository adapters and verification jobs

## Important
Only process and publish content for which you have the necessary rights/authorization. Do not put GitHub tokens in frontend JavaScript.

## Next implementation
1. Add authorized source adapters.
2. Add repository mappings and GitHub App/PAT secrets through repository Actions secrets.
3. Add deterministic upload/verification workers.
4. Connect the dashboard to read-only status artifacts or an authenticated backend.
