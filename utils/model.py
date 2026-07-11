from groq import Groq
import json
import re

SECTORS = [
    "", "Automotive", "Aviation & Aerospace", "Beauty & Cosmetics",
    "Construction & Real Estate", "Crypto & Web3", "Education & E-Learning",
    "Entertainment & Media", "E-Sports & Gaming", "Fashion & Apparel",
    "Finance & Banking", "Food & Beverage", "Government & Politics",
    "Health & Medical", "Hotels & Hospitality", "Insurance",
    "Law & Legal Services", "Logistics & Shipping", "Luxury & Lifestyle",
    "Manufacturing & Industry", "Music & Audio", "NFT & Digital Art",
    "Non-Profit & NGO", "Pets & Animals", "Photography & Film",
    "Religion & Spiritual", "Retail & E-Commerce", "Software & SaaS",
    "Sports & Fitness", "Technology & Electronics", "Telecommunications",
    "Travel & Tourism", "YouTube & Content Creation",
]

BOARDS_KEYWORD_CONTEXT = {
    "Logo Animations": "logo animation, motion graphics, brand animation, animated logo, logo reveal, motion design, brand identity, logo intro",
    "E Sports Gaming Logo Animations": "esports logo animation, gaming logo, esports branding, gaming motion graphics, esports team logo, gaming channel logo, streamer logo animation, esports identity",
    "Famous Brand Logo Animations": "famous brand logo, iconic brand animation, brand logo reveal, corporate logo animation, well-known brand motion, global brand identity, brand motion design",
}

CTA_VARIANTS = [
    "Link in bio 🔗 to get a custom animated logo today!",
    "Tap bio 👆 to order your professional logo animation.",
    "Click bio 🖱️ to get your static logo animated now.",
    "Visit bio 🚀 to start your logo animation process.",
    "Go to bio 💼 to get your brand logo animated fast.",
    "Go to bio ⚡ to bring your brand logo to life!",
    "Bio link 📲 to transform your logo into stunning 3D.",
    "Check profile ✨ to upgrade your logo with motion graphics.",
    "Visit profile 🎬 to make your static logo move beautifully.",
    "Link in bio 💎 to turn your logo into an eye-catching animation.",
    "Link in bio 🎯 to easily get your logo animated.",
    "Tap bio ⚡ for a quick and professional logo animation.",
    "Click bio 🤝 to get a high-quality animated logo without hassle.",
    "Visit bio 🔥 to get your logo animated quickly and easily.",
]


def detect_credits(caption: str, uploader_id: str, api_key: str) -> dict:
    """Detect client, animator, logo_maker, brand_name from caption only."""
    client = Groq(api_key=api_key)

    prompt = f"""Analyze this Instagram caption for a logo animation post.
Extract credit information. Return ONLY valid JSON, no markdown, no backticks.

CAPTION:
\"\"\"{caption}\"\"\"

UPLOADER_ID (the IG account that posted this — treat as the animator/creator by default): @{uploader_id}

Rules:
- "animator": ALWAYS @{uploader_id}. Never change this.
- "client": @username of the person/brand the animation was made FOR or WITH.
  Look for: "for @", "with @", "client @", "made for @", "made with @", or any @mention that is NOT the uploader.
  Example: "made with my wife - @ganihakobian" → client = @ganihakobian.
  Example: "logo animation for @nikesports" → client = @nikesports.
  null if no other @mention found.
- "logo_maker": @username explicitly credited as logo designer/graphic designer.
  Look for: "logo by @", "design by @", "graphic by @", "designed by @".
  null if not found. Do NOT assign client as logo_maker.
- "brand_name": plain name of the brand/logo being animated. Infer from context. If unclear, use empty string.

Return:
{{
  "brand_name": "...",
  "client": "@username or null",
  "animator": "@{uploader_id}",
  "logo_maker": "@username or null"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text.strip())
    except Exception:
        return {"brand_name": "", "client": None, "animator": f"@{uploader_id}", "logo_maker": None}


def generate_content(
    pin_title: str,
    brand_name: str,
    client: str,
    animator: str,
    logo_maker: str,
    board: str,
    caption: str,
    api_key: str,
    cta_index: int = 0,
    sector: str = "",
) -> dict:
    """Generate SEO title, description, keywords."""
    groq_client = Groq(api_key=api_key)
    keyword_context = BOARDS_KEYWORD_CONTEXT.get(board, BOARDS_KEYWORD_CONTEXT["Logo Animations"])
    cta_title = CTA_VARIANTS[cta_index % len(CTA_VARIANTS)]
    cta_desc = CTA_VARIANTS[(cta_index + 1) % len(CTA_VARIANTS)]

    # Build credit line
    parts = []
    if client and client not in ("null", ""):
        parts.append(f"IG: {client}")
    if animator:
        parts.append(f"Credit: {animator} on Instagram")
    if logo_maker and logo_maker not in ("null", ""):
        parts.append(f"Logo by {logo_maker}")
    credit_line = " | ".join(parts) if parts else f"Credit: {animator} on Instagram"

    sector_ctx = f" | Sector: {sector}" if sector else ""
    sector_kw = f", {sector.lower()} industry" if sector else ""
    sector_seo = f" Ideal for {sector.lower()} brands looking to elevate their visual identity." if sector else ""

    prompt = f"""You are a Pinterest SEO expert for logo animation content.
Generate SEO-optimized Pinterest content. Return ONLY valid JSON, no markdown, no backticks.

PIN TITLE: "{pin_title}"
BRAND NAME: {brand_name}
BOARD: {board}
KEYWORD CONTEXT: {keyword_context}{sector_ctx}
ORIGINAL CAPTION: {caption[:300]}

Generate:
- "keywords": comma-separated, max 20 highly relevant SEO keywords. Mix broad (logo animation, motion graphics) and specific (brand name, animation style{sector_kw}). No hashtags.
- "seo_body": 2 sentences of natural SEO text about this specific animation. Mention motion style, brand energy, visual quality.{sector_seo} Max 200 chars total. Do NOT repeat the pin title or brand name at the start.

Description format (for your reference only, do not include in output):
Line 1: {credit_line}
Line 2-3: seo_body
Line 4: {cta_desc}

Return:
{{
  "keywords": "...",
  "seo_body": "..."
}}"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text.strip())

        pin_title_full = f"{pin_title}. {cta_title}"
        # Description: NO title repeat — starts directly with credit line
        full_description = f"{credit_line}\n{data['seo_body']}\n{cta_desc}"

        return {
            "title": pin_title_full,
            "description": full_description,
            "keywords": data["keywords"],
            "credit_line": credit_line,
        }
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model returned invalid JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Groq API error: {str(e)}")
