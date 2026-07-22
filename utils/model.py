from groq import Groq
import json
import re

SECTORS = [
    "",
    # — General —
    "Automotive", "Aviation & Aerospace", "Beauty & Cosmetics",
    "Construction & Real Estate", "Crypto & Web3", "Education & E-Learning",
    "Entertainment & Media", "E-Sports & Gaming", "Fashion & Apparel",
    "Finance & Banking", "Food & Beverage", "Government & Politics",
    "Health & Medical", "Hotels & Hospitality", "Insurance",
    "Law & Legal Services", "Logistics & Shipping", "Luxury & Lifestyle",
    "Manufacturing & Industry", "Music & Audio", "NFT & Digital Art",
    "Non-Profit & NGO", "Outdoor & Recreation", "Pets & Animals", "Photography & Film",
    "Religion & Spiritual", "Retail & E-Commerce", "Software & SaaS",
    "Sports & Fitness", "Technology & Electronics", "Telecommunications",
    "Travel & Tourism", "YouTube & Content Creation",
    # — Mobile App —
    "Mobile App & Startup", "Fintech & Mobile Banking", "Food Delivery & Restaurant App",
    "Health & Fitness App", "Dating & Social App", "Productivity & SaaS App",
    "E-Commerce & Marketplace App", "Gaming & Mobile Gaming",
    "Education & Learning App", "Travel & Navigation App",
    # — Agency & Creative —
    "Branding & Design Agency", "Motion Design Studio", "Video Production Studio",
    "Creative Agency", "Social Media Agency", "Marketing Agency",
    "Advertising Agency", "UI/UX Design Studio", "3D & VFX Studio",
    "Illustration & Art Studio", "Photography Studio", "PR & Communications Agency",
    "Content Creation Agency", "Freelance Designer", "Independent Animator",
]

