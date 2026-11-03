#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Light-UI-UX — 3-Tier Adaptive Image Generation, CC0 Museum Retrieval & Pixel Analyzer (`scripts/media_gen.py`)
Supports:
  • Tier 1 (Host Native) : Structured prompt & post-processing contract for host `image-generator` subagent / MCP tool
  • Tier 2 (Custom API)  : User-configured OpenAI Images-compatible endpoint (`/v1/images/generations`)
  • Tier 3 (Zero-Key CC0): Open-access museum/archive search (Art Institute of Chicago, Met Museum, Wikimedia Commons) + local WebGL shader fallback
  • Pixel Analyzer       : 3x3 grid `calm` text-overlay zone detection, luminance profiling, and 6-step CSS page-blending snippet generator
"""

import argparse
import base64
import json
import math
import os
import re
import struct
import sys
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
GLOBAL_CONFIG_PATH = Path.home() / ".light-ui-ux" / "config.json"
LOCAL_CONFIG_PATH = WORKSPACE_ROOT / ".light-ui-ux.json"

FORBIDDEN_SLOP_PHRASES = [
    "ui background",
    "hero image",
    "website banner",
    "8k masterpiece",
    "futuristic glowing nodes",
    "cyberpunk neon grid",
    "transparent background",
    "checkerboard",
    "app icon",
    "brand mark",
    "vector logo",
    "emblem",
    "badge",
]

OPTICAL_PRESETS = {
    "editorial": "Shot on Hasselblad H6D-100c medium format, 80mm f/2.8 planar lens, Kodak Portra 400 film stock, natural directional window sidelight, subtle organic film grain, authentic tactile material micro-texture",
    "product": "Phase One IQ4 150MP studio macro photography, 120mm f/4 Apo-Macro lens, soft diffused overhead scrim lighting with controlled specular rim highlight, crisp depth of field, physical anodized and matte surface fidelity",
    "architectural": "Arca-Swiss large format technical camera, Rodenstock 45mm tilt-shift lens, golden hour low-angle directional sunlight casting long architectural shadows, Kodachrome 64 color science",
    "cinematic-dark": "Arri Alexa Mini LF, Cooke Anamorphic/i 50mm T2.3 lens, low-key chiaroscuro tungsten key light emerging from deep shadow, rich halation, atmospheric depth",
    "botanical-archive": "19th-century natural history museum specimen plate photography, overhead flat-lay diffused daylight, crisp organic edges, high-detail surface venation",
}

CALM_ZONE_DIRECTIVES = {
    "left": "Composition rule: place the primary subject in the right 55% of the frame; keep the entire left 45% as an uncluttered, out-of-focus, low-contrast negative space zone suitable for typography overlay.",
    "right": "Composition rule: place the primary subject in the left 55% of the frame; keep the entire right 45% as an uncluttered, smooth negative space zone suitable for typography overlay.",
    "top": "Composition rule: weight the subject in the lower 60% of the frame; leave the upper 40% as a calm, low-frequency tonal field for headline placement.",
    "bottom": "Composition rule: weight the subject in the upper 60% of the frame; leave the lower 40% as a quiet, smooth shadow/surface expanse.",
    "center": "Composition rule: frame the composition around the perimeter or as a subtle atmospheric field with a calm, low-variance center zone.",
    "none": "Composition rule: centered iconic subject occupying 75-85% of the frame with balanced breathing room.",
}


def load_config() -> dict:
    cfg = {
        "api_url": "",
        "api_key": "",
        "model": "black-forest-labs/FLUX.1-schnell",
        "provider": "openai-compatible",
    }
    # 1. Global config
    if GLOBAL_CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    # 2. Local config
    if LOCAL_CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(LOCAL_CONFIG_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    # 3. .env file in workspace
    env_fp = WORKSPACE_ROOT / ".env"
    if env_fp.exists():
        for line in env_fp.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip("\"'")
            if k == "LIGHT_IMAGE_API_URL":
                cfg["api_url"] = v
            elif k == "LIGHT_IMAGE_API_KEY":
                cfg["api_key"] = v
            elif k == "LIGHT_IMAGE_MODEL":
                cfg["model"] = v
            elif k == "LIGHT_IMAGE_PROVIDER":
                cfg["provider"] = v
    # 4. Environment variables (highest priority)
    if os.environ.get("LIGHT_IMAGE_API_URL"):
        cfg["api_url"] = os.environ["LIGHT_IMAGE_API_URL"]
    if os.environ.get("LIGHT_IMAGE_API_KEY"):
        cfg["api_key"] = os.environ["LIGHT_IMAGE_API_KEY"]
    if os.environ.get("LIGHT_IMAGE_MODEL"):
        cfg["model"] = os.environ["LIGHT_IMAGE_MODEL"]
    if os.environ.get("LIGHT_IMAGE_PROVIDER"):
        cfg["provider"] = os.environ["LIGHT_IMAGE_PROVIDER"]
    return cfg


def snap_to_16(val: int) -> int:
    return max(256, int(round(val / 16.0) * 16))


def sanitize_prompt(raw: str) -> str:
    cleaned = raw
    for bad in FORBIDDEN_SLOP_PHRASES:
        cleaned = re.sub(re.escape(bad), "", cleaned, flags=re.I)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def build_atelier_prompt(
    subject: str,
    mode: str = "editorial",
    bg_hex: str = "#0d0e11",
    calm_zone: str = "left",
    aspect: str = "16:9",
) -> dict:
    clean_subj = sanitize_prompt(subject)

    if mode == "ip-logo":
        pos = (
            f"Minimalist flat geometric character illustration of {clean_subj}. "
            "Constructed from only 4 to 7 bold rounded geometric shapes with zero sharp tips or acute angles. "
            "Retain only 1 defining species trait; no fingers, no hair texture, no whiskers, no blush, no props. "
            f"Strict 3-color semantic palette: 2 flat character body color blocks on a solid muted background ({bg_hex}), "
            "zero gradients, zero highlights, zero drop shadows. "
            "1:1 square canvas composition: the character emerges upright from the lower-left corner, "
            "breaking the bottom/side frame edge, occupying 88% of the canvas area."
        )
        neg = (
            "logo, brand mark, app icon, emblem, badge, circular border, text, typography, watermark, "
            "transparent background, checkerboard, 3D render, gradients, shadows, sharp corners, detailed fur"
        )
    elif mode == "cutout":
        pos = (
            f"Single isolated physical object: {clean_subj}. "
            f"{OPTICAL_PRESETS['product']}. "
            f"Shot against a completely uniform, flat, solid neutral studio backdrop ({bg_hex}) with crisp, "
            "well-defined outer silhouette edges and zero cast shadow clipping the frame border."
        )
        neg = (
            "busy background, text, watermark, UI chrome, cropped edges, motion blur, "
            "checkerboard pattern, neon glow, floating particles"
        )
    else:
        optics = OPTICAL_PRESETS.get(mode, OPTICAL_PRESETS["editorial"])
        calm_dir = CALM_ZONE_DIRECTIVES.get(calm_zone, CALM_ZONE_DIRECTIVES["left"])
        pos = (
            f"{clean_subj}. {optics}. "
            f"Color palette and ambient shadow floor harmonized with hex {bg_hex} so the image edges dissolve naturally into the page surface. "
            f"{calm_dir} Zero text, zero letters, zero UI widgets inside the photograph."
        )
        neg = (
            "UI background, hero image, website banner, text, letters, watermark, interface buttons, "
            "3D glowing nodes, purple cyan neon slop, plastic skin, oversaturated, uncanny, deformed"
        )

    aspect_map = {
        "16:9": (1344, 768),
        "4:3": (1152, 864),
        "1:1": (1024, 1024),
        "3:4": (864, 1152),
        "9:16": (768, 1344),
        "21:9": (1536, 640),
    }
    w, h = aspect_map.get(aspect, (1344, 768))

    # Generate 6-Step CSS Page-Blending Snippet
    grad_dir = {
        "left": "to right",
        "right": "to left",
        "top": "to bottom",
        "bottom": "to top",
        "center": "circle at center",
        "none": "to top",
    }.get(calm_zone, "to right")

    css_blend = f"""/* 6-Step Page-Blending CSS (Surface: {bg_hex}, Calm Text Zone: {calm_zone}) */
