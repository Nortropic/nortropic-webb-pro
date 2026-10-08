# Spanarens källor

Tabellen läses av `kontroller/spana.py`; dashboarden kör den en gång per dygn under piloten (`NWP_SPANING_INTERVALL_DAGAR`,
7 efter piloten), utan modell. En rad per källa: `typ` är rss, sida, github, hn eller awesome; `vikt` 0 stänger av raden;
1,5 är primärkällor (leverantörsdokumentation, standarder, verktyg vi använder: den klass som gav flest genomförda
poster), 1,2–1,3 facklitteratur, 1,0 vanliga flöden, under 1 brusiga. `område` är var i vårt flöde fynden hör hemma.
`github`-rader skriver gh-sökningen med flaggor (`--stars ">=200" --updated 90d`); `hn`-rader skriver Algolia-frågan.
`sida` bevakar en sida eller en fil: första körningen sätter baslinjen, sedan blir de tillagda meningarna kandidaten.
Nya YouTube-kanaler: kanal-id ur `.venv/bin/yt-dlp --skip-download --print "%(channel_id)s" <en video>`.

Källorna prövades 2026-10-03 (flöden med poster, sidor med status 200). Underlaget för urvalet: kirurgens 69 första
intag gav 10 "ta in" och 54 "nej"; 39 av 49 GitHub-repon blev nej, och 17 nej-domar gav ändå en ändring ur en enda idé.
Spaningen letar därför efter metoder och ändringar inom våra områden, inte efter populära repon.