# Per-sector SEO hint — injected into prompt untuk guide seo_body dan keywords
SECTOR_SEO_HINT = {
    # General
    "Automotive": "Mention speed, precision engineering, bold motion, and automotive brand energy. Keywords: car brand animation, automotive logo reveal, vehicle brand motion.",
    "Aviation & Aerospace": "Mention precision, altitude, futuristic motion, and aerospace identity. Keywords: aviation logo animation, aerospace brand, flight brand motion.",
    "Beauty & Cosmetics": "Mention elegance, glow, fluid motion, and beauty brand identity. Keywords: beauty brand animation, cosmetics logo reveal, skincare brand motion.",
    "Construction & Real Estate": "Mention strength, trust, solid brand presence, and real estate identity. Keywords: construction logo animation, real estate brand motion, property brand reveal.",
    "Crypto & Web3": "Mention decentralization, digital assets, futuristic motion, and blockchain brand. Keywords: crypto logo animation, Web3 brand identity, blockchain brand motion.",
    "Education & E-Learning": "Mention knowledge, growth, clean motion, and educational brand identity. Keywords: education logo animation, e-learning brand, academic brand motion.",
    "Entertainment & Media": "Mention bold storytelling, dynamic motion, media brand energy. Keywords: entertainment logo animation, media brand reveal, broadcast identity motion.",
    "E-Sports & Gaming": "Mention competitive energy, team identity, aggressive motion, and gaming brand. Keywords: esports logo animation, gaming brand reveal, team logo motion.",
    "Fashion & Apparel": "Mention style, elegance, fluid brand motion, and fashion identity. Keywords: fashion logo animation, apparel brand reveal, clothing brand motion.",
    "Finance & Banking": "Mention trust, precision, clean motion, and financial brand stability. Keywords: finance logo animation, banking brand reveal, financial identity motion.",
    "Food & Beverage": "Mention appetite, energy, playful motion, and food brand personality. Keywords: food brand animation, beverage logo reveal, restaurant brand motion.",
    "Government & Politics": "Mention authority, trust, clean motion, and civic brand identity. Keywords: government logo animation, political brand motion, civic identity reveal.",
    "Health & Medical": "Mention trust, care, gentle motion, and healthcare brand identity. Keywords: medical logo animation, healthcare brand reveal, clinic brand motion.",
    "Hotels & Hospitality": "Mention luxury, welcome, smooth motion, and hospitality brand warmth. Keywords: hotel logo animation, hospitality brand reveal, resort brand motion.",
    "Insurance": "Mention protection, trust, steady motion, and insurance brand identity. Keywords: insurance logo animation, protection brand reveal, financial security brand.",
    "Law & Legal Services": "Mention authority, precision, strong brand presence. Keywords: law firm logo animation, legal brand motion, attorney brand reveal.",
    "Logistics & Shipping": "Mention speed, reliability, bold motion, and logistics brand energy. Keywords: logistics logo animation, shipping brand reveal, supply chain brand motion.",
    "Luxury & Lifestyle": "Mention exclusivity, refinement, slow elegant motion, and premium brand identity. Keywords: luxury logo animation, premium brand reveal, lifestyle brand motion.",
    "Manufacturing & Industry": "Mention strength, precision, industrial brand energy. Keywords: manufacturing logo animation, industrial brand motion, factory brand reveal.",
    "Music & Audio": "Mention rhythm, sound visualization, dynamic motion, and music brand personality. Keywords: music logo animation, audio brand reveal, record label brand motion.",
    "NFT & Digital Art": "Mention digital creativity, collector culture, glitch motion, and Web3 art brand. Keywords: NFT logo animation, digital art brand motion, crypto art brand reveal.",
    "Non-Profit & NGO": "Mention purpose, community, meaningful motion, and social brand identity. Keywords: nonprofit logo animation, NGO brand motion, charity brand reveal.",
    "Outdoor & Recreation": "Mention adventure, nature, energetic motion, and outdoor brand identity. Keywords: outdoor brand animation, recreation logo reveal, adventure brand motion.",
    "Pets & Animals": "Mention playfulness, warmth, cute motion, and pet brand personality. Keywords: pet brand animation, animal logo reveal, pet care brand motion.",
    "Photography & Film": "Mention visual storytelling, shutter motion, cinematic brand energy. Keywords: photography logo animation, film brand reveal, studio brand motion.",
    "Religion & Spiritual": "Mention peace, meaning, gentle motion, and spiritual brand identity. Keywords: spiritual logo animation, religious brand motion, faith brand reveal.",
    "Retail & E-Commerce": "Mention shopping energy, product brand motion, e-commerce identity. Keywords: retail logo animation, e-commerce brand reveal, shop brand motion.",
    "Software & SaaS": "Mention clean UI motion, product launch energy, and SaaS brand identity. Keywords: SaaS logo animation, software brand reveal, tech product brand motion.",
    "Sports & Fitness": "Mention energy, athletic motion, competitive brand identity. Keywords: sports logo animation, fitness brand reveal, athletic brand motion.",
    "Technology & Electronics": "Mention innovation, sleek motion, and tech brand identity. Keywords: tech logo animation, electronics brand reveal, gadget brand motion.",
    "Telecommunications": "Mention connectivity, signal motion, and telecom brand identity. Keywords: telecom logo animation, network brand reveal, connectivity brand motion.",
    "Travel & Tourism": "Mention wanderlust, smooth motion, and travel brand personality. Keywords: travel logo animation, tourism brand reveal, destination brand motion.",
    "YouTube & Content Creation": "Mention creator energy, channel identity, intro animation, and content brand motion. Keywords: YouTube logo animation, channel intro, content creator brand motion.",
    # Mobile App
    "Mobile App & Startup": "Mention app launch energy, startup brand identity, clean UI motion, and digital product branding. Keywords: app logo animation, startup brand motion, mobile app brand reveal, app icon animation.",
    "Fintech & Mobile Banking": "Mention financial trust, clean digital motion, secure brand identity, and fintech product launch. Keywords: fintech logo animation, mobile banking brand, digital finance brand motion, payment app identity.",
    "Food Delivery & Restaurant App": "Mention appetite, speed, warm brand energy, and food app identity. Keywords: food app logo animation, delivery brand motion, restaurant app brand reveal, food tech identity.",
    "Health & Fitness App": "Mention motivation, clean motion, wellness brand identity, and fitness app launch. Keywords: fitness app logo animation, health app brand motion, wellness brand reveal, workout app identity.",
    "Dating & Social App": "Mention connection, playful motion, social brand personality, and app launch energy. Keywords: dating app logo animation, social app brand motion, connection brand reveal, lifestyle app identity.",
    "Productivity & SaaS App": "Mention efficiency, clean minimal motion, workspace brand identity, and SaaS product launch. Keywords: productivity app logo animation, SaaS brand motion, workspace brand reveal, tool app identity.",
    "E-Commerce & Marketplace App": "Mention shopping energy, marketplace brand motion, digital commerce identity. Keywords: marketplace app logo animation, e-commerce brand reveal, shopping app brand motion, retail app identity.",
    "Gaming & Mobile Gaming": "Mention bold game studio identity, launch screen animation, mobile game brand energy. Keywords: mobile game logo animation, game studio brand motion, gaming app brand reveal, mobile gaming identity.",
    "Education & Learning App": "Mention knowledge, growth, friendly brand motion, and edtech app identity. Keywords: edtech logo animation, learning app brand motion, education app brand reveal, e-learning app identity.",
    "Travel & Navigation App": "Mention exploration, smooth motion, travel tech brand identity. Keywords: travel app logo animation, navigation brand motion, map app brand reveal, travel tech identity.",
    # Agency & Creative
    "Branding & Design Agency": "Mention brand craftsmanship, visual identity systems, agency portfolio, and professional brand motion. Keywords: branding agency logo animation, design agency brand reveal, identity studio motion, brand strategy in motion.",
    "Motion Design Studio": "Mention studio craft, motion reel, animation showreel, and studio identity. Keywords: motion design studio logo, animation studio brand reveal, motion studio identity, design studio intro animation.",
    "Video Production Studio": "Mention cinematic brand energy, production house identity, studio logo reveal. Keywords: video production logo animation, production studio brand motion, film studio identity reveal.",
    "Creative Agency": "Mention creative brand energy, agency identity, conceptual motion design. Keywords: creative agency logo animation, agency brand reveal, creative studio motion, concept-driven brand identity.",
    "Social Media Agency": "Mention digital-first branding, social brand motion, agency identity for content creators. Keywords: social media agency logo, digital agency brand animation, content agency motion, social brand reveal.",
    "Marketing Agency": "Mention results-driven brand identity, marketing studio motion, agency logo reveal. Keywords: marketing agency logo animation, digital marketing brand motion, growth agency identity reveal.",
    "Advertising Agency": "Mention bold campaign energy, ad agency brand identity, creative motion. Keywords: advertising agency logo animation, ad studio brand reveal, campaign identity in motion.",
    "UI/UX Design Studio": "Mention clean interface motion, product design identity, UX studio brand. Keywords: UI UX studio logo animation, product design brand motion, interface studio identity reveal.",
    "3D & VFX Studio": "Mention dimensional brand energy, VFX studio identity, render-quality motion. Keywords: VFX studio logo animation, 3D studio brand reveal, visual effects identity motion.",
    "Illustration & Art Studio": "Mention artistic brand personality, illustration studio identity, hand-crafted motion. Keywords: illustration studio logo animation, art studio brand reveal, creative studio identity motion.",
    "Photography Studio": "Mention visual storytelling, photography studio brand, shutter-inspired motion. Keywords: photography studio logo animation, photo brand reveal, studio identity motion.",
    "PR & Communications Agency": "Mention trust, clarity, professional brand motion, and PR agency identity. Keywords: PR agency logo animation, communications brand reveal, public relations identity motion.",
    "Content Creation Agency": "Mention creator economy branding, content studio identity, digital media motion. Keywords: content agency logo animation, creator studio brand reveal, media production identity motion.",
    "Freelance Designer": "Mention personal brand motion, designer portfolio identity, solo creative studio. Keywords: freelance designer logo animation, personal brand reveal, designer identity motion, solo studio brand.",
    "Independent Animator": "Mention animator personal brand, motion showreel identity, solo studio intro. Keywords: animator logo animation, motion artist brand reveal, independent studio identity, animator personal brand motion.",
}

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
    board_tone = BOARD_SEO_TONE.get(board, BOARD_SEO_TONE["Logo Animations"])

    sector_hint = SECTOR_SEO_HINT.get(sector, "")
    sector_instruction = (
        f"\nSECTOR SEO INSTRUCTION ({sector}): {sector_hint}"
        if sector_hint else ""
    )

    is_brand_identity = (board == "Brand Identity in Motion")
    brand_identity_note = (
        "\nIMPORTANT: This pin is about a full brand identity system in motion, not just a logo. "
        "The seo_body must reflect brand system, visual language, and motion branding. "
        "Avoid phrases like 'logo reveal' or 'logo intro'."
    ) if is_brand_identity else ""

    prompt = f"""You are a Pinterest SEO expert for motion design and brand identity content.
Generate SEO-optimized Pinterest content. Return ONLY valid JSON, no markdown, no backticks.

PIN TITLE: "{pin_title}"
BRAND NAME: {brand_name}
BOARD: {board}
KEYWORD CONTEXT: {keyword_context}{sector_ctx}
ORIGINAL CAPTION: {caption[:300]}

TONE INSTRUCTION FOR THIS BOARD: {board_tone}{brand_identity_note}{sector_instruction}

Generate:
- "keywords": comma-separated, max 20 highly relevant SEO keywords. Mix broad board keywords with specific sector keywords from the sector instruction above. No hashtags.
- "seo_body": 2 sentences of natural SEO text. Follow the board tone AND sector instruction above. Max 200 chars total. Do NOT repeat the pin title or brand name at the start. Never mention 3D, three-dimensional, or 3D design.

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