.hero-media-stage {{
  position: relative;
  background-color: {bg_hex};
  overflow: hidden;
}}
.hero-media-stage img {{
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  /* Step 2: Feather image edges into page surface */
  -webkit-mask-image: linear-gradient(to bottom, #000 82%, transparent 100%);
  mask-image: linear-gradient(to bottom, #000 82%, transparent 100%);
}}
.hero-media-stage::after {{
  content: "";
  position: absolute;
  inset: 0;
  /* Step 3: Local directional scrim protecting {calm_zone} text zone (>=4.5:1 contrast) */
  background: linear-gradient({grad_dir if calm_zone != 'center' else 'to bottom'}, {bg_hex} 0%, color-mix(in oklch, {bg_hex} 72%, transparent) 42%, transparent 78%);
  pointer-events: none;
}}"""

    return {
        "subject": clean_subj,
        "mode": mode,
        "bg_hex": bg_hex,
        "calm_zone": calm_zone,
        "aspect_ratio": aspect,
        "width": snap_to_16(w),
        "height": snap_to_16(h),
        "positive_prompt": pos,
        "negative_prompt": neg,
        "css_blending_snippet": css_blend,
    }


def call_custom_api(cfg: dict, prompt_spec: dict, out_path: Path) -> dict:
    api_url = cfg["api_url"].strip()
    api_key = cfg["api_key"].strip()
    model = cfg["model"].strip()

    if not api_url:
        api_url = "https://api.openai.com/v1/images/generations"
    elif not api_url.endswith("/generations") and "generativelanguage.googleapis.com" not in api_url:
        api_url = api_url.rstrip("/") + "/v1/images/generations" if "/v1" not in api_url else api_url.rstrip("/") + "/images/generations"

    payload = {
        "model": model,
        "prompt": prompt_spec["positive_prompt"],
        "n": 1,
        "size": f"{prompt_spec['width']}x{prompt_spec['height']}",
    }
    if "siliconflow" in api_url.lower() or "flux" in model.lower() or "kolors" in model.lower():
        payload["image_size"] = f"{prompt_spec['width']}x{prompt_spec['height']}"
        if prompt_spec.get("negative_prompt"):
            payload["negative_prompt"] = prompt_spec["negative_prompt"]

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Light-UI-UX/1.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=90) as resp:
        resp_data = json.loads(resp.read().decode("utf-8"))

    img_bytes = None
    data_list = resp_data.get("data") or resp_data.get("images") or []
    if data_list:
        first = data_list[0]
        if "b64_json" in first and first["b64_json"]:
            img_bytes = base64.b64decode(first["b64_json"])
        elif "url" in first and first["url"]:
            img_req = urllib.request.Request(first["url"], headers={"User-Agent": "Light-UI-UX/1.0"})
            with urllib.request.urlopen(img_req, timeout=60) as ir:
                img_bytes = ir.read()

    if not img_bytes:
        raise RuntimeError(f"API response did not contain image bytes or URL: {json.dumps(resp_data)[:300]}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(img_bytes)
    return {
        "status": "ok",
        "tier": "tier2-custom-api",
        "model": model,
        "output_path": str(out_path.resolve()),
        "bytes": len(img_bytes),
    }


def search_and_download_cc0(query: str, out_path: Path) -> dict:
    """Query Art Institute of Chicago (CC0 public domain) and Wikimedia Commons for authentic high-res imagery."""
    headers = {"User-Agent": "Light-UI-UX/1.0 (Open Source Design Tool; mailto:dev@example.com)"}

    # 1. Try Art Institute of Chicago Public Domain API
    aic_url = (
        "https://api.artic.edu/api/v1/artworks/search?"
        + urllib.parse.urlencode(
            {
                "q": query,
                "query[term][is_public_domain]": "true",
                "fields": "id,title,artist_display,image_id,thumbnail",
                "limit": 5,
            }
        )
    )
    try:
        req = urllib.request.Request(aic_url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        iiif_base = data.get("config", {}).get("iiif_url", "https://www.artic.edu/iiif/2")
        for item in data.get("data", []):
            img_id = item.get("image_id")
            if img_id:
                dl_url = f"{iiif_base}/{img_id}/full/1400,/0/default.jpg"
                img_req = urllib.request.Request(dl_url, headers=headers)
                with urllib.request.urlopen(img_req, timeout=30) as ir:
                    raw = ir.read()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(raw)
                return {
                    "status": "ok",
                    "tier": "tier3-cc0-archive",
                    "source": "Art Institute of Chicago (CC0 Public Domain)",
                    "title": item.get("title", ""),
                    "artist": item.get("artist_display", ""),
                    "url": dl_url,
                    "output_path": str(out_path.resolve()),
                    "bytes": len(raw),
                }
    except Exception:
        pass

    # 2. Fallback: Wikimedia Commons API
    wiki_url = (
        "https://commons.wikimedia.org/w/api.php?"
        + urllib.parse.urlencode(
            {
                "action": "query",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {query}",
                "gsrnamespace": 6,
                "gsrlimit": 5,
                "prop": "imageinfo",
                "iiprop": "url|dimensions|extmetadata",
                "iiurlwidth": 1440,
                "format": "json",
            }
        )
    )
    req = urllib.request.Request(wiki_url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        wdata = json.loads(resp.read().decode("utf-8"))
    pages = (wdata.get("query") or {}).get("pages") or {}
    for _, pinfo in pages.items():
        iinfo = (pinfo.get("imageinfo") or [{}])[0]
        dl_url = iinfo.get("thumburl") or iinfo.get("url")
        if dl_url:
            img_req = urllib.request.Request(dl_url, headers=headers)
            with urllib.request.urlopen(img_req, timeout=30) as ir:
                raw = ir.read()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(raw)
            return {
                "status": "ok",
                "tier": "tier3-cc0-archive",
                "source": "Wikimedia Commons",
                "title": pinfo.get("title", ""),
                "url": dl_url,
                "output_path": str(out_path.resolve()),
                "bytes": len(raw),
            }

    raise RuntimeError(f"No CC0 imagery found for query '{query}'.")


def decode_png_rgb_grid(fp: Path, grid_size: int = 48) -> tuple[int, int, list[tuple[int, int, int]]] | None:
    """
    Pure-Python PNG decoder + Pillow fallback that downsamples an image into a `grid_size x grid_size`
    RGB array for 3x3 `calm` text-overlay zone analysis.
    """
    # Try Pillow first if installed in the environment
    try:
        from PIL import Image  # type: ignore

        with Image.open(fp) as im:
            orig_w, orig_h = im.size
            im_rgb = im.convert("RGB").resize((grid_size, grid_size))
            pixels = list(im_rgb.getdata())
            return orig_w, orig_h, pixels
    except Exception:
        pass

    # Pure-Python 8-bit RGB/RGBA non-interlaced PNG parser
    raw = fp.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos = 8
    w = h = bit_depth = color_type = interlace = 0
    idat_chunks = []
    while pos < len(raw):
        length = struct.unpack(">I", raw[pos : pos + 4])[0]
        ctype = raw[pos + 4 : pos + 8]
        cdata = raw[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            w, h, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", cdata)
        elif ctype == b"IDAT":
            idat_chunks.append(cdata)
        elif ctype == b"IEND":
            break

    if bit_depth != 8 or color_type not in (2, 6) or interlace != 0 or not idat_chunks:
        return w, h, []

    bpp = 3 if color_type == 2 else 4
    stride = w * bpp
    decomp = zlib.decompress(b"".join(idat_chunks))
    prev_row = bytearray(stride)
    rows_rgb = []
    offset = 0
    for y in range(h):
        ftype = decomp[offset]
        offset += 1
        cur_row = bytearray(decomp[offset : offset + stride])
        offset += stride
        if ftype == 1:  # Sub
            for i in range(bpp, stride):
                cur_row[i] = (cur_row[i] + cur_row[i - bpp]) & 0xFF
        elif ftype == 2:  # Up
            for i in range(stride):
                cur_row[i] = (cur_row[i] + prev_row[i]) & 0xFF
        elif ftype == 3:  # Average
            for i in range(stride):
                left = cur_row[i - bpp] if i >= bpp else 0
                cur_row[i] = (cur_row[i] + ((left + prev_row[i]) >> 1)) & 0xFF
        elif ftype == 4:  # Paeth
            for i in range(stride):
                a = cur_row[i - bpp] if i >= bpp else 0
                b = prev_row[i]
                c = prev_row[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur_row[i] = (cur_row[i] + pr) & 0xFF
        prev_row = cur_row
        rows_rgb.append(cur_row)

    pixels = []
    for gy in range(grid_size):
        sy = min(h - 1, int(gy * h / grid_size))
        row_buf = rows_rgb[sy]
        for gx in range(grid_size):
            sx = min(w - 1, int(gx * w / grid_size)) * bpp
            pixels.append((row_buf[sx], row_buf[sx + 1], row_buf[sx + 2]))
    return w, h, pixels


def analyze_image_file(fp: Path) -> dict:
    if not fp.exists():
        raise FileNotFoundError(f"Image not found: {fp}")

    G = 48
    decoded = decode_png_rgb_grid(fp, G)
    if not decoded or not decoded[2]:
        return {
            "path": str(fp),
            "bytes": fp.stat().st_size,
            "width": decoded[0] if decoded else 0,
            "height": decoded[1] if decoded else 0,
            "note": "Header parsed (install Pillow `pip install Pillow` for non-PNG pixel grid analysis).",
        }

    w, h, pixels = decoded
    lums = [(0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0 for (r, g, b) in pixels]
    mean_lum = sum(lums) / len(lums)
    sd_lum = math.sqrt(sum((x - mean_lum) ** 2 for x in lums) / len(lums))

    avg_r = int(sum(p[0] for p in pixels) / len(pixels))
    avg_g = int(sum(p[1] for p in pixels) / len(pixels))
    avg_b = int(sum(p[2] for p in pixels) / len(pixels))
    dominant_hex = f"#{avg_r:02x}{avg_g:02x}{avg_b:02x}"

    # Evaluate 5 directional regions (left, right, top, bottom, center) for text-overlay calmness
    regions = {
        "left": (0, G // 3, 0, G),
        "right": (2 * G // 3, G, 0, G),
        "top": (0, G, 0, G // 3),
        "bottom": (0, G, 2 * G // 3, G),
        "center": (G // 4, 3 * G // 4, G // 4, 3 * G // 4),
    }
    calm_zones = []
    zone_metrics = {}
    for zname, (x0, x1, y0, y1) in regions.items():
        z_lums = []
        grads = []
        for y in range(y0, y1):
            for x in range(x0, x1):
                val = lums[y * G + x]
                z_lums.append(val)
                if x + 1 < x1:
                    grads.append(abs(lums[y * G + (x + 1)] - val))
                if y + 1 < y1:
                    grads.append(abs(lums[(y + 1) * G + x] - val))
        zm = sum(z_lums) / len(z_lums)
        zsd = math.sqrt(sum((v - zm) ** 2 for v in z_lums) / len(z_lums))
        zgrad = sum(grads) / max(1, len(grads))
        is_calm = zsd < 0.095 and zgrad < 0.025
        zone_metrics[zname] = {
            "mean_luminance": round(zm, 3),
            "std_dev": round(zsd, 3),
            "gradient": round(zgrad, 3),
            "calm": is_calm,
            "recommended_text_color": "#ffffff" if zm < 0.52 else "#111111",
        }
        if is_calm:
            calm_zones.append(zname)

    best_zone = calm_zones[0] if calm_zones else min(zone_metrics.keys(), key=lambda k: zone_metrics[k]["std_dev"] + zone_metrics[k]["gradient"])
    tone = "dark" if mean_lum < 0.38 else ("light" if mean_lum > 0.68 else "mid")

    return {
        "path": str(fp.resolve()),
        "width": w,
        "height": h,
        "aspect_ratio": round(w / max(1, h), 3),
        "tone": tone,
        "mean_luminance": round(mean_lum, 3),
        "overall_std_dev": round(sd_lum, 3),
        "dominant_hex": dominant_hex,
        "calm_zones": calm_zones,
        "best_text_overlay_zone": best_zone,
        "zone_details": zone_metrics,
        "html_snippet": f'<img src="{fp.name}" alt="" width="{w}" height="{h}" loading="eager" fetchpriority="high" decoding="async" />',
    }


def cmd_status(args):
    cfg = load_config()
    has_api = bool(cfg.get("api_key", "").strip())
    status = {
        "active_default_tier": "Tier 1 (Host native preferred; availability checked by calling agent)",
        "fallback_order": ["host", "api (if configured)", "cc0"],
        "tier1_host_native": "Use an available host image-generation tool. Python cannot detect host tool availability; pass --host-unavailable to select a fallback.",
        "tier2_custom_api": {
            "configured": has_api,
            "api_url": cfg.get("api_url") or "(default: https://api.openai.com/v1/images/generations)",
            "model": cfg.get("model"),
            "api_key_masked": (cfg["api_key"][:6] + "..." + cfg["api_key"][-4:]) if len(cfg.get("api_key", "")) > 10 else ("SET" if has_api else "NOT SET"),
            "config_files": [str(GLOBAL_CONFIG_PATH), str(LOCAL_CONFIG_PATH), str(WORKSPACE_ROOT / ".env")],
        },
        "tier3_zero_key_fallback": "Available (Art Institute of Chicago CC0 + Wikimedia Commons + 16 WebGL2 Shaders in light-arsenal.db)",
    }
    print(json.dumps(status, indent=2, ensure_ascii=False))


def cmd_config(args):
    target_fp = LOCAL_CONFIG_PATH if args.local else GLOBAL_CONFIG_PATH
    cfg = load_config()
    if args.url is not None:
        cfg["api_url"] = args.url
    if args.key is not None:
        cfg["api_key"] = args.key
    if args.model is not None:
        cfg["model"] = args.model
    if args.provider is not None:
        cfg["provider"] = args.provider
    target_fp.parent.mkdir(parents=True, exist_ok=True)
    target_fp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Saved custom image generation config to: {target_fp}")


def cmd_prompt(args):
    spec = build_atelier_prompt(
        subject=args.subject,
        mode=args.mode,
        bg_hex=args.bg_hex,
        calm_zone=args.calm_zone,
        aspect=args.aspect,
    )
    if args.json:
        print(json.dumps(spec, indent=2, ensure_ascii=False))
        return
    print(f"=== Atelier Zero 3-Layer Physical Optics Prompt ({spec['mode']} | {spec['width']}x{spec['height']}) ===")
    print(f"\n[Positive Prompt]:\n{spec['positive_prompt']}")
    print(f"\n[Negative Prompt]:\n{spec['negative_prompt']}")
    print(f"\n[6-Step CSS Page-Blending Snippet]:\n{spec['css_blending_snippet']}")


def cmd_generate(args):
    cfg = load_config()
    spec = build_atelier_prompt(
        subject=args.subject,
        mode=args.mode,
        bg_hex=args.bg_hex,
        calm_zone=args.calm_zone,
        aspect=args.aspect,
    )
    out_fp = Path(args.out)

    tier = args.tier
    if tier == "auto":
        if not args.host_unavailable:
            tier = "host"
        else:
            tier = "api" if cfg.get("api_key", "").strip() else "cc0"

    if tier == "api":
        if not cfg.get("api_key", "").strip():
            sys.stderr.write("[ERROR] Tier 2 API key not configured. Set LIGHT_IMAGE_API_KEY or run `python scripts/media_gen.py config --key ...`\n")
            sys.exit(1)
        res = call_custom_api(cfg, spec, out_fp)
        print(json.dumps({**res, "prompt_spec": spec}, indent=2, ensure_ascii=False))
    elif tier == "cc0":
        res = search_and_download_cc0(args.subject, out_fp)
        print(json.dumps({**res, "css_blending_snippet": spec["css_blending_snippet"]}, indent=2, ensure_ascii=False))
    else:
        # Tier 1 Host Native Delegation Contract
        payload = {
            "status": "delegate_to_host_subagent",
            "tier": "tier1-host-native",
            "instruction": "Invoke an available host image-generation tool with the positive_prompt below, save the image to `target_output_path`, and then run `python scripts/media_gen.py analyze <path>`. This response is a delegation request, not a generated image. If the host tool is unavailable, rerun the same command with --tier auto --host-unavailable to use the configured API, or CC0 when no API key is configured.",
            "target_output_path": str(out_fp.resolve()),
            "prompt_spec": spec,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))


def cmd_analyze(args):
    res = analyze_image_file(Path(args.image))
    print(json.dumps(res, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Light-UI-UX 3-Tier Adaptive Image Generation & Pixel Analyzer")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Check active image generation tier and API configuration")

    p_cfg = sub.add_parser("config", help="Configure custom image generation API URL, Key, and Model")
    p_cfg.add_argument("--url", help="API Endpoint URL (e.g., https://api.siliconflow.cn/v1/images/generations)")
    p_cfg.add_argument("--key", help="API Key")
    p_cfg.add_argument("--model", help="Model name (e.g., black-forest-labs/FLUX.1-schnell, gpt-image-1)")
    p_cfg.add_argument("--provider", default="openai-compatible")
    p_cfg.add_argument("--local", action="store_true", help="Save to workspace .light-ui-ux.json instead of ~/.light-ui-ux/config.json")

    for sub_name in ["prompt", "generate"]:
        p = sub.add_parser(sub_name, help="Build Atelier Zero prompt or generate/retrieve media")
        p.add_argument("subject", help="Concrete physical subject description (or search query for --tier cc0)")
        p.add_argument("--mode", choices=["editorial", "product", "architectural", "cinematic-dark", "botanical-archive", "cutout", "ip-logo"], default="editorial")
        p.add_argument("--bg-hex", default="#0d0e11", help="Page background surface hex for edge blending")
        p.add_argument("--calm-zone", choices=["left", "right", "top", "bottom", "center", "none"], default="left", help="Where text will overlay the image")
        p.add_argument("--aspect", choices=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9"], default="16:9")
        if sub_name == "generate":
            p.add_argument("--tier", choices=["auto", "host", "api", "cc0"], default="auto", help="Routing tier (auto prefers host; explicit tiers override the default)")
            p.add_argument("--host-unavailable", action="store_true", help="With --tier auto, use the configured API or CC0 when the calling agent has no available host image tool")
            p.add_argument("--out", required=True, help="Output image file path")

    p_ana = sub.add_parser("analyze", help="Analyze image luminance and 3x3 `calm` text-overlay safe zones")
    p_ana.add_argument("image", help="Path to image file")

    args = parser.parse_args()
    dispatch = {
        "status": cmd_status,
        "config": cmd_config,
        "prompt": cmd_prompt,
        "generate": cmd_generate,
        "analyze": cmd_analyze,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