| typ | namn | url eller fråga | varför | vikt | område |
|---|---|---|---|---|---|
| rss | Claude Code releases | https://github.com/anthropics/claude-code/releases.atom | hooks, skills, headless, verktyg | 1.5 | agentflödet |
| sida | Claude platform release notes | https://platform.claude.com/docs/en/release-notes/overview | modeller, prompting | 1.5 | modeller och guider |
| sida | Claude Code best practices | https://code.claude.com/docs/en/best-practices | gav två poster i oktober | 1.5 | agentflödet |
| sida | Prompting Claude | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview | frontend-standardval, effort | 1.5 | modeller och guider |
| sida | Agent SDK | https://code.claude.com/docs/en/agent-sdk/overview | granskare och ateljé i egna sessioner | 1.3 | agentflödet |
| sida | Anthropic news | https://www.anthropic.com/news | modeller, produkter, guider och e-böcker | 1.5 | modeller och guider |
| sida | Anthropic engineering | https://www.anthropic.com/engineering | agenter, skills, evals i praktiken | 1.5 | agentflödet |
| sida | Claude-bloggen | https://claude.com/blog | guider för agenter och arbetsflöden | 1.3 | modeller och guider |
| sida | Claude Academy: Build with Claude | https://academy.claude.com/collections/build-with-claude | nya kurser om API, MCP, skills, verktyg | 1.3 | modeller och guider |
| sida | Claude Academy | https://academy.claude.com/ | kurser och guider (Claude Code, AI Fluency) | 1.0 | modeller och guider |
| rss | Claude cookbooks | https://github.com/anthropics/claude-cookbooks/commits/main.atom | mönster för verktyg, evals, agenter | 1.0 | agentflödet |
| sida | OpenAI frontend prompt guide | https://developers.openai.com/api/docs/guides/frontend-prompt | gav en post | 1.5 | ai-webbdesign |
| sida | OpenAI API changelog | https://developers.openai.com/api/docs/changelog | jämförelse: vad andra leverantörer inför | 1.0 | modeller och guider |
| sida | OpenAI cookbook | https://developers.openai.com/cookbook | evals, agenter | 0.9 | granskning |
| sida | OpenAI Academy | https://academy.openai.com/ | guider | 0.8 | modeller och guider |
| rss | OpenAI news | https://openai.com/news/rss.xml | bred, termfiltret sållar | 1.0 | modeller och guider |
| rss | Latent Space | https://www.latent.space/feed | AI-ingenjörskap, AINews | 0.8 | modeller och guider |
| sida | xAI release notes | https://docs.x.ai/developers/release-notes | Grok: modeller och verktyg | 0.7 | modeller och guider |
| sida | Gemini API release notes | https://ai.google.dev/gemini-api/docs/changelog | Google: modeller och verktyg | 0.7 | modeller och guider |
| sida | Anthropic frontend-design | https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md | vår kopia i kunskap/externa; ändringar i originalet | 1.5 | ai-webbdesign |
| rss | Anthropic skills | https://github.com/anthropics/skills/commits/main.atom | nya och ändrade skills | 1.3 | ai-webbdesign |
| rss | Taste-skill | https://github.com/Leonxlnx/taste-skill/commits/main.atom | vår kopia i kunskap/externa | 1.2 | ai-webbdesign |
| rss | Emil Kowalskis skills | https://github.com/emilkowalski/skills/commits/main.atom | design-eng, mobile-native | 1.2 | ai-webbdesign |
| rss | Jakub Krehels skills | https://github.com/jakubkrehel/skills/commits/main.atom | better-* i verktygslådan | 1.2 | ai-webbdesign |
| rss | Impeccable | https://github.com/pbakaus/impeccable/commits/main.atom | mönstren i stilrapporten | 1.2 | ai-webbdesign |
| rss | Vercel web interface guidelines | https://github.com/vercel-labs/web-interface-guidelines/commits/main.atom | vår kopia i kunskap/externa | 1.2 | ai-webbdesign |
| rss | Addy Osmanis web-quality-skills | https://github.com/addyosmani/web-quality-skills/commits/main.atom | vår kopia i kunskap/externa | 1.2 | ai-webbdesign |
| hn | HN: AI-webbdesign | "claude design" OR "ai website builder" OR "frontend design" | metoder och verktyg för AI-byggda sajter | 1.0 | ai-webbdesign |
| github | Agent-skills webbdesign | agent skills web design --stars ">=100" --updated 90d | | 1.0 | ai-webbdesign |
| github | Frontend design-skills | frontend design skill --stars ">=50" --updated 90d | | 1.0 | ai-webbdesign |
| rss | YouTube: AI LABS | https://www.youtube.com/feeds/videos.xml?channel_id=UCelfWQr9sXVMTvBzviPGlFw | ägaren matar kirurgen härifrån; två ta in, en prova | 1.0 | ai-webbdesign |
| rss | YouTube: Jack Roberts | https://www.youtube.com/feeds/videos.xml?channel_id=UCxVxcTULO9cFU6SB9qVaisQ | Claude Design | 0.9 | ai-webbdesign |
| rss | YouTube: RoboNuggets | https://www.youtube.com/feeds/videos.xml?channel_id=UCgscS8mBsQZ5sFRkJIFWD7Q | Claude Design | 0.9 | ai-webbdesign |
| rss | YouTube: Self-Made Web Designer | https://www.youtube.com/feeds/videos.xml?channel_id=UCDQ3BtYh76shNPjnqlQjxpg | webbdesignprocess | 0.9 | ai-webbdesign |
| rss | YouTube: DesignCode | https://www.youtube.com/feeds/videos.xml?channel_id=UCTIhfOopxukTIRkbXJ3kN-g | webbdesign med Claude | 0.9 | ai-webbdesign |
| rss | YouTube: Jono Catliff | https://www.youtube.com/feeds/videos.xml?channel_id=UCnzxPyNnn8jk4bHFk3JUBhA | webbdesign med Claude Code | 0.9 | ai-webbdesign |
| rss | YouTube: Create a Pro Website | https://www.youtube.com/feeds/videos.xml?channel_id=UCZw_mKFPJMpvIWKWWwWpuVA | webbdesign med Claude Code | 0.9 | ai-webbdesign |
| rss | YouTube: Mikey No Code | https://www.youtube.com/feeds/videos.xml?channel_id=UCde0vB0fTwC8AT3sJofFV0w | bygga och publicera | 0.8 | ai-webbdesign |
| rss | Reddit: AI-webbdesign | https://www.reddit.com/r/ClaudeAI+ClaudeCode+vibecoding+ai_website_builder+ChatGPTCoding/top/.rss?t=week | veckans mest lästa trådar; Reddit tål ett anrop per ~20 s utan inloggning, så raderna står långt isär (påslaget 2026-10-08: spana.py håller minst 20 s mellan anrop till reddit.com, kirurgen läser trådar med kontroller/reddit_trad.py) | 0.9 | ai-webbdesign |
| rss | Design with AI | https://designwithai.substack.com/feed | designers som arbetar med Claude Code | 1.0 | ai-webbdesign |
| rss | AI First Designer (ADPList) | https://adplist.substack.com/feed | designarbete med AI | 0.9 | ai-webbdesign |
| rss | Lovable-bloggen | https://lovable.dev/blog/rss.xml | AI-sajtbyggare: vad de inför | 0.7 | ai-webbdesign |
| sida | Figma release notes | https://www.figma.com/release-notes/ | Figma Make | 0.7 | ai-webbdesign |
| sida | Framer updates | https://www.framer.com/updates | AI-sajtbyggare | 0.6 | ai-webbdesign |
| sida | v0 changelog | https://v0.app/changelog | AI-sajtbyggare (Vercel) | 0.6 | ai-webbdesign |
| rss | YouTube: Anthropic | https://www.youtube.com/feeds/videos.xml?channel_id=UCrDwWp7EBBv4NwvScIpBDOA | | 1.1 | modeller och guider |
| rss | YouTube: DesignCourse | https://www.youtube.com/feeds/videos.xml?channel_id=UCVyRiMvfUNMA1UPlDPzG5Ow | UI | 0.9 | form och typografi |
| rss | Gerry McGovern | https://gerrymcgovern.com/feed/ | toppuppgifter, innehåll | 1.2 | innehåll och copy |
| rss | UX Writing Hub | https://uxwritinghub.com/feed/ | mikrocopy | 1.0 | innehåll och copy |
| rss | GDS-bloggen | https://gds.blog.gov.uk/feed/ | innehållsdesign, tjänster | 1.2 | innehåll och copy |
| rss | NN/g | https://www.nngroup.com/feed/rss/ | måttstocken | 1.3 | ux och forskning |
| rss | GOV.UK design notes | https://designnotes.blog.gov.uk/feed/ | mönster prövade på riktiga användare | 1.3 | ux och forskning |
| rss | Jakob Nielsen (UX Tigers) | https://jakobnielsenphd.substack.com/feed | AI och användbarhet; heuristikernas upphovsman | 1.3 | ux och forskning |
| rss | Luke Wroblewski | https://www.lukew.com/rss.xml | formulär, mobil, AI-gränssnitt; källa i forfragan.md | 1.2 | ux och forskning |
| rss | Reddit: webbdesign och UX | https://www.reddit.com/r/web_design+webdev+Frontend+UXDesign+userexperience+typography+astrojs/top/.rss?t=week | veckans mest lästa trådar (påslaget 2026-10-08: spana.py håller minst 20 s mellan anrop till reddit.com, kirurgen läser trådar med kontroller/reddit_trad.py) | 0.8 | ux och forskning |
| rss | UX Collective | https://uxdesign.cc/feed | brett, termfiltret sållar | 0.7 | ux och forskning |
| sida | Baymard blog | https://baymard.com/blog | formulär, konvertering | 1.3 | ux och forskning |
| rss | Jeremy Keith | https://adactio.com/journal/rss | progressive enhancement, hantverk | 1.0 | ux och forskning |
| rss | Smashing Magazine | https://www.smashingmagazine.com/feed/ | | 1.2 | ux och forskning |
| rss | A List Apart | https://alistapart.com/main/feed/ | | 0.8 | ux och forskning |
| rss | Josh Comeau | https://www.joshwcomeau.com/rss.xml | CSS, layout | 1.1 | form och typografi |
| rss | Ahmad Shadeed | https://ishadeed.com/feed.xml | layout, komponenter | 1.1 | form och typografi |
| rss | Sidebar | https://sidebar.io/feed.xml | fem utvalda designlänkar om dagen | 1.0 | form och typografi |
| sida | Typewolf | https://www.typewolf.com/ | typsnitt i bruk | 0.9 | form och typografi |
| rss | Piccalilli | https://piccalil.li/feed.xml | CSS, progressive enhancement | 1.2 | form och typografi |
| rss | Sara Soueidan | https://www.sarasoueidan.com/blog/index.xml | | 1.2 | tillgänglighet |
| rss | Astro releases | https://github.com/withastro/astro/releases.atom | vår stack | 1.5 | stacken |
| rss | Astro blog | https://astro.build/rss.xml | | 1.3 | stacken |
| rss | web-features (Baseline) | https://github.com/web-platform-dx/web-features/releases.atom | vad som går att använda i alla webbläsare | 1.3 | stacken |
| rss | GOV.UK Frontend | https://github.com/alphagov/govuk-frontend/releases.atom | formulär- och felmönster | 1.2 | stacken |
| rss | Chrome for Developers | https://developer.chrome.com/static/blog/feed.xml | | 1.5 | stacken |
| rss | YouTube: Chrome for Developers | https://www.youtube.com/feeds/videos.xml?channel_id=UCnUYZLuoy1rq1aVMwx4aTzw | | 1.0 | stacken |
| rss | YouTube: Kevin Powell | https://www.youtube.com/feeds/videos.xml?channel_id=UCJZv4d5rbIKd4QHMPkcABCw | CSS | 1.0 | stacken |
| rss | YouTube: Web Dev Simplified | https://www.youtube.com/feeds/videos.xml?channel_id=UCFbNIlppjAuEX4znoulh0Cw | | 0.8 | stacken |
| rss | YouTube: Theo | https://www.youtube.com/feeds/videos.xml?channel_id=UCbRP3c757lWg9M-U7TyEkXA | åsikter, brus | 0.5 | stacken |
| rss | CSS-Tricks | https://css-tricks.com/feed/ | | 1.0 | stacken |
| rss | HTMHell | https://www.htmhell.dev/feed.xml | semantik | 1.1 | stacken |
| rss | CSS Weekly | https://feedpress.me/cssweekly | veckans CSS | 1.1 | stacken |
| rss | Frontend Focus | https://frontendfoc.us/rss | webbläsar- och plattformsnytt | 1.1 | stacken |
| rss | W3C WAI | https://www.w3.org/WAI/feed.xml | WCAG, standarder | 1.5 | tillgänglighet |
| rss | Deque | https://www.deque.com/feed/ | axe:s utgivare | 1.2 | tillgänglighet |
| rss | GOV.UK tillgänglighet | https://accessibility.blog.gov.uk/feed/ | | 1.2 | tillgänglighet |
| rss | Adrian Roselli | https://adrianroselli.com/feed | | 1.3 | tillgänglighet |
| rss | Lighthouse releases | https://github.com/GoogleChrome/lighthouse/releases.atom | provets grind | 1.5 | provet |
| rss | axe-core releases | https://github.com/dequelabs/axe-core/releases.atom | provets grind | 1.5 | provet |
| rss | Playwright releases | https://github.com/microsoft/playwright/releases.atom | inspektion, stilrapport | 1.5 | provet |
| rss | html-validate | https://gitlab.com/html-validate/html-validate/-/tags?format=atom | standardens 2.5 | 1.5 | provet |
| rss | schema.org | https://github.com/schemaorg/schemaorg/releases.atom | ny version: kör kontroller/data/hamta_schemaorg.py | 1.5 | provet |
| rss | web.dev | https://web.dev/feed.xml | Core Web Vitals | 1.5 | provet |
| rss | SpeedCurve | https://www.speedcurve.com/blog/rss/ | prestanda | 1.2 | provet |
| rss | Google Search Central | https://feeds.feedburner.com/blogspot/amDG | lokal SEO, rikresultat | 1.5 | lokal synlighet |
| sida | Google: AI-optimeringsguiden | https://developers.google.com/search/docs/fundamentals/ai-optimization-guide | Googles linje för AI Overviews och AI Mode (publicerad 2026-05-15, uppdaterad 2026-07-10) | 1.5 | lokal synlighet |
| sida | Google: AI-funktioner och din webbplats | https://developers.google.com/search/docs/appearance/ai-features | krav och kontroller för AI Overviews och AI Mode | 1.5 | lokal synlighet |
| rss | Google Search Status | https://status.search.google.com/en/feed.atom | rankinguppdateringar | 1.5 | lokal synlighet |
| rss | Sterling Sky | https://www.sterlingsky.ca/feed/ | Google-företagsprofilen | 1.3 | lokal synlighet |
| rss | Search Engine Roundtable | https://www.seroundtable.com/index.rdf | daglig SEO-nyhet, brusig | 0.9 | lokal synlighet |
| rss | Reddit: lokal SEO, copy och tillgänglighet | https://www.reddit.com/r/SEO+LocalSEO+copywriting+accessibility+smallbusiness/top/.rss?t=week | veckans mest lästa trådar (påslaget 2026-10-08: spana.py håller minst 20 s mellan anrop till reddit.com, kirurgen läser trådar med kontroller/reddit_trad.py) | 0.8 | lokal synlighet |
| sida | IMY | https://www.imy.se/nyheter/ | GDPR, integritetssidan | 1.3 | juridik och förtroende |
| sida | Konsumentverket | https://www.konsumentverket.se/aktuellt/ | marknadsföring, omdömen, priser | 1.3 | juridik och förtroende |
| sida | PTS | https://pts.se/sv/nyheter/ | kakor, e-post | 1.2 | juridik och förtroende |
| sida | Webbriktlinjer | https://webbriktlinjer.se/ | svenska riktlinjer för webben | 1.2 | juridik och förtroende |
| rss | Hamel Husain | https://hamel.dev/index.xml | evals, LLM som domare | 1.3 | granskning |
| rss | Eugene Yan | https://eugeneyan.com/rss/ | evals, domare | 1.2 | granskning |
| rss | Simon Willison | https://simonwillison.net/atom/everything/ | LLM-verktyg i praktiken | 1.2 | granskning |
| github | Claude Code-skills | claude code skills --stars ">=200" --updated 90d | brusig: 39 av 49 GitHub-repon dömdes nej | 0.8 | agentflödet |
| github | Lighthouse och axe | lighthouse accessibility audit --stars ">=200" --updated 90d | | 0.8 | provet |
| github | Astro-teman | astro theme business --language Astro --stars ">=50" | | 0.6 | stacken |
| github | Nytt och växande | website frontend "web design" --created 180d --stars ">=200" --sort stars | brusig | 0.5 | stacken |
| hn | HN: Core Web Vitals och Lighthouse | "core web vitals" OR lighthouse | | 1.1 | provet |
| hn | HN: tillgänglighet | accessibility WCAG | | 1.1 | tillgänglighet |
| hn | HN: Claude Code | "claude code" | gav schack, spel, kylskåpsmagneter | 0.8 | agentflödet |
| hn | HN: småföretagssajt | "small business" website | | 1.1 | ux och forskning |
| awesome | awesome-claude-code | https://github.com/hesreallyhim/awesome-claude-code | bara nya länkar räknas | 1.0 | agentflödet |
| awesome | awesome-design-md | https://github.com/VoltAgent/awesome-design-md | dömd nej som källa; här en pekare | 1.0 | ai-webbdesign |
| rss | Vercel changelog | https://vercel.com/atom | lanseringen väntar; höj vikten när en kund ska ut | 0.3 | lansering |
