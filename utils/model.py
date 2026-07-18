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
    "Brand Identity in Motion": "brand identity animation, animated brand identity, motion branding, brand in motion, visual identity system, kinetic branding, brand motion design, animated brand system",
}

BOARD_SEO_TONE = {
    "Logo Animations": "Focus on animation quality, motion style, and logo reveal technique. Use words like: logo reveal, animated logo, motion design, logo intro, brand animation.",
    "E Sports Gaming Logo Animations": "Focus on gaming energy, esports identity, and competitive branding. Use words like: esports logo, gaming clan, streamer intro, team identity, gaming motion.",
    "Famous Brand Logo Animations": "Focus on iconic brand recognition, corporate identity, and global brand presence. Use words like: iconic brand, corporate logo, world-famous, brand reveal, global identity.",
    "Brand Identity in Motion": "Focus on brand storytelling, visual identity systems, and how the brand communicates through motion. Do NOT focus on just the logo — talk about brand personality, visual language, and identity in motion. Use words like: brand identity, visual storytelling, motion branding, brand system, kinetic identity.",
}

BOARD_TITLE_SUFFIX = {
    "Logo Animations": "Logo Animation",
    "E Sports Gaming Logo Animations": "Logo Animation",
    "Famous Brand Logo Animations": "Logo Animation",
    "Brand Identity in Motion": "Animated Brand Identity",
}

CTA_VARIANTS = [
    "Inspired by this? Our bio link connects you with the right motion designer 🔗",
    "Love this style? Find talented animators via the link in our bio ✨",
    "Bio link has options if you want something like this for your brand 🎬",
    "See bio link to explore logo animation services for your brand 🔗",
    "Want this for your brand? Our bio link is a good starting point 💡",
    "Curious about motion design? Check the bio link for where to start 🎯",
    "Great motion design is closer than you think. Bio link has options 🔗",
    "Find the right motion designer for your brand via our bio link ✨",
    "Bio link connects you with designers who can bring your logo to life 🎬",
    "Looking for motion design services? Start with the bio link 🔗",
    "Your brand could move like this. Bio link has the right people 💡",
    "Explore logo animation options for your brand via the bio link 🎯",
    "Motion design for your brand starts here. Check the bio link 🔗",
    "Bio link has everything you need to get your brand animated ✨",
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

    board_tone = BOARD_SEO_TONE.get(board, BOARD_SEO_TONE["Logo Animations"])

    prompt = f"""You are a Pinterest SEO expert for motion design and brand identity content.
Generate SEO-optimized Pinterest content. Return ONLY valid JSON, no markdown, no backticks.

PIN TITLE: "{pin_title}"
BRAND NAME: {brand_name}
BOARD: {board}
KEYWORD CONTEXT: {keyword_context}{sector_ctx}
ORIGINAL CAPTION: {caption[:300]}

TONE INSTRUCTION FOR THIS BOARD: {board_tone}

Generate:
- "keywords": comma-separated, max 20 highly relevant SEO keywords. Mix broad and specific terms based on the board tone above{sector_kw}. No hashtags.
- "seo_body": 2 sentences of natural SEO text. Follow the board tone instruction above.{sector_seo} Max 200 chars total. Do NOT repeat the pin title or brand name at the start. Never mention 3D, three-dimensional, or 3D design.

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
