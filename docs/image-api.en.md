# Image configuration

[Back to README](../README.md) · [简体中文](image-api.zh-CN.md)

## Channel priority

1. Use the agent's native image-generation tool when one is available.
2. If no host tool is available, use the configured custom API.
3. Without a custom API, search openly licensed media.

Adding an API key does not change this order. An explicit provider choice in your brief takes precedence. Images are generated when the design calls for them.

## Configuration file

Copy [`.light-ui-ux.example.json`](../.light-ui-ux.example.json) to `.light-ui-ux.json` in the **skill's root directory**:

```json
{
  "api_url": "https://your-api.example/v1/images/generations",
  "api_key": "",
  "model": "YOUR_IMAGE_MODEL_ID",
  "provider": "openai-compatible"
}
```

| Field | Value |
| --- | --- |
| `api_url` | Your provider's full image-generation endpoint, usually ending in `/v1/images/generations` |
| `api_key` | Your API key; an empty value leaves the custom channel disabled |
| `model` | The image model ID supplied by your provider |
| `provider` | Keep `openai-compatible` |

Changes are read on the next call. Keep the file in the skill directory; generated websites do not need it.

The script supports Bearer authentication and OpenAI Images-compatible responses containing `data[].b64_json` or `data[].url`. Native Gemini, chat-based image generation, and asynchronous job APIs need an adapter rather than a URL change alone.

Keep real configuration local. `.light-ui-ux.json` and `.env` are ignored, and release archives include only the empty template. Remove actual endpoints, keys, and private request content before sharing an issue or project.

## Other configuration sources

Settings are resolved in this order, highest priority first:

System environment → `.env` in the skill root → `.light-ui-ux.json` in the skill root → `~/.light-ui-ux/config.json`.

| Environment variable | Field |
| --- | --- |
| `LIGHT_IMAGE_API_URL` | `api_url` |
| `LIGHT_IMAGE_API_KEY` | `api_key` |
| `LIGHT_IMAGE_MODEL` | `model` |
| `LIGHT_IMAGE_PROVIDER` | `provider` |

## Command line

Run from the skill root. Use `python3` on macOS / Linux:

```bash
# Show channel status without generating an image
python scripts/media_gen.py status

# Use the custom API
python scripts/media_gen.py generate "A ceramic cup on linen, soft daylight" --tier api --out ./cup.png

# Choose the custom API or open media when a host tool is unavailable
python scripts/media_gen.py generate "A ceramic cup on linen, soft daylight" --host-unavailable --out ./cup.png
```

Native generation is handled by the agent's image tool. In host mode, the script returns the prompt and parameters for the agent to carry out the generation.
