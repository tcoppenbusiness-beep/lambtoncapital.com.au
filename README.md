# Lambton Capital website

Static site in `public/`, deployed to Cloudflare from `main` (config in `wrangler.jsonc`). No build step.

- Workers flow: build command blank, deploy command `npx wrangler deploy`
- Pages flow: build command blank, output directory `public`
