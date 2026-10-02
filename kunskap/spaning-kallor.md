# Spanarens källor

Tabellen läses av `kontroller/spana.py` (dashboarden kör den en gång i veckan utan modell). En rad per källa: `typ` är
rss, sida, github, hn eller awesome; `vikt` 0 stänger av raden; 1,5 är leverantörsdokumentation (den klass som gav
flest genomförda poster), 1,3 litteratur, 1,0 vanliga flöden, under 1 brusiga. `github`-rader skriver gh-sökningen
med flaggor (`--stars ">=200" --updated 90d`); `hn`-rader skriver Algolia-frågan. Nya YouTube-kanaler: kanal-id ur
`.venv/bin/yt-dlp --dump-single-json --flat-playlist --playlist-items 1 'https://www.youtube.com/@Namn'`.

| typ | namn | url eller fråga | varför | vikt |
|---|---|---|---|---|
| rss | Claude Code releases | https://github.com/anthropics/claude-code/releases.atom | hooks, skills, verktyg | 1.5 |
| sida | Claude platform release notes | https://platform.claude.com/docs/en/release-notes/overview | modeller, prompting | 1.5 |
| sida | Claude Code best practices | https://code.claude.com/docs/en/best-practices | gav två poster i oktober | 1.5 |
| sida | Prompting Claude | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview | frontend-standardval, effort | 1.5 |
| sida | OpenAI frontend prompt guide | https://developers.openai.com/api/docs/guides/frontend-prompt | gav en post | 1.5 |
| rss | OpenAI news | https://openai.com/news/rss.xml | bred, termfiltret sållar | 1.2 |
| rss | Astro releases | https://github.com/withastro/astro/releases.atom | vår stack | 1.5 |
| rss | Astro blog | https://astro.build/rss.xml | | 1.3 |
| rss | Lighthouse releases | https://github.com/GoogleChrome/lighthouse/releases.atom | provets grind | 1.5 |
| rss | web.dev | https://web.dev/feed.xml | Core Web Vitals | 1.5 |
| rss | Chrome for Developers | https://developer.chrome.com/static/blog/feed.xml | | 1.5 |
| rss | Google Search Central | https://feeds.feedburner.com/blogspot/amDG | lokal SEO | 1.5 |
| rss | NN/g | https://www.nngroup.com/feed/rss/ | måttstocken | 1.3 |
| rss | Smashing Magazine | https://www.smashingmagazine.com/feed/ | | 1.3 |
| rss | A List Apart | https://alistapart.com/main/feed/ | | 1.3 |
| rss | Adrian Roselli | https://adrianroselli.com/feed | tillgänglighet | 1.3 |
| rss | Piccalilli | https://piccalil.li/feed.xml | CSS, progressive enhancement | 1.2 |
| rss | Sara Soueidan | https://www.sarasoueidan.com/blog/index.xml | | 1.2 |
| rss | CSS-Tricks | https://css-tricks.com/feed/ | | 1.1 |
| rss | HTMHell | https://www.htmhell.dev/feed.xml | semantik | 1.1 |
| rss | SpeedCurve | https://www.speedcurve.com/blog/rss/ | prestanda | 1.3 |
| sida | Baymard blog | https://baymard.com/blog | formulär, konvertering | 1.3 |
| rss | YouTube: Chrome for Developers | https://www.youtube.com/feeds/videos.xml?channel_id=UCnUYZLuoy1rq1aVMwx4aTzw | | 1.0 |
| rss | YouTube: Kevin Powell | https://www.youtube.com/feeds/videos.xml?channel_id=UCJZv4d5rbIKd4QHMPkcABCw | CSS | 1.0 |
| rss | YouTube: Anthropic | https://www.youtube.com/feeds/videos.xml?channel_id=UCrDwWp7EBBv4NwvScIpBDOA | | 1.1 |
| rss | YouTube: DesignCourse | https://www.youtube.com/feeds/videos.xml?channel_id=UCVyRiMvfUNMA1UPlDPzG5Ow | UI | 0.9 |
| rss | YouTube: Web Dev Simplified | https://www.youtube.com/feeds/videos.xml?channel_id=UCFbNIlppjAuEX4znoulh0Cw | | 0.9 |
| rss | YouTube: Theo | https://www.youtube.com/feeds/videos.xml?channel_id=UCbRP3c757lWg9M-U7TyEkXA | åsikter, brus | 0.8 |
| github | Claude Code-skills | claude code skills --stars ">=200" --updated 90d | | 1.2 |
| github | Agent-skills webbdesign | agent skills web design --stars ">=100" --updated 90d | | 1.2 |
| github | Astro-teman | astro theme business --language Astro --stars ">=50" | | 1.0 |
| github | Lighthouse och axe | lighthouse accessibility audit --stars ">=200" --updated 90d | | 1.0 |
| github | Nytt och växande | website frontend "web design" --created 180d --stars ">=200" --sort stars | | 1.0 |
| hn | HN: Core Web Vitals och Lighthouse | "core web vitals" OR lighthouse | | 1.1 |
| hn | HN: tillgänglighet | accessibility WCAG | | 1.1 |
| hn | HN: Claude Code | "claude code" | | 1.1 |
| hn | HN: småföretagssajt | "small business" website | | 1.1 |
| awesome | awesome-claude-code | https://github.com/hesreallyhim/awesome-claude-code | bara nya länkar räknas | 1.0 |
| awesome | awesome-design-md | https://github.com/VoltAgent/awesome-design-md | dömd nej som källa; här en pekare | 1.0 |
