# 生图配置

[返回 README](../README.md) · [English](image-api.en.md)

## 调用顺序

1. Agent 有可用的原生生图工具时，优先调用宿主工具。
2. 宿主工具不可用时，使用已配置的自定义 API。
3. 未配置 API 时，检索开放授权素材。

填写自定义 Key 不会改变这一顺序。在任务中明确指定生图通道时，以你的选择为准；设计不需要图片时，不会为了生图而生图。

## 配置文件

将 **Skill 根目录**中的 [`.light-ui-ux.example.json`](../.light-ui-ux.example.json) 复制为 `.light-ui-ux.json`：

```json
{
  "api_url": "https://your-api.example/v1/images/generations",
  "api_key": "",
  "model": "YOUR_IMAGE_MODEL_ID",
  "provider": "openai-compatible"
}
```

| 字段 | 填写内容 |
| --- | --- |
| `api_url` | 服务商提供的完整图片生成接口地址，通常以 `/v1/images/generations` 结尾 |
| `api_key` | 你的 API Key；留空时不启用自定义 API |
| `model` | 服务商提供的生图模型 ID |
| `provider` | 保持 `openai-compatible` |

保存后，下一次调用会读取配置，无需重启。配置放在 Skill 目录，生成的网站无需携带它。

支持 Bearer Key 鉴权，以及返回 `data[].b64_json` 或 `data[].url` 的 OpenAI Images 兼容接口。Gemini 原生协议、聊天生图协议和异步任务接口需要适配，不能只替换 URL。

真实配置仅在本地保存。`.light-ui-ux.json` 和 `.env` 已加入忽略列表，Release 只包含空白模板。提交 Issue 或分享项目时，请删除真实 URL、Key 和请求中的私密内容。

## 其他配置方式

也可以使用环境变量，优先级由高到低：

系统环境变量 → Skill 根目录 `.env` → Skill 根目录 `.light-ui-ux.json` → 用户目录 `~/.light-ui-ux/config.json`。

| 环境变量 | 对应字段 |
| --- | --- |
| `LIGHT_IMAGE_API_URL` | `api_url` |
| `LIGHT_IMAGE_API_KEY` | `api_key` |
| `LIGHT_IMAGE_MODEL` | `model` |
| `LIGHT_IMAGE_PROVIDER` | `provider` |

## 命令行使用

在 Skill 根目录运行；macOS / Linux 使用 `python3`：

```bash
# 查看通道状态，不生成图片
python scripts/media_gen.py status

# 使用自定义接口
python scripts/media_gen.py generate "A ceramic cup on linen, soft daylight" --tier api --out ./cup.png

# 宿主不可用时，自动选择自定义 API 或开放素材
python scripts/media_gen.py generate "A ceramic cup on linen, soft daylight" --host-unavailable --out ./cup.png
```

宿主生图由 Agent 调用对应工具。脚本在宿主通道下返回调用所需的提示词与参数，由 Agent 接着完成生图。
