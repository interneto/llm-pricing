# LLM Pricing

**Compare the cost and quality of large language models.**

🌐 **[Open the live chart](https://interneto.github.io/llm-pricing/)**

The cost of LLMs is steadily falling while their quality improves. This project
puts both dimensions on one chart so that useful, affordable models are easier
to find.

A rough estimate of the **cost of an LLM** is
the cost per million tokens of input, mostly from [LLMPriceCheck](https://llmpricecheck.com/).
(Typically, inputs are the bigger component of the cost, compared to outputs.)

A rough estimate of the **quality of an LLM** is
the ELO score on the [LMSYS Leaderboard](https://lmarena.ai/).
(This is like the chess ELO score, but for LLMs, where people compare 2 LLMs on the same task.)

The chart combines:

- **Cost:** input price per million tokens (CPMI), primarily from
  [LLMPriceCheck](https://llmpricecheck.com/).
- **Quality:** ELO scores from the [LMSYS / LMArena leaderboard](https://lmarena.ai/).

Use the **Overall**, **Coding**, and **Hard** views to compare different quality
scores. Search by model name or move the month slider to explore how the market
has changed over time.

Some LLMs are "pareto optimal", i.e. there is no LLM better in both cost and quality.
These are shown in green 🟢 and are the best LLMs to use.

Some LLMs are "pareto suboptimal", i.e. there is no LLM worse in both cost and quality.
These are shown in red 🔴 and are the LLMs to avoid.

Last updated: **26 Jul 2026**

Related sources: [LiveBench](https://livebench.ai/) · [Artificial Analysis models](https://artificialanalysis.ai/models)

## Understanding the chart

Models in the green 🟢 **Pareto-optimal** set are not beaten by another model
on both price and quality. They are strong value choices.

Models in the red 🔴 **Pareto-suboptimal** set are beaten by another model on
both dimensions and may be worth avoiding.

The chart is a rough comparison, not a recommendation. Prices, availability,
context limits, latency, and task-specific performance can change the result.

## Updating the data

### Prerequisites

- [uv](https://docs.astral.sh/uv/) for running the Python scripts
- Playwright, which can either connect to Chrome/Chromium through the DevTools
  Protocol on `localhost:9222` or launch its own browser

Run the update script. By default, `download.py` first tries to connect to
Chrome at `localhost:9222`; if no CDP browser is available, it automatically
launches a headless browser through Playwright:

```bash
./update.sh
```

The script downloads the Overall, Hard, and Coding LMArena leaderboards to
temporary files and updates the corresponding columns in `data/elo.csv`.

To force a specific browser mode for one leaderboard:

```bash
# Use an existing Chrome DevTools Protocol session
uv run download.py URL output.tsv --browser cdp

# Launch Chrome/Chromium with Playwright
uv run download.py URL output.tsv --browser launch
```

Set `LLMPRICING_CHROMIUM` or pass `--executable` when Playwright cannot find
your Chrome/Chromium installation automatically. On Windows, the downloader
also checks `C:\Users\<user>\AppData\Local\Chromium\Application\chrome.exe`.
Install the Playwright browser runtime only if you do not want to use an
existing Chrome/Chromium installation:

```bash
uv run playwright install chromium
```

To update one leaderboard manually:

```bash
uv run download.py https://lmarena.ai/leaderboard/text file.txt
uv run scripts/update_elo.py file.txt --elo data/elo.csv --column overall
```

Use the following URL and column for the other leaderboards:

| Leaderboard | URL path | Column |
| --- | --- | --- |
| Overall | `/leaderboard/text` | `overall` |
| Hard | `/leaderboard/text/hard-prompts` | `hard` |
| Coding | `/leaderboard/text/coding` | `coding` |

`download.py --describe` prints the machine-readable command contract.

### Updating screenshots

Capture chart screenshots with `screenshot.py`:

```bash
uv run screenshot.py --model gpt,gemini,claude [--force]
```

Use `--dry-run` to preview the files that would be created. The default output
directory is `screenshots/`. To create a video from a captured sequence:

```bash
ffmpeg -framerate 2 -i screenshots/gpt-%03d.png \
  -c:v libvpx-vp9 -pix_fmt yuva420p screenshots/gpt.webm
```

## Repository layout

| Path | Purpose |
| --- | --- |
| `index.html` | Main pricing chart page |
| `intelligence.html` | Intelligence comparison page |
| `js/main.js` | Chart rendering, filtering, tooltips, and interactions |
| `data/elo.csv` | Historical model quality and pricing data |
| `data/narrative.json` | Scrollytelling chart content |
| `download.py` | Extracts leaderboard data through Chrome DevTools Protocol |
| `scripts/update_elo.py` | Merges leaderboard results into the CSV |
| `screenshot.py` | Captures chart screenshots with Playwright |
| `update.sh` | Updates all three leaderboard views |
