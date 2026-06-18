# How to update

Go to each of these pages:

- https://lmarena.ai/leaderboard/text
- https://lmarena.ai/leaderboard/text/hard-prompts
- https://lmarena.ai/leaderboard/text/coding

Paste this bookmarklet:

```js
copy($$("table tr").map(d => {
  const cells = d.querySelectorAll("td, th");
  const [model, score] = [cells[2].querySelector("a")?.innerText ?? cells[2].innerText, cells[3].innerText.split(/\s/)[0]];
  return `${model}\t${score}`;
}).join("\n"));
```

Save as file.txt and run:

```bash
uv run update_elo.py file.txt --column [overall|coding|hard]
```

# Billing rates

Run `uv run billing.py` to get the per-hour output "billing rates" of LLMs in billing.json.

Blog post: https://www.s-anand.net/blog/wage-rates-of-nations-and-llms/
ChatGPT analysis: https://chatgpt.com/share/68317a06-0cac-800c-ad6f-13646ceb489f