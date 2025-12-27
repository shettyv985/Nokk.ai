"""
Basecamp AI QC Bot v15.0 – Multi-Project Support
Handles multiple projects with project-specific brand contexts
"""

import re
import os
from datetime import datetime
import traceback
from dotenv import load_dotenv
from groq import Groq
import requests
from flask import Flask, request, jsonify
from PIL import Image
from huggingface_hub import InferenceClient
import threading
from queue import Queue
from dataclasses import dataclass
from typing import Optional

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

CONFIG = {
    "CLIENT_ID": os.getenv("CLIENT_ID", ""),
    "CLIENT_SECRET": os.getenv("CLIENT_SECRET", ""),
    "REFRESH_TOKEN": os.getenv("REFRESH_TOKEN", ""),
    "ACCOUNT_ID": os.getenv("ACCOUNT_ID", ""),
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
}

# Project configurations with brand personality
PROJECTS = {
    37749144: {
        "name": "ABAD BUILDERS",
        "card_table_id": 7457620867,
        "brand_context": """Background: Founded in 1995 under the ABAD Group, Abad Builders is a Kochi-based premium real estate developer specializing in luxury apartments and villas, with 48+ completed projects and 3,000+ families housed, known for trust, transparency, and superior craftsmanship.

Tone: Formal, polished, professional, and premium at all times.

Audience: High-end, discerning homebuyers seeking exclusivity, long-term value, and refined living.

Content Focus: Always highlight project location, connectivity advantages, premium amenities, and clear unique selling points.

Communication Style: Direct, concise, confident, and impact-driven with no unnecessary fluff.

Visual Direction: Use high-quality, elegant, minimal visuals that reflect luxury, scale, and architectural finesse.

Trends: Instagram trends and viral formats are allowed only when adapted tastefully to match a premium real estate brand.

Language: Content may be in English, Malayalam, Manglish(English+Malayalam) ; English, Malayalam, Manglish(English+Malayalam) must be equally refined, accurate, and professional.

Goal: Drive qualified leads, encourage site visits, and build long-term brand trust."""
    },
    42909637: {
        "name": "ActivBase",
        "card_table_id": 8806504777,
        "brand_context": """Background: Activbase is a sports and orthopedic rehabilitation brand in India focused on holistic wellness, movement science, and empowering individuals across all demographics.

Tone: Polished, professional, credible, and performance-focused.

Communication Style: Direct and professional; minimal humor is allowed but must remain subtle, relevant, and never casual.

Trends: Use relevant sports, rehabilitation, and fitness trends only when they reinforce Activbase’s mission and expertise.

Audience: Athletes, sports enthusiasts, and individuals seeking high-quality orthopedic rehabilitation and fitness solutions.

Facilities & Locations: Highlight state-of-the-art rehabilitation facilities, modern equipment, and multi-location presence across India.

Language: English, Malayalam, Manglish(English+Malayalam)  content are both allowed; English, Malayalam, Manglish(English+Malayalam) must be equally refined in quality, clarity, and professionalism.

Goal: Enable optimal physical and mental performance while promoting a culture of excellence in health, movement, and recovery."""
    },
    32745257: {
        "name": "Angel Lungies",
        "card_table_id": 6147569340,
        "brand_context": """Background: Founded in 1988, Angel Lungies is a third-generation Indian textile brand known for high-quality lungies and premium Indian cotton bath towels, built on craftsmanship, quality, and customer trust.

Tone: Professional, simple, and easy to understand.

Communication Style: Direct and product-focused, clearly highlighting features, benefits, and everyday comfort.

Visual Direction: Products must be showcased clearly, properly, and prominently in all images.

Trends: Trends and popular formats are allowed when they support product clarity and value.

Audience: Everyday consumers seeking comfortable, durable, and high-quality lungies and towels.

Language: English, Malayalam, Manglish(English+Malayalam) content are allowed; both must be high-quality, accurate, and easy to understand.

Goal: Emphasize product quality, comfort, and value while building long-term customer trust and loyalty.

Benjies Rule: When referring to Benjies, never use the words activewear, boxers, innerwear, or underwear."""
    },
    43383165: {
        "name": "Bismi Connect",
        "card_table_id": 8929602065,
        "brand_context": """Background: Bismi Connect Kottayam, part of the Bismi Group, is a multi-category retail store in  Kerala, offering home appliances, electronics, mobiles, computers, and related services through a trusted statewide retail network.

Audience: Families and homemakers, tech-savvy customers, first-time buyers needing guidance, working professionals upgrading home or office appliances, and students purchasing mobiles, laptops, and accessories.

Tone: Friendly, professional, approachable, and customer-first.

Communication Style: Direct, simple, and easy to understand, clearly highlighting product features, benefits, pricing value, and practical usage.

Visual Direction: Products must be showcased clearly, prominently, and accurately in all images and videos.

Trends: Reels and viral formats are allowed when clean, relevant, and strictly product-focused.

Language:English, Malayalam, Manglish(English+Malayalam) content are both allowed and must be high-quality, professional, and consumer-friendly.

Goal: Emphasize product value, quality, and usefulness, build trust and loyalty, help customers make confident buying decisions, and position Bismi Connect as a reliable all-in-one electronics and appliance destination."""
    },
    30438693: {
        "name": "BluCampus",
        "card_table_id": 7086056821,
        "brand_context": """Background: BluCampus, established in 2023, is the education arm of Blusteak Media, delivering industry-driven digital marketing education powered by real agency experience and hands-on training.

Brand Essence: A practical, skill-first learning hub focused on real-world exposure, agency-level expertise, and job readiness.

Audience: Students seeking industry-relevant training, freshers aiming for job-ready skills, working professionals upskilling or switching careers, and entrepreneurs learning digital marketing.

Tone: Motivational, professional, positive, and trustworthy.

Communication Style: Direct, clear, and inspiring, emphasizing practical learning, mentorship strength, real agency environment, and career outcomes without overhype.

Visual Direction: Use real class sessions, agency-style training setups, student activities, and practical work environments.

Trends: Clean, relevant trends are allowed when they support education, authenticity, and learning outcomes.

Language: High-quality English, Malayalam, Manglish(English+Malayalam) content; both must be crisp, educational, and easy to understand.

Goal: Position BluCampus as Kerala’s most trusted practical digital marketing learning hub by driving admissions through proof of job readiness, mentorship, and real project exposure."""
    },
    36261272: {
        "name": "Brillar",
        "card_table_id": 7069783202,
        "brand_context": """Background: Brillar, from the ABAD Group and rooted in Kochi’s culinary culture, offers premium frozen foods that deliver authentic homestyle taste for modern, busy lifestyles.

Brand Essence: A balance of authenticity, convenience, and soulful flavour—preserving traditional cooking values in ready-to-use food solutions.

Audience: Working professionals, busy households, students living away from home, and families seeking quick yet authentic meals.

Product Categories: Ready-to-Fry, Ready-to-Cook, and Heat-&-Eat products, positioned as quick, easy, high-quality, and homestyle.

Tone: Warm, inviting, family-oriented, and trustworthy.

Communication Style: Direct, simple, and emotionally warm, highlighting taste, convenience, quality, and authenticity without exaggeration.

Visual Direction: Showcase food clearly, appetizingly, and realistically, focusing on freshness and homely appeal.

Trends: Instagram and Reel trends are allowed when clean, food-focused, and aligned with brand warmth.

Language: High-quality English, Malayalam, Manglish(English+Malayalam) content, maintaining emotional flavour, clarity, and consumer friendliness.

Goal: Position Brillar as a trusted frozen food brand delivering the true taste of home with modern convenience, driving purchase through flavour, ease, and reliability."""
    },
    
    24763032: {
        "name": "Blusteak",
        "card_table_id": 7036264515,
        "brand_context": """Background: Founded in 2017 by Telson Thomas and Jaison Thomas, Blusteak Media is a Kerala-based creative digital marketing agency with a 25+ member team, delivering result-oriented digital solutions to 75+ clients across four continents.

Brand Essence: A fusion of creativity, performance, and smart digital problem-solving, blending data, storytelling, and innovation to drive measurable business growth.

Audience: Ambitious brands seeking online growth, performance-driven campaigns, strong social media presence, and end-to-end digital strategy.

Tone: Confident, creative, modern, solution-oriented, and insight-led, never overhyped.

Communication Style: Clear, concise, and value-driven, focusing on results, strategy, creativity, and brand growth.

Visual Direction: Fresh, aesthetic, trend-aware, and consistently aligned with the brand’s creative identity.

Trends & Humor: All relevant trends and humorous formats are allowed, including reel-based and trend-led content, as long as they remain smart, strategic, and brand-relevant.

Language: High-quality English, Malayalam, and Manglish (English + Malayalam), maintaining clarity, professionalism, and creative expression.

Goal: Position Blusteak Media as Kerala’s top creative-performance digital agency by showcasing measurable results, strategic thinking, and standout creative execution."""
    },


    24763639: {
        "name": "Care N Cure",
        "card_table_id": 7036265363,
        "brand_context": """Background: Care n Cure Pharmacy is a trusted healthcare retail chain in Qatar, operating 63+ outlets across Doha, including multiple 24×7 pharmacies, offering professional pharmacist-led guidance and high-quality, internationally compliant healthcare products.

Brand Essence: Accessible, supportive, and reliable healthcare delivered with professionalism, accuracy, and care.

Audience: Residents of Doha and wider Qatar, including families, working professionals, parents, and elderly customers seeking convenient and trustworthy pharmacy services.

Tone: Professional, warm, friendly, empathetic, culturally respectful, and easy to understand.

Communication Style: Supportive and community-focused, highlighting accessibility, pharmacist expertise, safety, hygiene, and accurate dispensing without medical claims.

Content Focus: Emphasise 24×7 availability, convenient locations, friendly pharmacists, product authenticity, international standards, and reliable service.

Visual Direction: Clean, hygienic, lifestyle-oriented visuals with minimal text and clear product presentation.

Trends: Clean, relevant trends are allowed when they remain informative, respectful, and healthcare-appropriate.

Language: Clear, simple, and professional English (and Arabic/Malayalam only if approved), avoiding complex medical terminology.

Word Restrictions: Never use outcome-based or guarantee terms (e.g., guaranteed, complete cure, 100% results); use safe alternatives like expert guidance, supportive care, helps in managing, recommended options.

Do’s: Highlight 24×7 service, pharmacist support, accuracy, safety standards, and Qatar/Doha context.

Don’ts: Do not promise outcomes, give prescriptions, exaggerate effects, or imply guaranteed medical results.

Goal: Position Care n Cure Pharmacy as Qatar’s most dependable, accessible, and professional pharmacy chain built on trust, care, and convenience."""
    },
    42155802: {
        "name": "Chakolas",
        "card_table_id": 8610065428,
        "brand_context": """Background: Chakolas Pavilion is a distinguished event destination in Kalamassery, Ernakulam, known for refined architecture, calm ambience, and precisely orchestrated hospitality across banquets, dining, and guest services.

Brand Essence: Quiet elegance, disciplined execution, and thoughtfully curated experiences shaped by aesthetics, structure, and grace.

Experience & Offerings: World-class banquet halls, gourmet F&B and outdoor catering, professional event coordination, luxury guest accommodation, spacious parking, immaculate hygiene, and seamless event flow.

Audience: High-earning NRIs, corporate leaders, entrepreneurs, discerning families, and individuals who value subtle refinement over flamboyance.

Tone: Poetic, calm, sophisticated, culturally grounded, and emotionally layered.

Language Style: Refined vocabulary with rhythm and restraint, evoking harmony, serenity, craftsmanship, and timelessness without exaggeration.

Communication Style: Experience-led, evocative, and human, never sales-driven, generic, templated, or mechanical.

Visual Direction: Cinematic yet calm visuals highlighting space, light, structure, hospitality, and atmosphere.

Trends: Trend formats are allowed only when executed with elegance, restraint, and aesthetic alignment.

Tone Restrictions: Avoid words like lavish, majestic, unforgettable, memorable, grand clichés, overhype, slang, or robotic phrasing.

Writing Approach: Use subtle imagery, gentle symbolism, and cultural touchstones to convey refinement without loudness.

Operational Note: High-demand venue with peak-season bookings; early reservations are recommended.

Goal: Position Chakolas Pavilion as a venue of quiet distinction—where gatherings unfold with precision, beauty, and understated luxury."""
    },
    44872946: {
        "name": "Dito",
        "card_table_id": 9304562627,
        "brand_context": """Background: DIT’O is a modern beverage solutions brand combining India’s filter coffee heritage with precision engineering to deliver fast, hygienic, and consistent coffee at scale.

Brand Essence: Traditional taste, engineered for speed, hygiene, and zero manual effort.

Product Offering: Automated filter coffee machines designed for high-volume environments, delivering taste-accurate output with minimal human intervention.

Key Benefits: Fast dispensing, hygienic operation, consistent taste, high-volume capacity, operational reliability, and reduced manpower dependency.

Use Cases: Hotels, cafés, buffets, room service, offices, airports, hospitals, transit hubs, colleges, universities, and institutional facilities.

Audience: HoReCa owners, chefs, F&B managers, café operators, office administrators, HR and workplace managers, facility heads, and institutional decision-makers.

Tone: Direct, sharp, performance-driven, and conversion-focused.

Communication Style: Product-first and solution-oriented, using short sentences and clear functional benefits with no storytelling or filler.

Visual Direction: Machines in action, clean outputs, hygienic setups, and high-footfall usage scenarios.

Trends: Allowed only if they reinforce speed, efficiency, hygiene, and performance.

Language: Clear, concise English (and approved regional languages if required), written for Meta and Google Ads performance.

Goal: Position DIT’O as the most reliable high-performance beverage machine brand by highlighting speed, hygiene, consistency, zero manual effort, and measurable operational efficiency."""},
    33660253: {
        "name": "Geojit",
        "card_table_id": 6378073817,
        "brand_context": """Background: Geojit is a leading Indian investment services company with a strong presence across India and GCC countries, serving over a million clients with decades of trusted financial expertise.

Brand Essence: A transparent, compliant, and client-first financial partner enabling responsible investing across life stages.

Experience & Offerings: Mutual fund and insurance distribution, equities, derivatives, commodities, PMS, goal-based financial planning, and advanced digital investment platforms supported by branches, online portals, and customer care.

Audience: First-time investors seeking guided understanding, existing investors exploring broader services, professionals planning early retirement, retirees, and individuals seeking reliable investment support.

Tone: Educational, factual, empowering, friendly, and trustworthy—never fear-driven or salesy.

Communication Style: Education-first and product-supported, using simple explanations of investment concepts while maintaining accuracy, clarity, and regulatory discipline.

Content Focus: Transparency, compliance, expert guidance, diversified solutions, digital tools, and multi-channel accessibility.

Visual Direction: Clean, professional visuals showcasing real platforms, dashboards, tools, and practical investment use cases.

Trends: Light engagement formats allowed only if informative, compliant, and professional; no memes, clickbait, or urgency tactics.

Compliance Rules: Strict adherence to RBI, SEBI, and mutual fund advertising regulations; mandatory disclaimers where required; no guarantees, performance promises, or misleading claims.

Restrictions: Never guarantee returns, create fear-based narratives, exaggerate outcomes, or imply assured profits.

Language: Clear, professional English (and approved regional languages if applicable), with no slang or emotional manipulation.

Goal: Position Geojit as a safe, compliant, and trustworthy investment partner that builds confidence through education, clarity, and responsible financial communication."""
    },
    
    44358469: {
        "name": "Happy Hens",
        "card_table_id": 9169106524,
        "brand_context": """Background: Happy Hens is an ethics-driven, natural-farming egg brand founded by Manjunath M and Ashok Kannan, focused on nutritional integrity, biodiversity-friendly practices, and responsible production.

Audience: Fitness-focused consumers, high-income and quality-conscious buyers, and individuals addressing protein, Vitamin D, and Vitamin B12 nutritional needs.

Tone: Scientific, intelligent, premium, and ad-ready, with zero clichés, no poetic filler, and no exaggerated claims.

Communication Style: Fact-driven and product-first, using accurate nutrition science (bioavailability, amino acid profile, micronutrient density, HDL relevance) in clear, concise language.

Product Positioning: Happy Hens eggs deliver high protein digestibility, strong micronutrient density, and cleaner nutrition through ethical hen-raising, supporting strength training, recovery, and daily nutritional balance.

Content Rules: Every message must state a clear, verifiable nutritional benefit; generic terms like “healthy eggs” are not allowed.

Trends & Formats: Trends, memes, and high-conversion Meta/Google Ads are allowed only when facts remain accurate and compliant.

Restrictions: No medical claims, cures, emotional manipulation, vague adjectives, unrealistic promises, or non-scientific statements.

QC Standard: Reject any content that is generic, unverified, emotionally driven, or scientifically incorrect.

Goal: Position Happy Hens as a premium, nutrition-forward egg brand trusted by informed consumers for ethical sourcing and measurable nutritional value."""
    },
    40447220: {
        "name": "Incheon Kia",
        "card_table_id": 9221243664,
        "brand_context": """Background: Incheon Kia is a leading Kia dealership network in Kerala with multiple showrooms, advanced service workshops, and Certified Pre-Owned outlets, recognised for ISO-certified quality and environmental standards and award-winning dealership excellence.

Brand Essence: Trust-led automotive retail built on quality systems, service precision, and customer experience.

Experience & Offerings: Modern Kia showrooms, high-tech workshops with certified technicians, structured service processes, and a transparent Certified Pre-Owned program.

Audience: Premium car buyers in Kerala, urban professionals, families seeking dependable and feature-rich vehicles, and first-time or upgrade buyers who value trust and service quality.

Tone: Premium, clear, informative, professional, and customer-first.

Communication Style: Product- and service-focused with factual accuracy, clarity, and zero exaggeration.

Content Focus: Vehicle features, safety and technology highlights, service reliability, ISO standards, sustainability focus, and award credentials.

Visual Direction: Clean, premium visuals showcasing vehicles, showrooms, service quality, and customer experience.

Restrictions: Never use overclaims (e.g., best ever, guaranteed, zero maintenance), misleading performance or safety statements, false delivery/mileage promises, slang, memes, or casual humour.

Compliance: Ensure accurate feature representation and adherence to automotive communication norms at all times.

Goal: Position Incheon Kia as Kerala’s most trusted Kia dealership network by consistently reinforcing quality, reliability, service excellence, and transparent customer experience."""
    },
    
    43584998: {
        "name": "Me n Moms",
        "card_table_id": 8981389456,
        "brand_context": """Background: Founded in 1994 by Mr. Naresh Khatar, Me N Moms is a leading Indian babycare and parenting brand with 100+ stores nationwide, supporting parents through the baby’s foundation years (0–3 years).

Brand Essence: Safe, trusted, and science-backed babycare designed to make early parenting easier and more confident.

Product Portfolio: Babycare essentials across feeding, hygiene, travel, nursery, toys, fashion, and maternity, led by the in-house brand Mee Mee.

Proof Points: 100+ PAN-India stores, 10,000+ retail partners, products tested to ASTM, EN, and BIS standards, child-safe materials, and innovative designs.

Audience: New parents, expecting mothers, gift buyers, and middle-income to premium families seeking certified, safe, and affordable baby products.

Tone: Warm, empathetic, parent-first, trustworthy, and reassuring—never fear-driven.

Communication Style: Clear, product- and safety-focused, benefit-led, and easy to understand, optimized for high-conversion Meta and Google Ads.

Content Focus: Product safety, certifications, baby-friendly materials, practical benefits, and everyday parenting convenience.

Visual Direction: Products must be shown clearly and accurately, with clean, family-friendly visuals.

Trends: Allowed only when factual, safe, and appropriate for babycare categories.

Restrictions: No medical claims, fear-based messaging, overpromising, exaggerated language, or guarantees.

CTA Guidance: Always include clear CTAs such as Shop Now, Learn More, or Visit Store.

QC Standard: Every creative must show the product clearly, highlight benefits simply, mention safety/certifications when relevant, remain emotionally warm but practical, and follow Meta/Google ad best practices.

Goal: Position Me N Moms as India’s most trusted one-stop babycare brand by reinforcing safety, certification, convenience, and parental confidence."""
    },
    44319946: {
        "name": "Mother's Food",
        "card_table_id": 9159425873,
        "brand_context": """Background: Mother’s Foods is a 50-year heritage FMCG brand from Kerala, trusted for pure, home-style food products made with natural ingredients, honest processing, and modern hygiene standards.

Brand Essence: Tradition-led purity, family trust, and everyday food made with care.

Audience: Health-conscious families, homemakers, urban professionals, wellness-oriented consumers, culture-rooted buyers, and NRIs seeking authentic Kerala purity and clean-label foods.

Tone: Warm, trustworthy, family-oriented, and culturally rooted—never dramatic, fear-based, or medical.

Communication Style: Simple, clean, and honest, focusing on purity, natural ingredients, consistency, and home-style care.

Content Focus: Ingredient transparency, traditional values (used sparingly), hygiene standards, and everyday reliability.

Claims & Compliance: Use preservative-free or natural claims only when factually applicable; avoid exaggeration, miracle claims, medical statements, or false nutritional messaging.

Visual Direction: Clean, homely, fresh visuals that align with natural, honest, and hygienic food values.

Restrictions: No misleading health claims, no fear-based language, no over-commercial tone, and no inaccurate ingredient assertions.

QC Standard: Every creative must accurately reflect purity and ingredients, maintain a warm family tone, use heritage responsibly, and align visuals and words with freshness, hygiene, and honesty.

Goal: Position Mother’s Foods as a trusted Kerala heritage brand delivering pure, natural, and dependable everyday foods rooted in tradition and care."""
    },
    44944277: {
        "name": "Pulimoottil",
        "card_table_id": 9324174080,
        "brand_context": """Background: Pulimoottil Silks is a 100-year legacy apparel brand from Kerala with six large-format showrooms, offering premium-quality, tradition-rooted, and innovative clothing collections in an elegant, family-friendly shopping environment.

Brand Essence: Heritage, trust, uncompromising quality, and culturally rooted elegance in apparel.

Audience: Brides and wedding families, NRKs, fashion-conscious youth, homemakers, festive shoppers, and value-driven families seeking premium-quality, trusted heritage clothing.

Tone: Premium, warm, family-friendly, elegant, festive, and tradition-forward; never slangy or meme-like.

Communication Style: Clear, culturally sophisticated, and quality-focused, highlighting legacy, service, and authentic silk craftsmanship.

Content Focus: Pure silk / Silk Mark, bridal wear, family shopping, premium collections, showroom experience, and Kerala-rooted elegance.

Visual Direction: Grand, festive, premium, and culturally resonant; highlighting silk, bridal, and family collections in elegant store settings.

Restrictions: Avoid unrealistic offers, overclaims, low-price positioning, slang, memes, or cheap-sales tonality.

QC Standard: Verify accurate representation of legacy, quality, silk purity, collection relevance, store details, and premium, family-oriented tone.

Goal: Position Pulimoottil Silks as Kerala’s trusted century-old apparel brand delivering premium, culturally rooted, and family-focused shopping experiences."""
    },
    34803430: {
        "name": "Zeiq Consultants",
        "card_table_id": 6662918066,
        "brand_context": """Background: Zeiq is a premier German language training and abroad education consultancy in Kerala, delivering transparent guidance, personalized support, and high-quality language coaching, with 100+ completed batches and 1,000+ students placed globally.

Brand Essence: Trusted, student-focused, and results-oriented language and abroad education support.

Audience: Students aiming for Germany and other countries, young professionals, parents seeking reliable institutes, career-builders, and individuals pursuing certified language skills and authentic abroad guidance.

Tone: Friendly, motivating, educational, slightly humorous, direct, positive, and supportive.

Communication Style: Trend- and moment-friendly, student-centric, clear, and confident; emphasizes trust, affordability, experienced trainers, and tangible student outcomes.

Content Focus: Language coaching quality, abroad guidance, student support, Zeiq’s credibility, and the “Why choose Zeiq” value proposition.

Visual Direction: Neat, student-focused visuals with clear hierarchy and emphasis on learning outcomes.

Restrictions: Never belittle students or countries, never exaggerate or promise guaranteed visas/admissions, humor must be respectful and educational.

QC Standard: Verify respectful tone, accurate representation of training and abroad services, clear value messaging, and proper student-centric visual hierarchy.

Goal: Position Zeiq as Kerala’s most trusted German language and abroad education consultancy, highlighting credibility, quality, and student success."""
    },
        34803430: {
        "name": "Zeiq Consultants",
        "card_table_id": 9238571731,
        "brand_context": """Background: Zeiq is a premier German language training and abroad education consultancy in Kerala, offering transparent guidance, personalized support, and high-quality language coaching with 100+ completed batches and 1,000+ students placed globally.

Brand Essence: Trusted, student-focused, outcome-oriented language and abroad education.

Audience: Students aiming for Germany and other countries, young professionals, parents seeking reliable institutes, career-builders, and learners seeking certified language skills and authentic abroad guidance.

Tone: Friendly, motivating, educational, slightly humorous, direct, positive, and supportive.

Communication Style: Trend- and moment-friendly, student-centric, clear, concise, and confidence-inspiring; emphasizes trust, affordability, experienced trainers, and tangible outcomes.

Content Focus: Language training quality, German certifications (A1–C1), placement support, Zeiq’s credibility, and “Why choose Zeiq” as the USP.

High-Conversion Ad Guidelines: Short, sharp headlines (30–40 chars), clear USP, strong CTA (Enroll Now, Book Free Counselling, Join Today), outcomes-focused, no misleading visa or placement promises, professional and accurate messaging.

Visual Direction: Clean, student-focused visuals with clear hierarchy, trend integration allowed if relevant, respecting platform policies.

Restrictions: Never belittle students or countries; humor must be educative and respectful; no exaggerated or false claims; maintain trust, professionalism, and accuracy.

QC Standard: Verify instant headline hook, crisp conversion-focused messaging, visible USP, strong CTA, respectful tone, trend relevance, platform compliance, and clear Meta ad visual hierarchy.

Goal: Position Zeiq as Kerala’s most trusted German language and abroad education consultancy, driving enrollments through credibility, quality, affordability, and demonstrable student success."""
    },
}

@dataclass
class QCTask:
    """Represents a single QC task"""
    comment_id: int
    project_id: int
    card_id: int
    content: str
    urls: list
    brand_context: str
    full_context: str
    timestamp: float

# Global queue and processing state
qc_queue = Queue()
processing_lock = threading.Lock()
is_processing = False
current_task: Optional[QCTask] = None

# Lazy initialization of Groq client
def get_groq_client():
    """Initialize Groq client lazily to avoid errors if API key is missing"""
    if not hasattr(get_groq_client, 'client'):
        get_groq_client.client = Groq(api_key=CONFIG["GROQ_API_KEY"])
    return get_groq_client.client

# Queue system
access_token = None
processed_comments = set()
IMAGE_BASE_DIR = "qc_images"

# Create base image directory
os.makedirs(IMAGE_BASE_DIR, exist_ok=True)
def get_access_token():
    global access_token
    try:
        r = requests.post(
            "https://launchpad.37signals.com/authorization/token",
            data={
                "type": "refresh",
                "client_id": CONFIG["CLIENT_ID"],
                "client_secret": CONFIG["CLIENT_SECRET"],
                "refresh_token": CONFIG["REFRESH_TOKEN"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        if r.ok:
            access_token = r.json()["access_token"]
            print(f"✓ Token refreshed @ {datetime.now().strftime('%H:%M:%S')}")
            return access_token
        else:
            print(f"✗ Token refresh failed: {r.status_code}")
    except Exception as e:
        print(f"✗ Token error: {e}")
    return None

# ==================== PROJECT UTILITIES ====================
def get_project_config(project_id):
    """Get project configuration by ID"""
    return PROJECTS.get(project_id)

def get_project_image_path(project_id):
    """Get project-specific image path"""
    project_config = get_project_config(project_id)
    if not project_config:
        return os.path.join(IMAGE_BASE_DIR, f"project_{project_id}_temp.jpg")
    
    # Create project-specific folder
    project_name = project_config["name"].replace(" ", "_").lower()
    project_folder = os.path.join(IMAGE_BASE_DIR, project_name)
    os.makedirs(project_folder, exist_ok=True)
    
    return os.path.join(project_folder, "latest_qc_image.jpg")

# ==================== UTILITIES ====================
def strip_html(html):
    """Remove HTML tags and normalize whitespace"""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()

def extract_urls(text):
    """Extract URLs from text - PRESERVES CASE for Drive IDs"""
    return re.findall(r"https?://[^\s<>\"{}|\\^`\[\]]+", text)

# ==================== GOOGLE DRIVE DOWNLOAD ====================
def download_image_to_disk(url, save_path):
    """Downloads image from Google Drive with virus scan bypass"""
    try:
        if "drive.google.com" not in url:
            print("✗ Not a Google Drive URL")
            return None

        # Extract file ID - PRESERVE CASE!
        fid = None
        if "/d/" in url:
            fid = url.split("/d/")[1].split("/")[0].split("?")[0]
        elif "id=" in url:
            fid = url.split("id=")[1].split("&")[0]
        
        if not fid:
            print("✗ Could not extract file ID from URL")
            return None

        print(f"📁 File ID: {fid}")

        # Direct download URL
        download_url = f"https://drive.google.com/uc?export=download&id={fid}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        session = requests.Session()
        print(f"⬇️  Downloading: {download_url}")
        
        # First request
        response = session.get(download_url, headers=headers, stream=True, timeout=60)
        content_type = response.headers.get("Content-Type", "")
        
        # Check if we hit the virus scan warning page
        if "text/html" in content_type and response.status_code == 200:
            print("⚠️  Got HTML (virus scan page), looking for confirm token...")
            
            patterns = [
                r'id="uc-download-link"[^>]*href="([^"]*)"',
                r'confirm=([0-9A-Za-z_-]+)',
                r'download_warning[^>]*value="([^"]*)"',
                r'uuid=([0-9A-Za-z_-]+)',
                r'&amp;confirm=([0-9A-Za-z_-]+)'
            ]
            
            confirm_token = None
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    if 'href=' in pattern:
                        href = match.group(1).replace('&amp;', '&')
                        confirm_match = re.search(r'confirm=([^&]+)', href)
                        if confirm_match:
                            confirm_token = confirm_match.group(1)
                    else:
                        confirm_token = match.group(1)
                    
                    if confirm_token:
                        print(f"🔑 Found confirm token: {confirm_token}")
                        break
            
            if confirm_token:
                download_url = f"https://drive.google.com/uc?export=download&id={fid}&confirm={confirm_token}"
                print(f"🔄 Retrying with confirm token...")
                response = session.get(download_url, headers=headers, stream=True, timeout=60)
                content_type = response.headers.get("Content-Type", "")
        
        print(f"📊 Status: {response.status_code}, Type: {content_type}")
        
        if response.status_code == 200:
            if os.path.exists(save_path):
                os.remove(save_path)
                print(f"🗑️  Deleted old image")
            
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"💾 Saved as: {save_path}")
            
            try:
                img = Image.open(save_path)
                print(f"✅ Valid image: {img.size[0]}x{img.size[1]} {img.mode}")
                return img
            except Exception as e:
                print(f"✗ Not a valid image: {e}")
                return None
        
        elif response.status_code == 404:
            print("=" * 60)
            print("❌ ERROR 404 - FILE NOT FOUND")
            print(f"📋 File ID: {fid}")
            print("=" * 60)
            return None
        
        else:
            print(f"✗ HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ Download exception: {type(e).__name__}: {e}")
        traceback.print_exc()
    
    return None

def download_image_with_auth(url, token, save_path):
    """Download image from Basecamp attachment"""
    try:
        r = requests.get(
            url, 
            headers={"Authorization": f"Bearer {token}"}, 
            timeout=30
        )
        if r.status_code == 200:
            if os.path.exists(save_path):
                os.remove(save_path)
                print(f"🗑️  Deleted old image")
            
            with open(save_path, "wb") as f:
                f.write(r.content)
            
            img = Image.open(save_path)
            print(f"✅ Downloaded from Basecamp: {img.size[0]}x{img.size[1]}")
            return img
    except Exception as e:
        print(f"✗ Basecamp download failed: {e}")
    return None
# ==================== GROQ VISION QC ====================
# ==================== HUGGING FACE VISION QC ====================
def perform_image_qc_with_huggingface(image: Image.Image, brand_context: str = "") -> str:
    """Perform visual QC using Hugging Face's Llama Vision model"""
    try:
        w, h = image.size
        print(f"🤖 Sending to Hugging Face Llama Vision...")
        print(f"   Original Image: {w}x{h}px")
        
        # Resize if needed
        max_size = 1024
        if w > max_size or h > max_size:
            if w > h:
                new_w = max_size
                new_h = int(h * (max_size / w))
            else:
                new_h = max_size
                new_w = int(w * (max_size / h))
            
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            print(f"   Resized to: {new_w}x{new_h}px")
        
        # Save with compression
        from io import BytesIO
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)
        
        file_size = len(buffer.getvalue())
        print(f"   Compressed size: {file_size / 1024:.1f} KB")
        
        # Encode to base64
        import base64
        img_data = base64.b64encode(buffer.getvalue()).decode()
        image_url = f"data:image/jpeg;base64,{img_data}"
        
        brand_section = f"\n**Brand Context:**\n{brand_context}\n" if brand_context else ""
        
        prompt = f"""You are a Senior Visual QC Analyst specializing in digital and print advertising with 20 years of experience. Your feedback must be specific, consistent, actionable, and thorough.Analyze objectively—catch real errors but don't invent issues.

═══════════════════════════════════════════════════
IMAGE SPECIFICATIONS
═══════════════════════════════════════════════════
Image Details: {image.size[0]}×{image.size[1]}px
Format Type: [Auto-detect: Social Media Ad / Display Banner / Print Material]
{brand_section}
═══════════════════════════════════════════════════
🚨 STEP 1: BRAND VERIFICATION (DO THIS FIRST!)
═══════════════════════════════════════════════════
CRITICAL: Look at the image. What brand logo/name do you see?

Check logo text, brand name, company name visible
Compare to brand context above

IF THE BRANDS DON'T MATCH:
Stop immediately and output ONLY this:

APPROVAL STATUS: 🚨 BLOCKED - BRAND MISMATCH
Image shows: [Brand name visible in image]
Context expects: [Brand name from brand context]
Action: Verify you're in the correct project/card table. Do not proceed with QC until brand match is confirmed.
DO NOT analyze further if brands don't match. END HERE.

STEP 2: IF BRAND MATCHES, PROCEED WITH QC
═══════════════════════════════════════════════════
YOUR CORE MISSION
═══════════════════════════════════════════════════
Catch every error before launch. Be the last line of defense. Your job is to:

FIRST: Verify brand match (logo, name, products vs brand context)
Identify BLOCKER issues that prevent approval
Spot HIGH PRIORITY issues that need fixing
Note MEDIUM PRIORITY improvements
Provide specific, actionable feedback with exact fixes
Score fairly with transparent math

═══════════════════════════════════════════════════
CRITICAL ERROR CATEGORIES (NEVER MISS THESE)
═══════════════════════════════════════════════════
🚨 BLOCKER ISSUES (Must fix before approval):

Brand Mismatch: Wrong brand entirely (auto-reject)
Grammar/Spelling: Errors in headline, CTA, body copy, or product names
Logo Issues: Wrong version, distorted, illegible, missing
Critical Info Errors: Wrong prices, dates, phone numbers, URLs
Broken Layout: Text cut off, major alignment collapse
Illegible Text: Poor contrast, too small (<8pt), overlapped
Non-Functional Elements: Dead links, missing CTA

⚠️ HIGH PRIORITY (Fix before launch):

Minor Grammar: Secondary text errors
Brand Deviation: Off-brand colors (not exact hex), wrong fonts
Visual Hierarchy: Wrong element emphasized (CTA buried, headline lost)
Image Quality: Pixelation, blur, compression artifacts
Weak CTA: Generic wording ("Click Here"), poor visibility
Inconsistent Style: Mixed fonts, spacing, alignment issues

📋 MEDIUM PRIORITY (Should improve):

Polish Issues: Minor spacing, subtle alignment tweaks
Optimization: CTA could be stronger, flow could improve
Enhancement: Color adjustments, hierarchy refinements

═══════════════════════════════════════════════════
ANALYSIS STRUCTURE (Exactly 5 Sections)
═══════════════════════════════════════════════════
SECTION 1: TOP AREA - LOGO/BRANDING/HEADER
Inspect top 25% of creative:
✓ Logo Quality:

Correct version (check against brand guidelines)
Not stretched, squished, or distorted
Proper clear space (minimum 2x logo height around it)
High resolution (no pixelation)
Correct colors (exact hex codes if specified)
✓ Brand Name:
Correct spelling and capitalization
Proper trademark symbols (®, ™, ©)
✓ Header/Tagline:
Grammar and spelling perfect
Proper punctuation
Alignment consistent

SECTION 2: COPY QUALITY & CONTENT
Analyze ALL text elements:
✓ Headline:

Zero grammar/spelling errors
Clear, compelling message
Appropriate length for platform
Proper capitalization (Title Case vs Sentence case)
✓ Body Copy:
Grammar, punctuation, spelling flawless
Tone matches brand voice (formal/casual/friendly)
Message clarity (no jargon unless brand-appropriate)
Logical flow and structure
✓ Product/Offer Details:
Accurate information (prices, dates, specs)
No misleading claims
Legal compliance (disclaimers present if needed)
✓ Special Characters:
Proper apostrophes (not straight quotes)
Em dashes (—) vs hyphens (-)
Currency symbols correct
✓ Language-Specific:
If Malayalam/Manglish: Verify script accuracy, no broken Unicode
Mixed language: Consistent font support for all characters

⚠️ ALWAYS quote exact problematic text in "quotes"
SECTION 3: DESIGN & VISUAL QUALITY
Evaluate visual execution:
✓ Layout & Composition:

Organized grid system or intentional asymmetry
Visual balance (not top/bottom heavy)
Professional appearance
White space used effectively (not cramped)
✓ Visual Hierarchy:
Eye flow: Headline → Key Visual → CTA
Size relationships correct (most important = largest)
Contrast guides attention properly
✓ Image Quality:
High resolution (zoom to check for pixelation)
Sharp focus on key elements
No compression artifacts
Colors vibrant and accurate
✓ Alignment & Spacing:
Elements properly aligned (left/center/right consistent)
Consistent padding and margins
Text not touching edges (minimum 10px margin)
Even spacing between elements
✓ Color Usage:
On-brand palette (verify against guidelines)
Sufficient contrast (WCAG AA: 4.5:1 for text)
No color clashes
Accessible for colorblind users if applicable
✓ Typography:
Correct brand fonts
Consistent font weights
Readable sizes (body: 12-14pt minimum, headline: 20pt+ minimum)
Line height comfortable (1.4-1.6)
No more than 3 font families

SECTION 4: CTA & FOOTER ELEMENTS
Check bottom 25% and conversion elements:
✓ CTA Button/Text:

Action verb present (Shop, Buy, Learn, Book, Join, Start)
NOT generic ("Click Here", "Submit", "Enter")
Visually prominent (contrasting color, adequate size)
Easy to find (not buried in design)
Logical placement in visual flow
✓ Contact Information:
Phone: Correct format, no typos
Email: Valid format, correct domain
Website: Correct URL, includes https://
Address: Complete and accurate
✓ Footer Elements:
Legal disclaimers readable (minimum 8pt)
Social media handles correct (@username format)
Copyright notice present if required
Terms/conditions linked if applicable
✓ Platform-Specific:
Safe zones respected (no text in Instagram story corners)
Aspect ratio correct for platform

SECTION 5: OVERALL BRAND CONSISTENCY
Final brand compliance check:
✓ Logo Implementation:

Matches approved brand guidelines 100%
Correct color variant (full color vs monochrome)
Proper lockup if using tagline
✓ Color System:
Primary colors match exact hex codes
Secondary colors used appropriately
No unauthorized colors introduced
✓ Typography System:
Correct primary font (headlines)
Correct secondary font (body)
Proper hierarchy (H1, H2, body sizes)
✓ Overall Polish:
Professional, finished appearance
No placeholder content
Consistent style throughout
✓ Format Specifications:
Correct dimensions for intended platform
File size appropriate (not too large for web)

═══════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT (Copy Exactly)
═══════════════════════════════════════════════════
VISUAL QC ANALYSIS REPORT
Image Dimensions: {image.size[0]}×{image.size[1]}px
Detected Format: [Instagram Post / Facebook Ad / etc.]
───────────────────────────────────────────────────
SECTION 1: TOP AREA - LOGO/BRANDING/HEADER
───────────────────────────────────────────────────
STATUS: [✓ ALL CLEAR / ⚠️ ISSUES FOUND]
[If no issues:] ✓ No issue All clear

[If issues found:]
✗ ISSUES FOUND:

[BLOCKER] - [Issue Title]
Location: [Specific position: "Top-left corner" / "Center header"]
Current State: "[Quote or describe what's wrong]"
Problem: [Detailed explanation - why is this wrong?]

[HIGH] - [Issue Title]
Location: [Specific area]
Problem: [What's wrong]

[MEDIUM] - [Issue Title]
Location: [Specific area]
Problem: [What could be better]

───────────────────────────────────────────────────
SECTION 2: COPY QUALITY & CONTENT
───────────────────────────────────────────────────
STATUS: [✓ ALL CLEAR / ⚠️ ISSUES FOUND]
[If no issues:] ✓ No issue All clear

[If issues found:]
✗ ISSUES FOUND:

[BLOCKER] - [Issue Title: Grammar Error / Spelling Mistake / etc.]
Location: [Headline / Body Copy / CTA / Product Name]
Current Text: "[Quote EXACT text with error highlighted]"
Problem: [Grammar rule violated / Spelling error / Clarity issue]

[HIGH] - [Issue Title]
Current Text: "[Quote problematic text]"
Problem: [Weak messaging / Off-brand tone / Unclear phrasing]

[MEDIUM] - [Issue Title]
Current: "[Quote text]"

───────────────────────────────────────────────────
SECTION 3: DESIGN & VISUAL QUALITY
───────────────────────────────────────────────────
STATUS: [✓ ALL CLEAR / ⚠️ ISSUES FOUND]
[If no issues:] ✓ No issue All clear

[If issues found:]
✗ ISSUES FOUND:

[BLOCKER] - [Issue Title]
Element: [Specific design component: "Product image" / "Background" / "Text block"]
Problem: [Alignment off / Pixelation / Poor contrast / Spacing issue]

[HIGH] - [Issue Title]
Element: [Design component]
Problem: [What's wrong with hierarchy/quality/style]

[MEDIUM] - [Issue Title]
Element: [Component]
Enhancement: [How to polish]

───────────────────────────────────────────────────
SECTION 4: CTA & FOOTER ELEMENTS
───────────────────────────────────────────────────
STATUS: [✓ ALL CLEAR / ⚠️ ISSUES FOUND]
[If no issues:] ✓ No issue All clear

[If issues found:]
✗ ISSUES FOUND:

[BLOCKER] - [Issue Title]
Element: [CTA Button / Phone Number / URL / etc.]
Current: "[Quote exact text or describe element]"
Problem: [Not action-oriented / Incorrect info / Poor visibility / Missing]

[HIGH] - [Issue Title]
Current: "[Quote CTA or footer text]"
Problem: [Weakness identified]

[MEDIUM] - [Issue Title]
Suggestion: [Enhancement idea]
Benefit: [Improvement gained]

Overall Consistency:

[✓ Fully aligned with brand guidelines]
[⚠️ Minor deviations: List them]
[✗ Major inconsistencies: Detail them]

FIX NEEDED: [What corrections required] OR "None - brand consistency excellent"
═══════════════════════════════════════════════════
PERFORMANCE RATINGS & SCORING BREAKDOWN
═══════════════════════════════════════════════════
📝 COPY QUALITY: [X]/10
Calculation:

Base Score: 10/10
Deduction: -[X] pts → [Specific issue: "Headline grammar error: 'their' should be 'there'"]
Deduction: -[X] pts → [Specific issue: "Body copy typo: 'recieve' → 'receive'"]
Deduction: -[X] pts → [If applicable]
Final Score: [X]/10
Grade: [Excellent 9-10 / Good 7-8 / Needs Work 5-6 / Poor 3-4 / Critical 0-2]
Assessment: [1-2 sentence summary of copy quality state]

🎨 DESIGN & LAYOUT: [X]/10
Calculation:

Base Score: 10/10
Deduction: -[X] pts → [Specific issue: "Poor visual hierarchy - CTA not prominent"]
Deduction: -[X] pts → [Specific issue: "Product image pixelated in center"]
Deduction: -[X] pts → [If applicable]
Final Score: [X]/10
Grade: [Rating category]
Assessment: [Brief design quality summary]

🎯 CTA EFFECTIVENESS: [X]/10
Calculation:

Base Score: 10/10
Deduction: -[X] pts → [Specific issue: "Generic CTA text: 'Click Here' instead of action verb"]
Deduction: -[X] pts → [Specific issue: "CTA button low contrast - poor visibility"]
Final Score: [X]/10
Grade: [Rating category]
Assessment: [CTA strength evaluation]

⭐ OVERALL IMPACT: [X]/10
Calculation:

Average of above: ([Copy + Design + CTA] ÷ 3) = [X.X]
Adjustment: [+/-X pts] → [Reason: "Cohesive storytelling boosts impact" / "Multiple issues reduce effectiveness"]
Final Score: [X]/10
Grade: [Rating category]

Holistic Assessment:
[2-3 sentences answering: Does this creative achieve its marketing goal? Would you approve it for launch? Why or why not? What's the biggest strength and biggest weakness?]
═══════════════════════════════════════════════════
PRIORITY ACTION ITEMS
═══════════════════════════════════════════════════
🚨 CRITICAL (Must Fix Before Approval):

[Most critical blocker - exact issue and fix]
[Second blocker if exists]
[Third blocker if exists]
[If no blockers: "None - no blocking issues identified"]

⚠️ HIGH PRIORITY (Should Fix Before Launch):

[Most important high-priority issue with fix]
[Second high-priority issue]
[Third if exists]
[If none: "None - quality meets launch standards"]

📋 RECOMMENDED IMPROVEMENTS:

[Best medium-priority enhancement]
[Second polish suggestion]
[Third if applicable]
[If none: "None - creative is well-polished"]

═══════════════════════════════════════════════════
APPROVAL STATUS
═══════════════════════════════════════════════════
STATUS: [Select ONE:]
🚨 BLOCKED - BRAND MISMATCH

Reason: This creative shows [Brand X visible in image] but the brand context indicates this should be for [Brand Y from context].
Action Required: Verify correct project/card table. Do not proceed with this creative.
Note: Detailed analysis skipped due to brand mismatch.

🚫 BLOCKED

Reason: [X] critical issues must be fixed before approval
Blockers: [List critical issues preventing approval]
Next Steps: Address all blocking issues and resubmit for QC

⚠️ NEEDS REVISION

Reason: [X] high-priority issues affect quality
Required Fixes: [List high-priority items]
Timeline: Should be fixed before launch
Status After Fixes: Will be approved once addressed

✅ APPROVED WITH NOTES

Status: Ready for production with minor improvements suggested
Optional Enhancements: [List medium-priority suggestions]
Timeline: Can launch now, implement suggestions in future versions

✅ APPROVED

Status: Excellent quality - ready for immediate launch
Strengths: [List 2-3 key strengths]
Notes: No changes required

STATUS LOGIC:

BLOCKED - BRAND MISMATCH: Wrong brand entirely (logo/name/products don't match context)
BLOCKED: Any grammar errors OR critical logo/layout/info errors
NEEDS REVISION: Multiple high-priority issues affecting quality
APPROVED WITH NOTES: Minor improvements suggested but not required
APPROVED: Professional, error-free, ready to launch

═══════════════════════════════════════════════════
STRICT SCORING SYSTEM
═══════════════════════════════════════════════════
START EVERY CATEGORY AT 10/10, THEN DEDUCT POINTS:
📝 COPY QUALITY DEDUCTIONS:

-3 points: Grammar or spelling error in HEADLINE or CTA (high visibility)
-2 points: Grammar or spelling error in BODY COPY or product descriptions
-2 points: Incorrect product name, price, or critical information
-1 point: Awkward phrasing, unclear message, or confusing structure
-1 point: Inconsistent capitalization or punctuation
-1 point: Off-brand tone (too casual/formal for brand)
-1 point: Missing key information or call-to-action

🎨 DESIGN & LAYOUT DEDUCTIONS:

-3 points: Major alignment failure or broken layout structure
-3 points: Text cut off or major readability issues
-2 points: Poor visual hierarchy (wrong element emphasized/CTA buried)
-2 points: Pixelated, blurry, or low-resolution images
-2 points: Severe color contrast issues (text unreadable)
-1 point: Minor spacing inconsistencies between elements
-1 point: Subtle alignment issues (not catastrophic)
-1 point: Weak visual balance or composition
-1 point: Too many fonts or colors (visual clutter)

🎯 CTA EFFECTIVENESS DEDUCTIONS:

-3 points: CTA missing entirely or completely hidden
-3 points: Critical contact information wrong (phone, URL)
-2 points: CTA uses generic weak wording ("Click Here", "Submit", "Enter")
-2 points: CTA poor visibility (low contrast, too small, buried)
-2 points: CTA placement illogical in visual flow
-1 point: CTA could be more action-oriented (good but not great)
-1 point: Multiple competing CTAs causing confusion

⭐ OVERALL IMPACT CALCULATION:

Calculate average: (Copy + Design + CTA ) ÷ 3
Apply holistic adjustments:

+1 point: Exceptional cohesion, storytelling, or creative execution
0 points: Standard execution, no adjustments needed
-1 point: Multiple small issues compound to reduce overall impact
-2 points: Significant effectiveness concerns despite individual scores



SCORE INTERPRETATION GUIDE:
9-10 → EXCELLENT ✅

Zero or negligible issues
Professional, polished, on-brand
Ready for immediate launch
Example: Minor spacing tweak suggested but not required

7-8 → GOOD ✅

Minor issues present but not critical
Overall quality acceptable
Recommended fixes before launch but not blocking
Example: Small grammar error in body copy, CTA could be stronger

5-6 → NEEDS WORK ⚠️

Multiple issues affecting quality
Revision required before approval
Not ready for launch in current state
Example: Several grammar errors, off-brand colors, weak hierarchy

3-4 → POOR 🚫

Major issues across multiple categories
Significant revision required
Quality below acceptable standards
Example: Headline grammar error, pixelated images, wrong logo

0-2 → CRITICAL 🚫

Severe fundamental problems
Complete rework needed
Cannot be salvaged with minor fixes
Example: Wrong brand entirely, layout broken, multiple critical errors

═══════════════════════════════════════════════════
QUALITY CONTROL RULES - NEVER VIOLATE
═══════════════════════════════════════════════════
✅ ALWAYS DO:

Be hyper-specific: "Top-left logo is pixelated" not "logo has issues"
Quote exact text: For any copy issue, use "quotes" around problematic text
Explain WHY: Every issue must include impact/consequence
Show math: Display every point deduction with reasoning
Balance feedback: Acknowledge strengths AND issues (not just negative)
Categorize severity: Every issue tagged [BLOCKER]/[HIGH]/[MEDIUM]
Provide exact fixes: Not "improve CTA" but "Change 'Click Here' to 'Shop Now'"
Apply consistency: Same error type = same point deduction every time
Consider context: Platform, audience, brand voice in evaluation
Verify brand match: FIRST check if creative matches brand context

❌ NEVER DO:

Vague feedback: "Text needs work" is unacceptable - specify WHAT and WHERE
Miss grammar errors: Read EVERY word - zero tolerance for spelling/grammar mistakes
Inflate scores: Be honest - don't give 8/10 if it's really 5/10
Skip explanations: Never list issues without explaining WHY they matter
Ignore context: Don't apply print standards to social media or vice versa
Overlook logo issues: Brand consistency is CRITICAL - scrutinize logo carefully
Miss image quality: Check for pixelation, blur, compression - zoom in if needed
Forget readability: Check ALL text is legible (contrast, size, background)
Skip contact info: Verify phone, email, URL, address accuracy
Rush the analysis: Take time to check every detail systematically

═══════════════════════════════════════════════════
COMMON ERRORS TO CATCH (EXPANDED)
═══════════════════════════════════════════════════
GRAMMAR TRAPS:

Its vs. It's: "Its" = possessive, "It's" = "it is"
Your vs. You're: "Your" = possessive, "You're" = "you are"
Their/There/They're: Location, possession, "they are"
Affect vs. Effect: Verb vs. noun (usually)
Then vs. Than: Time vs. comparison
Lose vs. Loose: Misplace vs. not tight
Comma splices: Two independent clauses joined with just comma
Missing apostrophes: "Dont" → "Don't", "Its" → "It's"
Inconsistent capitalization: "Digital Marketing" vs "digital marketing"
Serial comma: "A, B, and C" vs "A, B and C" (brand style dependent)

PUNCTUATION ERRORS:

Straight quotes vs. curly quotes: Use "smart quotes" not "dumb quotes"
Apostrophes vs. single quotes: Use ' not ' for possessives
Hyphens vs. en dash vs. em dash: Hyphen (-) for compounds, en dash (–) for ranges, em dash (—) for pauses
Ellipsis: Use … (single character) not ... (three periods)
Spacing: One space after period, not two

BRAND LOGO ISSUES:

Outdated version: Old logo when brand has updated
Wrong color variant: Full color used when monochrome required (or vice versa)
Distortion: Stretched, squished, or disproportionate
Low resolution: Pixelated or blurry logo
Poor clear space: Logo too close to other elements
Wrong lockup: Logo + tagline when should be logo only
Incorrect orientation: Horizontal vs vertical vs stacked

DESIGN RED FLAGS:

Text over busy background: Unreadable text on complex images without overlay
Too many fonts: More than 3 font families in one design
Color chaos: More than 5 colors creating visual noise
Inconsistent alignment: Mixed left/center/right with no clear system
Pixelated images: Low-res images that look fuzzy or jagged
Poor contrast: Text color too similar to background (WCAG fail)
Text cut off: Words or letters touching or crossing image edges
Unbalanced layout: Too much weight on one side, awkward white space
Inconsistent spacing: Random gaps between elements
Clashing colors: Colors that vibrate or create visual discomfort

CTA PROBLEMS:

Generic wording: "Click Here", "Submit", "Enter", "Learn More" (weak verbs)
Not visually prominent: Same size/color as other text, no button treatment
Wrong placement: Bottom corner when eye flows to center
Multiple CTAs: 3+ competing actions causing decision paralysis
No CTA at all: Missing clear next step for user
Passive language: "You can shop" vs. "Shop Now"
Unclear action: "See more" → What will I see? Be specific

CONTACT INFO ERRORS:

Wrong phone format: Missing country code, incorrect spacing
Typo in email: Missing @ or .com, wrong domain
URL errors: Missing https://, www when required, typos in domain
Address incomplete: Missing city, zip code, or state

═══════════════════════════════════════════════════
LANGUAGE-SPECIFIC QC (MULTILINGUAL)
═══════════════════════════════════════════════════
ENGLISH:

Standard grammar rules (subject-verb agreement, tense consistency)
Spell check every word (US vs UK spelling consistency)
Capitalization rules (title case for headlines)

MALAYALAM:

Unicode integrity (no broken characters: ാ� or ്)
Proper conjunct formation (സ്ത not സ + ് + ത)
Consistent font (ensure font supports all Malayalam glyphs)
No romanized Malayalam unless intentional Manglish

MANGLISH (English + Malayalam):

Font must support both scripts seamlessly
Language switching mid-sentence should be intentional, not error
Common Manglish words verified: "നല്ല good", "super ആണ്"
Readability maintained despite code-switching

═══════════════════════════════════════════════════
FINAL CHECKLIST BEFORE SUBMITTING REPORT
═══════════════════════════════════════════════════
VERIFICATION STEPS - COMPLETE EVERY TIME:
☐ 1. Brand Verification (First Priority)

Brand in image matches brand in context
If mismatch: Stop analysis, output BLOCKED - BRAND MISMATCH

☐ 2. Text Accuracy (Zero Tolerance Zone)

Read EVERY word for spelling errors
Check EVERY comma, period, apostrophe
Verify proper names, product names, prices, dates
Confirm phone numbers, emails, URLs are correct

☐ 3. Logo Quality (Brand Critical)

Correct logo version (not outdated)
Not stretched, squished, or distorted
High resolution (zoom to verify)
Proper clear space around it
Right color variant for context

☐ 4. Brand Colors (Exact Match Required)

Colors match brand guidelines (hex codes if provided)
No unauthorized colors introduced
Sufficient contrast for readability

☐ 5. Visual Hierarchy (Eye Flow Check)

Eye naturally flows: Headline → Key Visual → CTA
Most important element is most prominent
CTA stands out and is easy to find

☐ 6. CTA Evaluation (Conversion Critical)

Uses action verb (Shop, Buy, Join, Start, Book)
NOT generic (Click Here, Submit, Enter, Learn More)
Visually prominent (contrasting color, adequate size)
Logical placement in design flow

☐ 7. Image Quality (Professional Standard)

No pixelation or blur (zoom in to check)
Sharp focus on key elements
No compression artifacts
Colors accurate and vibrant

☐ 8. Layout & Alignment (Professional Polish)

Elements aligned consistently
Spacing consistent between elements
Text not touching edges (minimum margins)
Balanced composition

☐ 9. Issue Documentation (Actionable Feedback)

Quoted exact problematic text for copy issues
Explained WHY each issue matters (impact)
Provided specific fixes for every issue
Categorized severity [BLOCKER]/[HIGH]/[MEDIUM]

☐ 10. Scoring Transparency (Show Your Math)

Listed every point deduction with reason
Applied consistent scoring standards
Justified final scores with evidence
Calculated overall impact fairly

☐ 11. Priority Ordering (Clear Action Plan)

Listed critical blockers first
Then high-priority issues
Then recommended improvements
Each with specific fix instructions

☐ 12. Approval Status (Clear Decision)

Selected appropriate status based on issues found
Justified decision with supporting evidence
Provided clear next steps


Writing Economy Tips:
✓ Be precise, not verbose
✓ Use bullet points for clarity
✓ Avoid repetition
✓ Focus on actionable insights
✓ Cut unnecessary words ("in order to" → "to")
✓ Use active voice ("Logo is distorted" not "The logo has been distorted")
Quality over Quantity:

5 specific issues > 10 vague observations
Short, clear sentences > Long, complex paragraphs
Exact fixes > General suggestions

═══════════════════════════════════════════════════
REMEMBER: LAST LINE OF DEFENSE
═══════════════════════════════════════════════════
You are the FINAL checkpoint before this creative goes live to potentially millions of people.
Every error you catch saves:

Brand reputation and credibility
Marketing budget from wasted spend
Customer trust and engagement
Legal issues from incorrect information
Conversion opportunities from poor CTAs

Every error you miss creates:

Embarrassing public mistakes
Lost sales and leads
Damaged brand perception
Costly reprints or re-edits
Lost stakeholder confidence

**NOTE:Be objective dont invent issues**

**REMEMBER:** You are the last line of defense before this creative goes live. Be thorough, be specific, be consistent. Every error you catch saves the brand's reputation and marketing investment.Catch real errors that matter. Don't manufacture issues.

Now analyze the image following this exact structure."""


        completion = get_groq_client().chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        result = completion.choices[0].message.content.strip()
        print(f"✅ Vision QC completed ({len(result)} chars)")
        return result
        
    except Exception as e:
        error_msg = f"Hugging Face Vision API failed: {type(e).__name__}: {e}"
        print(f"✗ {error_msg}")
        traceback.print_exc()
        return error_msg

# ==================== TEXT QC ====================
def perform_text_qc(text, brand_context: str = "", is_reel: bool = False):
    """Perform text-only QC using Groq - Handles both reel scripts and poster copy"""
    try:
        if not text or len(text.strip()) < 10:
            return "⚠️ No content to analyze. Please provide text or an image."
        
        brand_section = f"\n**Brand Context:**\n{brand_context}\n" if brand_context else ""
        
        if is_reel:
            # Reel/Video Script QC Prompt
            prompt = f"""You are a Senior Reel/Video Content QC Analyst specializing in short-form video content for social media. Your feedback must be specific, actionable, and focused on video performance.

═══════════════════════════════════════════════════
BRAND CONTEXT (MUST BE STRICTLY FOLLOWED)
═══════════════════════════════════════════════════
{brand_context}

⚠️ **CRITICAL:** Every aspect of your analysis must verify alignment with the brand context above. Any deviation from brand guidelines, tone, or messaging is a BLOCKER issue.
═══════════════════════════════════════════════════
SCRIPT TO ANALYZE
═══════════════════════════════════════════════════
**Script Length:** {len(text.split())} words
**Estimated Duration:** {len(text.split()) / 2.5:.1f} seconds (at average pace)
{brand_section}
**Script Content:**
"{text}"

═══════════════════════════════════════════════════
YOUR CORE MISSION
═══════════════════════════════════════════════════
Evaluate how this script will perform as a VIDEO. Consider:
1. Will viewers STOP scrolling in the first 3 seconds?
2. Is the pacing right for the platform (Reels/Shorts/TikTok)?
3. Are dialogues natural and easy to deliver on camera?
4. Will on-screen text/captions be readable and timed well?
5. Does the CTA drive clear action?
6. Does it match brand voice while staying engaging?

═══════════════════════════════════════════════════
CRITICAL ERROR CATEGORIES (NEVER MISS THESE)
═══════════════════════════════════════════════════

🚨 BLOCKER ISSUES (Must fix before production):
- **BRAND/SCRIPT MISMATCH:** Script appears to be for a DIFFERENT brand than the one in brand context (wrong brand name, wrong products, wrong industry) - If detected, immediately set PRODUCTION STATUS to "BLOCKED - BRAND MISMATCH" and stop detailed analysis
• Weak or missing hook in first 3 seconds
• Grammar/spelling errors in dialogues or captions
• Script too long for intended platform (>60 sec for Reels)
• Unclear or missing CTA
• Off-brand tone or messaging
• Dialogues that are difficult to pronounce or sound unnatural
• Confusing story flow or scene transitions

⚠️ HIGH PRIORITY (Fix before filming):
• Hook could be stronger
• Pacing too fast or too slow for video format
• Captions/on-screen text unclear or poorly timed
• CTA not prominent or compelling enough
• Dialogues need better flow for video delivery
• Missing key brand elements or messaging
• Scene descriptions vague or incomplete

📋 MEDIUM PRIORITY (Recommended improvements):
• Could use more dynamic visual cues
• Opportunity to add emotional beats
• Caption timing could be optimized
• Could leverage trending formats better
• Minor dialogue refinements for natural delivery

═══════════════════════════════════════════════════
ANALYSIS STRUCTURE (Exactly 5 Categories)
═══════════════════════════════════════════════════

**CATEGORY 1: HOOK & OPENING (25% Weight)**
Analyze:
✓ First 3 seconds: Does it stop the scroll?
✓ Hook strength: Curiosity, shock value, relatability, or problem statement?
✓ Opening line delivery: Natural, attention-grabbing, easy to say?
✓ Visual interest: Does opening scene description set up engagement?

**CATEGORY 2: VISUAL FLOW & PACING (20% Weight)**
Analyze:
✓ Scene transitions: Smooth, logical, and engaging?
✓ Timing: Appropriate pace for platform (not too rushed/slow)?
✓ Visual variety: Different shots, angles, or visual breaks?
✓ Rhythm: Does script have natural beats and pauses?
✓ Length: Appropriate for platform and attention span?

**CATEGORY 3: DIALOGUES & DELIVERY (20% Weight)**
Analyze:
✓ Pronunciation: Easy to say on camera? No tongue-twisters?
✓ Natural flow: Sounds conversational, not scripted?
✓ Clarity: Clear messaging without confusion?
✓ Tone: Matches brand personality?
✓ Energy: Appropriate enthusiasm/emotion for content?

**CATEGORY 4: ON-SCREEN TEXT, CAPTIONS & CTA (20% Weight)**
Analyze:
✓ Caption clarity: Short, readable, and impactful?
✓ Text timing: Appears at right moments in script?
✓ CTA placement: End or strategic points throughout?
✓ CTA clarity: Clear action word (Shop, Follow, Learn More)?
✓ CTA urgency: Creates motivation to act immediately?

**CATEGORY 5: BRAND VOICE & TREND ALIGNMENT (15% Weight)**
Analyze:
✓ Brand consistency: Tone, messaging, and values aligned?
✓ Trend relevance: Uses current formats appropriately?
✓ Platform fit: Optimized for Instagram/TikTok/YouTube style?
✓ Target audience: Resonates with intended viewers?
✓ Authenticity: Feels genuine, not forced or salesy?

═══════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT (Copy Exactly)
═══════════════════════════════════════════════════

**REEL/VIDEO SCRIPT QC ANALYSIS**
**Script Length:** {len(text.split())} words | **Est. Duration:** {len(text.split()) / 2.5:.1f}s

───────────────────────────────────────────────────
**CATEGORY 1: HOOK & OPENING (25% Weight)**
───────────────────────────────────────────────────
• [If no issues: "✓ All good"]

✗ **ISSUES FOUND:**
• **[BLOCKER/HIGH/MEDIUM]** - [Issue title]
  **Current Script:** "[Quote exact opening lines]"
  **Problem:** [Why this hook is weak/strong, what's missing]

**SCORE: [X]/10**
**Deductions:**
• -[X] points: [Specific issue - e.g., "hook doesn't create curiosity"]
• -[X] points: [Specific issue - e.g., "opening line too generic"]

───────────────────────────────────────────────────
**CATEGORY 2: VISUAL FLOW & PACING (20% Weight)**
───────────────────────────────────────────────────
• [If no issues: "✓ All good"]

✗ **ISSUES FOUND:**
• **[BLOCKER/HIGH/MEDIUM]** - [Issue title]
  **Problem:** [Scene transition issues, pacing problems, length concerns]


**SCORE: [X]/10**
**Deductions:**
• -[X] points: [Specific issue - e.g., "too slow for Reels format"]
• -[X] points: [Specific issue - e.g., "abrupt scene changes"]

───────────────────────────────────────────────────
**CATEGORY 3: DIALOGUES & DELIVERY (20% Weight)**
───────────────────────────────────────────────────
• [If no issues: "✓ All good"]

✗ **ISSUES FOUND:**
• **[BLOCKER/HIGH/MEDIUM]** - [Issue title]
  **Current Dialogue:** "[Quote problematic dialogue]"
  **Problem:** [Grammar, pronunciation, flow, or naturalness issues]


**SCORE: [X]/10**
**Deductions:**
• -[X] points: [Specific issue - e.g., "unnatural phrasing for video"]
• -[X] points: [Specific issue - e.g., "grammar error in main dialogue"]

───────────────────────────────────────────────────
**CATEGORY 4: ON-SCREEN TEXT, CAPTIONS & CTA (20% Weight)**
───────────────────────────────────────────────────
• [If no issues: "✓ All good"]

✗ **ISSUES FOUND:**
• **[BLOCKER/HIGH/MEDIUM]** - [Issue title]
  **Current CTA/Caption:** "[Quote exact text]"
  **Problem:** [Clarity, timing, visibility, or action issues]


**SCORE: [X]/10**
**Deductions:**
• -[X] points: [Specific issue - e.g., "weak CTA wording"]
• -[X] points: [Specific issue - e.g., "captions too long to read"]

───────────────────────────────────────────────────
**CATEGORY 5: BRAND VOICE & TREND ALIGNMENT (15% Weight)**
───────────────────────────────────────────────────
• [If no issues: "✓ All good"]

✗ **ISSUES FOUND:**
• **[BLOCKER/HIGH/MEDIUM]** - [Issue title]
  **Problem:** [Brand voice misalignment, trend misuse, platform mismatch]


**SCORE: [X]/10**
**Deductions:**
• -[X] points: [Specific issue - e.g., "tone too formal for Reels"]
• -[X] points: [Specific issue - e.g., "doesn't match brand guidelines"]

═══════════════════════════════════════════════════
**OVERALL SCRIPT PERFORMANCE**
═══════════════════════════════════════════════════

**📊 WEIGHTED OVERALL SCORE: [X.X]/10**

**Calculation:**
• Hook & Opening (25%): [X]/10 × 0.25 = [X.XX]
• Visual Flow & Pacing (20%): [X]/10 × 0.20 = [X.XX]
• Dialogues & Delivery (20%): [X]/10 × 0.20 = [X.XX]
• Captions & CTA (20%): [X]/10 × 0.20 = [X.XX]
• Brand & Trends (15%): [X]/10 × 0.15 = [X.XX]
**Total:** [X.X]/10

**🎯 PERFORMANCE PREDICTION:**
[Will this script drive engagement? Will viewers watch till the end? Will the CTA convert? Why or why not?]

═══════════════════════════════════════════════════
**PRIORITY ACTION ITEMS**
═══════════════════════════════════════════════════

**🚨 CRITICAL (Fix Before Production):**
1. [Most critical script issue blocking production]
2. [Second critical issue]

**⚠️ HIGH PRIORITY (Fix Before Filming):**
1. [Important issue affecting video quality]
2. [Another important issue]

**📋 RECOMMENDED IMPROVEMENTS:**
1. [Enhancement for better performance]
2. [Polish suggestion for engagement]

───────────────────────────────────────────────────
**PRODUCTION STATUS:** [BLOCKED - BRAND MISMATCH / BLOCKED / NEEDS REVISION / READY WITH NOTES / READY TO FILM]
───────────────────────────────────────────────────

**Status Logic:**
- **BLOCKED - BRAND MISMATCH:** Script is for wrong brand (wrong brand name/products/industry mentioned)
- **BLOCKED:** Critical grammar/safety issues
- **NEEDS REVISION:** High priority issues affecting quality
- **READY WITH NOTES:** Minor improvements suggested
- **READY TO FILM:** All systems go

⚠️ **SPECIAL INSTRUCTION:** If at ANY point during analysis you notice the script mentions a DIFFERENT brand name, products, or industry than what's in the brand context above, immediately output:

**PRODUCTION STATUS: BLOCKED - BRAND MISMATCH**

**Reason:** This script appears to be for [detected brand/industry] but the brand context is for [expected brand/industry]. Please verify you're in the correct project and card table.

[Skip detailed category scoring if brand mismatch detected]

═══════════════════════════════════════════════════
STRICT SCORING SYSTEM
═══════════════════════════════════════════════════

**Start each category at 10/10, then deduct:**

**Hook & Opening (25% weight):**
• -3 points: Weak/generic hook that won't stop scroll
• -2 points: Opening line difficult to deliver or unclear
• -2 points: No curiosity/interest created in first 3 seconds
• -1 point: Hook works but could be stronger
• -1 point: Opening scene description vague

**Visual Flow & Pacing (20% weight):**
• -3 points: Pacing completely wrong for platform (too slow/fast)
• -2 points: Poor scene transitions or confusing flow
• -2 points: Script length inappropriate (>60s for Reels)
• -1 point: Minor pacing issues in middle sections
• -1 point: Could use more visual variety

**Dialogues & Delivery (20% weight):**
• -3 points: Grammar/spelling errors in key dialogues
• -2 points: Unnatural phrasing or hard to pronounce
• -2 points: Tone doesn't match brand or content
• -1 point: Dialogues slightly stiff or scripted-sounding
• -1 point: Minor word choice improvements needed

**On-Screen Text, Captions & CTA (20% weight):**
• -3 points: Missing or very weak CTA
• -2 points: CTA unclear or poor placement
• -2 points: Captions too long or poorly timed
• -1 point: CTA could be more action-oriented
• -1 point: Text formatting could be clearer

**Brand Voice & Trend Alignment (15% weight):**
• -3 points: Significantly off-brand tone or messaging
• -2 points: Doesn't fit platform style/audience
• -2 points: Trend misused or forced
• -1 point: Minor brand guideline deviations
• -1 point: Could better leverage current trends

**Score Interpretation:**
• **9-10:** Excellent - Ready to film, high engagement potential
• **7-8:** Good - Minor tweaks for better performance
• **5-6:** Needs Work - Several improvements required
• **3-4:** Poor - Major script revision needed
• **0-2:** Critical - Complete rewrite recommended

═══════════════════════════════════════════════════
QUALITY CONTROL RULES - NEVER VIOLATE
═══════════════════════════════════════════════════

**✅ ALWAYS DO:**
1. Quote exact problematic script lines
2. Evaluate as VIDEO content (not just text)
3. Consider platform-specific performance (Reels ≠ YouTube)
4. Check if dialogues are natural and deliverable
5. Assess hook strength for scroll-stopping power
6. Verify CTA clarity and placement
7. Show weighted scoring calculation
8. Think about viewer retention and engagement

**❌ NEVER DO:**
1. Analyze like static text (this is VIDEO)
2. Ignore platform differences (Reels vs Shorts vs TikTok)
3. Miss pronunciation or delivery difficulties
4. Overlook weak hooks (first 3 seconds critical)
5. Forget about caption readability
6. Inflate scores without justification
7. Be vague about timing or pacing issues
8. Skip brand voice verification

═══════════════════════════════════════════════════
PLATFORM-SPECIFIC OPTIMIZATION CHECKS
═══════════════════════════════════════════════════

**Instagram Reels:**
• Optimal length: 15-30 seconds (max 90s)
• Hook in first 1-2 seconds critical
• Trending audio mention acceptable
• Text overlays should be minimal and readable
• CTA placement: End card or verbal call

**YouTube Shorts:**
• Optimal length: 15-60 seconds
• Can be slightly slower paced than Reels
• Educational hooks work well
• Text can be more informative
• Subscribe CTA important

**TikTok:**
• Optimal length: 15-30 seconds
• Fastest pace, most casual tone
• Trends and challenges highly relevant
• Text quick and punchy
• Engagement CTA (comment, duet, stitch)

**Facebook Video Ads:**
• Length: 15-30 seconds for feed, up to 60s for stories
• Hook must work without sound (captions critical)
• Clear value proposition needed early
• Strong CTA with urgency
• Brand presence throughout

═══════════════════════════════════════════════════
VIDEO-SPECIFIC RED FLAGS TO CATCH
═══════════════════════════════════════════════════

**Hook Problems:**
• Generic opening ("Hey guys, today I'm going to...")
• No value/curiosity in first 3 seconds
• Opening too slow or informational
• Starts with brand name instead of hook

**Pacing Issues:**
• Too much setup before getting to point
• Dead air or awkward pauses in script
• Rushed ending with no breathing room
• No rhythm or beats in delivery

**Dialogue Problems:**
• Tongue-twisters or hard-to-pronounce words
• Sentences too long for single breath
• Overly formal language for casual video
• Lists that are hard to remember/follow

**Caption Issues:**
• Text too small or too much at once
• Important info only in audio (no captions)
• Captions compete with visuals
• Spelling/grammar errors in overlays

**CTA Failures:**
• CTA buried in middle of script
• Unclear what action to take
• Multiple conflicting CTAs
• No CTA at all

═══════════════════════════════════════════════════
FINAL CHECKLIST BEFORE SUBMITTING
═══════════════════════════════════════════════════

Before finalizing, verify you have:
☐ Evaluated hook strength (first 3 seconds)
☐ Checked all dialogues for pronunciation/flow
☐ Verified script length fits platform
☐ Assessed pacing for video delivery
☐ Confirmed CTA is clear and prominent
☐ Quoted exact problematic script lines
☐ Shown weighted score calculation
☐ Categorized all issues (BLOCKER/HIGH/MEDIUM)
☐ Considered platform-specific optimization
☐ Verified brand voice consistency
☐ Predicted viewer engagement/retention
☐ Given clear PRODUCTION STATUS

═══════════════════════════════════════════════════

**REMEMBER:** This script will be PERFORMED on camera and watched by scrolling users. Your job is to ensure it STOPS the scroll, ENGAGES the viewer, and DRIVES action. Be specific, be critical, be helpful.

Now analyze this reel/video script following this exact structure  and get them all done under 150-170 words."""
        else:
            # Normal Poster Copy QC Prompt
            prompt = f"""You are a Senior Copy QC Analyst specializing in advertising copy. Your feedback must be specific, actionable, and focused on marketing effectiveness.

Text Content: "{text}"
{brand_section}
═══════════════════════════════════════════════════
BRAND CONTEXT (MUST BE STRICTLY FOLLOWED)
═══════════════════════════════════════════════════
{brand_context}

⚠️ **CRITICAL:** Every aspect of your analysis must verify alignment with the brand context above. Any deviation from brand guidelines, tone, or messaging is a BLOCKER issue.

═══════════════════════════════════════════════════
YOUR CORE MISSION
═══════════════════════════════════════════════════
Evaluate how this copy will perform as ADVERTISING CONTENT. Consider:
1. Will the headline grab attention in 2-3 seconds?
2. Does the main copy clearly communicate the value?
3. Does the subcopy support the main message effectively?
4. Are there ANY grammar, spelling, or punctuation errors?
5. Is the CTA compelling and action-oriented?
6. Does it match brand voice while driving conversion?

**IMPORTANT:** Adapt your analysis to the format:
- **Static Ads/Posters:** Evaluate as single-view content (all elements visible at once)
- **Carousels/Multi-Slide:** Evaluate progressive revelation (information unfolds across slides)
- **For Carousels:** Favor clarity and proof points over aggressive sales language

═══════════════════════════════════════════════════
CRITICAL ERROR CATEGORIES (NEVER MISS THESE)
═══════════════════════════════════════════════════

🚨 BLOCKER ISSUES (Must fix before production):
- **BRAND/COPY MISMATCH:** Copy mentions a DIFFERENT brand than the one in brand context (wrong brand name, wrong products/services, wrong industry) - Set PRODUCTION STATUS to "BLOCKED - BRAND MISMATCH"
- Grammar or spelling errors ANYWHERE in copy
- Factual errors in product names, prices, or claims
- Missing or completely unclear CTA
- Punctuation errors that change meaning
- Inconsistent capitalization in headlines/CTAs
- Off-brand tone that contradicts brand guidelines

⚠️ HIGH PRIORITY (Fix before launch):
- Headline confusing or lacks clarity (not just "could be better")
- Main copy fails to communicate core value/benefit
- Subcopy contradicts or confuses main message
- CTA uses passive/unclear language ("Click here" vs "Shop Now")
- Critical information missing for decision-making
- Copy demonstrably too long for the format/space

📋 MEDIUM PRIORITY (Consider if time permits):
- Headline works but alternative could test better
- Minor word choice improvements for stronger impact
- CTA could add urgency without changing clarity
- Tone could better match audience segment

**SCORING DISCIPLINE:**
- Only deduct points for **demonstrable problems**, not hypothetical improvements
- "Could be better" is NOT a valid deduction unless you can show clear weakness
- For carousels: reward clear, factual trust-builders (don't penalize for not being "emotional")
- Don't suggest changes unless current copy has a clear flaw

═══════════════════════════════════════════════════
ANALYSIS STRUCTURE (Exactly 5 Categories)
═══════════════════════════════════════════════════

**CATEGORY 1: COPY EFFECTIVENESS - ALL ELEMENTS (30% Weight)**

You MUST analyze THREE separate elements:
1. **HEADLINE** - The main attention-grabbing title
2. **MAIN COPY/PRIMARY TEXT** - The core message body
3. **SUBCOPY/SUPPORTING TEXT** - Additional details or benefits

For EACH element, check:
✓ Does it serve its purpose effectively?
✓ Is it appropriate length for the format?
✓ Does it contain clear, specific information?

**Scoring Guide:**
- **10/10:** All three elements work effectively for their purpose
- **9/10:** One minor improvement opportunity that doesn't hurt performance
- **7-8/10:** One element has clear weakness affecting effectiveness
- **5-6/10:** Two elements need fixing or one has major issues
- **Below 5:** Multiple elements fail basic requirements

**CATEGORY 2: GRAMMAR & SPELLING (25% Weight)**
Analyze:
✓ Spelling: Zero errors in ALL text elements
✓ Grammar: Proper sentence structure throughout
✓ Punctuation: Correct usage (commas, periods, apostrophes)
✓ Capitalization: Consistent style across copy
✓ Typos: Check headline, main copy, subcopy, CTA

**Scoring Guide:**
- **10/10:** Zero errors found
- **6-7/10:** 1-2 minor typos in body copy
- **3-4/10:** Spelling error in headline/CTA or multiple grammar issues
- **Below 3:** Multiple critical errors

**CATEGORY 3: MESSAGE CLARITY & FLOW (20% Weight)**
Analyze:
✓ Logical flow: Does information build coherently?
✓ Simplicity: Easy to understand at a glance
✓ Coherence: All elements support single message
✓ Readability: Appropriate for target audience
✓ Specificity: Concrete information vs vague claims

**Scoring Guide:**
- **10/10:** Message is crystal clear with perfect flow
- **8-9/10:** Clear message with minor flow hiccups
- **6-7/10:** Some confusion or logical gaps
- **Below 6:** Message unclear or disconnected

**CATEGORY 4: CTA & CONVERSION ELEMENTS (15% Weight)**
Analyze:
✓ CTA clarity: Specific action stated clearly
✓ Action verb: Uses direct command ("Shop," "Get," "Explore")
✓ Relevance: Matches the offer/message context
✓ Findability: Easy to identify as the action step

**Scoring Guide:**
- **10/10:** Clear, action-oriented, relevant CTA
- **8-9/10:** Good CTA that could be slightly more specific
- **6-7/10:** Generic or passive CTA ("Learn More," "Click Here")
- **Below 6:** Missing, buried, or confusing CTA

**CATEGORY 5: BRAND VOICE & AUDIENCE FIT (10% Weight)**
Analyze:
✓ Brand consistency: Aligns with stated brand guidelines
✓ Audience appropriateness: Language suits target demographic
✓ Authenticity: Doesn't feel forced or off-tone
✓ Format appropriateness: Tone matches ad type (carousel vs static)

**Scoring Guide:**
- **10/10:** Perfect brand and audience alignment
- **8-9/10:** Good fit with minor adjustments possible
- **6-7/10:** Noticeable tone mismatch
- **Below 6:** Significantly off-brand or wrong audience

═══════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT
═══════════════════════════════════════════════════

📝 COPY QC ANALYSIS
Copy Length: {len(text.split())} words | Character Count: {len(text)} characters
Format Detected: [Static Ad / Carousel / Multi-Slide]

───────────────────────────────────────────────────
CATEGORY 1: COPY EFFECTIVENESS - ALL ELEMENTS (30% Weight)
───────────────────────────────────────────────────
**1A. HEADLINE ANALYSIS:**
✓  **ALL GOOD** OR ✗ **ISSUE FOUND:**
- **Current Headline:** "[Quote exact headline]"
- **Problem:** [Specific, demonstrable weakness - not "could be better"]

**1B. MAIN COPY/PRIMARY TEXT ANALYSIS:**
✓ **ALL GOOD** [Specific strengths] OR ✗ **ISSUE FOUND:**
- **Current Main Copy:** "[Quote exact text]"
- **Problem:** [Specific failure to communicate value]

**1C. SUBCOPY/SUPPORTING TEXT ANALYSIS:**
✓ **ALL GOOD** [Specific strengths] OR ✗ **ISSUE FOUND:**
- **Current Subcopy:** "[Quote exact text]"
- **Problem:** [How it fails to support or contradicts]

**📊 CATEGORY 1 SCORE: [X]/10**
**Deductions:**
- -[X] points: [Specific, demonstrable issue only]

───────────────────────────────────────────────────
CATEGORY 2: GRAMMAR & SPELLING (25% Weight)
───────────────────────────────────────────────────

✓ **ALL GOOD** - No errors found.

OR

✗ **ISSUES FOUND:**
- **[BLOCKER/HIGH/MEDIUM]** - [Specific error]
  **Location:** [Exact location]
  **Current Text:** "[Quote exact problematic text]"
  **Error Type:** [Spelling/Grammar/Punctuation]
  **Fix:** [Correct version]

**📊 CATEGORY 2 SCORE: [X]/10**

───────────────────────────────────────────────────
CATEGORY 3: MESSAGE CLARITY & FLOW (20% Weight)
───────────────────────────────────────────────────

✓ **ALL GOOD** - Message clear and logical flow.

OR

✗ **ISSUE FOUND:**
- **[BLOCKER/HIGH/MEDIUM]** - [Specific clarity problem]
  **Problem:** [Demonstrable confusion or gap]

**📊 CATEGORY 3 SCORE: [X]/10**

───────────────────────────────────────────────────
CATEGORY 4: CTA & CONVERSION ELEMENTS (15% Weight)
───────────────────────────────────────────────────

✓ **ALL GOOD** - CTA is clear and action-oriented.

OR

✗ **ISSUE FOUND:**
- **Current CTA:** "[Quote exact CTA]"
- **Problem:** [Passive language, missing action verb, or unclear]

**📊 CATEGORY 4 SCORE: [X]/10**

───────────────────────────────────────────────────
CATEGORY 5: BRAND VOICE & AUDIENCE FIT (10% Weight)
───────────────────────────────────────────────────

✓ **ALL GOOD** - Tone aligns with brand and audience.

OR

✗ **ISSUE FOUND:**
- **Problem:** [Specific brand/audience mismatch]

**📊 CATEGORY 5 SCORE: [X]/10**

═══════════════════════════════════════════════════
📊 OVERALL COPY PERFORMANCE
═══════════════════════════════════════════════════

**📊 WEIGHTED OVERALL SCORE: [X.X]/10**

**🧮 Calculation:**
- Copy Effectiveness (30%): [X]/10 × 0.30 = [X.XX]
- Grammar & Spelling (25%): [X]/10 × 0.25 = [X.XX]
- Message Clarity & Flow (20%): [X]/10 × 0.20 = [X.XX]
- CTA & Conversion (15%): [X]/10 × 0.15 = [X.XX]
- Brand Voice & Audience (10%): [X]/10 × 0.10 = [X.XX]
**Total:** [X.X]/10

**🎯 PERFORMANCE PREDICTION:**
[Will this copy perform effectively? Is it error-free? One concise sentence.]

═══════════════════════════════════════════════════
📋 PRIORITY ACTION ITEMS
═══════════════════════════════════════════════════

**🚨 CRITICAL (Must Fix Before Production):**
[Only list if BLOCKER issues exist - otherwise state "None"]

**⚠️ HIGH PRIORITY (Fix Before Launch):**
[Only list if HIGH priority issues exist - otherwise state "None"]

**📋 RECOMMENDED IMPROVEMENTS:**
[Only list if MEDIUM priority issues exist - otherwise state "None - copy is production-ready"]

───────────────────────────────────────────────────
✅ **PRODUCTION STATUS:** [BLOCKED / NEEDS REVISION / APPROVED / APPROVED WITH NOTES]
───────────────────────────────────────────────────

**Status Guide:**
- **BLOCKED - BRAND MISMATCH:** Script is for wrong brand (wrong brand name/products/industry mentioned)
- **BLOCKED:** Grammar errors or critical flaws present
- **NEEDS REVISION:** High priority issues that hurt effectiveness
- **APPROVED WITH NOTES:** Minor improvements suggested but not required
- **APPROVED:** Ready for production as-is
⚠️ **SPECIAL INSTRUCTION:** If at ANY point during analysis you notice the script mentions a DIFFERENT brand name, products, or industry than what's in the brand context above, immediately output:

**PRODUCTION STATUS: BLOCKED - BRAND MISMATCH**

**Reason:** This script appears to be for [detected brand/industry] but the brand context is for [expected brand/industry]. Please verify you're in the correct project and card table.

[Skip detailed category scoring if brand mismatch detected]
═══════════════════════════════════════════════════
STRICT SCORING SYSTEM
═══════════════════════════════════════════════════

**Copy Effectiveness (30% weight):**
Start at 10/10, deduct ONLY for demonstrable problems:
- -3 points: Headline is confusing, misleading, or buries key info
- -2 points: Main copy fails to communicate what's being offered
- -2 points: Subcopy contradicts or confuses the main message
- -1 point: One element good but has clear (not hypothetical) weakness

**Grammar & Spelling (25% weight):**
- -5 points: Multiple errors or error in headline/CTA
- -3 points: Single error in headline or CTA
- -2 points: 1-2 errors in body copy
- -1 point: Minor punctuation inconsistency

**Message Clarity & Flow (20% weight):**
- -4 points: Core message unclear or confusing
- -2 points: Logical gaps between elements
- -1 point: Minor flow issue that doesn't hurt comprehension

**CTA & Conversion (15% weight):**
- -5 points: Missing or completely unclear CTA
- -3 points: Passive/generic CTA ("Click Here," "Learn More")
- -2 points: CTA buried or hard to identify
- -1 point: CTA works but could be more specific

**Brand Voice & Audience (10% weight):**
- -4 points: Clearly contradicts brand guidelines
- -2 points: Wrong tone for target audience
- -1 point: Minor tone adjustment would improve fit

═══════════════════════════════════════════════════
QUALITY CONTROL RULES
═══════════════════════════════════════════════════

**✅ ALWAYS DO:**
1. Analyze ALL THREE copy elements separately
2. Quote exact text when citing issues
3. Only deduct points for actual problems, not hypothetical improvements
4. Recognize format differences (carousel vs static)
5. Give credit for clarity and factual proof points
6. Show weighted calculation
7. Be concise - total analysis under 200 words

**❌ NEVER DO:**
1. Deduct points for vague "could be better" without showing clear weakness
2. Penalize carousel copy for being "too factual" or lacking emotion
3. Suggest changes without identifying specific current problems
4. Inflate or deflate scores without justification
5. Miss actual grammar/spelling errors
6. Ignore format context when evaluating tone

═══════════════════════════════════════════════════
FORMAT-SPECIFIC EVALUATION
═══════════════════════════════════════════════════

**For CAROUSEL/MULTI-SLIDE Content:**
- ✅ Reward: Clear, bite-sized information | Progressive revelation | Factual trust-builders (stats, proof)
- ❌ Don't penalize: Not using "emotional" language | Being straightforward vs "punchy"
- Focus on: Does each slide serve its purpose? Is flow logical across slides?

**For STATIC ADS/POSTERS:**
- ✅ Reward: Strong immediate hook | Clear hierarchy | Single cohesive message
- ❌ Don't penalize: Shorter copy | Very direct approach
- Focus on: Will all elements work when viewed simultaneously?

**For BOTH Formats:**
- Grammar errors are ALWAYS blockers
- CTA must be clear and action-oriented
- Copy must match stated brand voice
- Benefits must be communicated, not buried

═══════════════════════════════════════════════════

**CRITICAL INSTRUCTION:** You MUST analyze Category 1 in THREE separate sub-sections (1A: Headline, 1B: Main Copy, 1C: Subcopy). Never skip any element. Only cite problems you can specifically demonstrate.

Now analyze this copy following this exact structure."""

        print(f"🤖 Sending to Groq Text API (Llama 3.3 70B)...")
        print(f"   Content Type: {'REEL/VIDEO SCRIPT' if is_reel else 'POSTER COPY'}")
        
        completion = get_groq_client().chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        
        result = completion.choices[0].message.content.strip()
        print(f"✅ Text QC completed ({len(result)} chars)")
        return result
        
    except Exception as e:
        error_msg = f"Text QC failed: {type(e).__name__}: {e}"
        print(f"✗ {error_msg}")
        return error_msg


def get_card_attachments(pid, cid, token):
    """Get image attachments from a Basecamp card"""
    try:
        url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{pid}/recordings/{cid}.json"
        r = requests.get(
            url, 
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        if r.ok:
            attachments = r.json().get("attachments", [])
            images = [a for a in attachments if a.get("content_type", "").startswith("image/")]
            print(f"📎 Found {len(images)} image attachment(s)")
            return images
    except Exception as e:
        print(f"✗ Failed to get attachments: {e}")
    return []

def get_card_content(pid, cid, token):
    """Get text content from a Basecamp card"""
    try:
        url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{pid}/recordings/{cid}.json"
        r = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        if r.ok:
            content = strip_html(r.json().get("content", ""))
            print(f"📄 Card content: {len(content)} chars")
            return content
    except Exception as e:
        print(f"✗ Failed to get card content: {e}")
    return None

def post_comment_to_basecamp(pid, cid, text, token):
    """Post QC results as a comment to Basecamp with highlighted keywords"""
    try:
        url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{pid}/recordings/{cid}/comments.json"
        
        formatted_text = text.strip()
        
        # Step 1: Protect quoted text first
        quote_pattern = r'"([^"]+)"'
        quotes = re.findall(quote_pattern, formatted_text)
        quote_placeholders = {}
        for i, quote in enumerate(quotes):
            placeholder = f"___QUOTE_{i}___"
            # Highlighted quoted text - yellow background only for emphasis
            quote_placeholders[placeholder] = f'<span style="background:#FFD700;color:#993838;padding:2px 6px;border-radius:3px;font-style:italic;font-weight:500;">"{quote}"</span>'
            formatted_text = formatted_text.replace(f'"{quote}"', placeholder, 1)
        
        # Step 2: Convert **text** to bold (but NOT for section headers)
        def replace_bold(match):
            content = match.group(1)
            # Don't convert section headers - they'll be handled separately
            section_headers = [
                'VISUAL QC ANALYSIS REPORT', 'REEL/VIDEO SCRIPT QC ANALYSIS', 
                'POSTER COPY QC ANALYSIS', 'SECTION 1:', 'SECTION 2:', 'SECTION 3:', 
                'SECTION 4:', 'SECTION 5:', 'CATEGORY 1:', 'CATEGORY 2:', 'CATEGORY 3:', 
                'CATEGORY 4:', 'CATEGORY 5:', 'PERFORMANCE RATINGS', 'SCORING BREAKDOWN',
                'OVERALL SCRIPT PERFORMANCE', 'OVERALL COPY PERFORMANCE', 'PRIORITY ACTION ITEMS',
                'APPROVAL STATUS', 'PRODUCTION STATUS', 'Image Dimensions', 'Script Length',
                'Copy Length', 'BLOCKER', 'HIGH PRIORITY', 'MEDIUM', 'CRITICAL', 'RECOMMENDED IMPROVEMENTS'
            ]
            if any(header in content for header in section_headers):
                return f'**{content}**'
            return f'<strong>{content}</strong>'
        
        formatted_text = re.sub(r'\*\*(.+?)\*\*', replace_bold, formatted_text)
        
        # Step 3: Highlight QC-specific keywords from the prompts
        
        # === VISUAL QC KEYWORDS ===
        keywords_map = {
            # Section headers (Visual QC) - Bold colored text, no background
            r'SECTION 1: TOP AREA - LOGO/BRANDING/HEADER': '<div style="color:#1E90FF;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">📍 SECTION 1: TOP AREA - LOGO/BRANDING/HEADER</div>',
            r'SECTION 2: COPY QUALITY & CONTENT': '<div style="color:#1E90FF;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">✍️ SECTION 2: COPY QUALITY & CONTENT</div>',
            r'SECTION 3: DESIGN & VISUAL QUALITY': '<div style="color:#1E90FF;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">🎨 SECTION 3: DESIGN & VISUAL QUALITY</div>',
            r'SECTION 4: CTA & FOOTER ELEMENTS': '<div style="color:#1E90FF;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">🎯 SECTION 4: CTA & FOOTER ELEMENTS</div>',
            r'SECTION 5: BRAND CONSISTENCY CHECK': '<div style="color:#1E90FF;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">🏢 SECTION 5: BRAND CONSISTENCY CHECK</div>',
            
            # === REEL/VIDEO QC KEYWORDS ===
            r'CATEGORY 1: HOOK & OPENING': '<div style="color:#FF6347;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">🎣 CATEGORY 1: HOOK & OPENING (25%)</div>',
            r'CATEGORY 2: VISUAL FLOW & PACING': '<div style="color:#FF6347;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">🎬 CATEGORY 2: VISUAL FLOW & PACING (20%)</div>',
            r'CATEGORY 3: DIALOGUES & DELIVERY': '<div style="color:#FF6347;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">🗣️ CATEGORY 3: DIALOGUES & DELIVERY (20%)</div>',
            r'CATEGORY 4: ON-SCREEN TEXT, CAPTIONS & CTA': '<div style="color:#FF6347;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">📱 CATEGORY 4: CAPTIONS & CTA (20%)</div>',
            r'CATEGORY 5: BRAND VOICE & TREND ALIGNMENT': '<div style="color:#FF6347;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">🎭 CATEGORY 5: BRAND & TRENDS (15%)</div>',
            
            # === POSTER COPY QC KEYWORDS ===
            r'CATEGORY 1: HEADLINE EFFECTIVENESS': '<div style="color:#32CD32;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">💡 CATEGORY 1: HEADLINE EFFECTIVENESS (30%)</div>',
            r'CATEGORY 2: GRAMMAR & SPELLING': '<div style="color:#32CD32;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">✅ CATEGORY 2: GRAMMAR & SPELLING (25%)</div>',
            r'CATEGORY 3: MESSAGE CLARITY & FLOW': '<div style="color:#32CD32;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">📝 CATEGORY 3: MESSAGE CLARITY & FLOW (20%)</div>',
            r'CATEGORY 4: CTA & CONVERSION ELEMENTS': '<div style="color:#32CD32;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">🚀 CATEGORY 4: CTA & CONVERSION (15%)</div>',
            r'CATEGORY 5: BRAND VOICE & AUDIENCE FIT': '<div style="color:#32CD32;font-weight:bold;margin:15px 0 8px 0;font-size:16px;">🎯 CATEGORY 5: BRAND & AUDIENCE (10%)</div>',
            
            # Common issue labels - Background ONLY for critical tags
            r'\[BLOCKER\]': '<span style="background:#DC143C;color:#FFFFFF;padding:3px 8px;border-radius:4px;font-weight:bold;font-size:12px;">🚨 BLOCKER</span>',
            r'\[HIGH\]': '<span style="background:#FF8C00;color:#FFFFFF;padding:3px 8px;border-radius:4px;font-weight:bold;font-size:12px;">⚠️ HIGH</span>',
            r'\[MEDIUM\]': '<span style="background:#FFD700;color:#000000;padding:3px 8px;border-radius:4px;font-weight:bold;font-size:12px;">📋 MEDIUM</span>',
            
            # Issue components - Colored text only
            r'Current Text:': '<span style="color:#1E90FF;font-weight:bold;">📄 Current Text:</span>',
            r'Current Headline:': '<span style="color:#1E90FF;font-weight:bold;">💬 Current Headline:</span>',
            r'Current Script:': '<span style="color:#1E90FF;font-weight:bold;">📜 Current Script:</span>',
            r'Current Dialogue:': '<span style="color:#1E90FF;font-weight:bold;">💭 Current Dialogue:</span>',
            r'Current CTA:': '<span style="color:#1E90FF;font-weight:bold;">🎯 Current CTA:</span>',
            r'Current Copy:': '<span style="color:#1E90FF;font-weight:bold;">✏️ Current Copy:</span>',
            r'Problem:': '<span style="color:#DC143C;font-weight:bold;">❌ Problem:</span>',
            r'Fix Needed:': '<span style="color:#32CD32;font-weight:bold;">🔧 Fix Needed:</span>',
            r'Impact:': '<span style="color:#FF8C00;font-weight:bold;">⚡ Impact:</span>',
            r'Location:': '<span style="color:#9370DB;font-weight:bold;">📍 Location:</span>',
            r'Element:': '<span style="color:#9370DB;font-weight:bold;">🎨 Element:</span>',
            
            # Scoring sections - Colored text
            r'SCORE:': '<div style="color:#1E90FF;font-weight:bold;font-size:15px;margin:10px 0 5px 0;">📊 SCORE:</div>',
            r'Deductions:': '<div style="color:#FF6347;font-weight:bold;margin:8px 0 4px 0;">➖ Deductions:</div>',
            r'Calculation:': '<div style="color:#32CD32;font-weight:bold;margin:8px 0 4px 0;">🧮 Calculation:</div>',
            
            # Main report headers - Bold colored text
            r'VISUAL QC ANALYSIS REPORT': '<div style="color:#4169E1;font-weight:bold;text-align:center;margin:10px 0 15px 0;font-size:20px;letter-spacing:1px;">🔍 VISUAL QC ANALYSIS REPORT</div>',
            r'REEL/VIDEO SCRIPT QC ANALYSIS': '<div style="color:#FF6347;font-weight:bold;text-align:center;margin:10px 0 15px 0;font-size:20px;letter-spacing:1px;">🎬 REEL/VIDEO SCRIPT QC ANALYSIS</div>',
            r'POSTER COPY QC ANALYSIS': '<div style="color:#32CD32;font-weight:bold;text-align:center;margin:10px 0 15px 0;font-size:20px;letter-spacing:1px;">📝 POSTER COPY QC ANALYSIS</div>',
            
            # Performance sections - Colored text
            r'PERFORMANCE RATINGS & SCORING BREAKDOWN': '<div style="color:#FF6347;font-weight:bold;margin:15px 0 10px 0;font-size:17px;">📈 PERFORMANCE RATINGS & SCORING BREAKDOWN</div>',
            r'OVERALL SCRIPT PERFORMANCE': '<div style="color:#FF6347;font-weight:bold;margin:15px 0 10px 0;font-size:17px;">📊 OVERALL SCRIPT PERFORMANCE</div>',
            r'OVERALL COPY PERFORMANCE': '<div style="color:#32CD32;font-weight:bold;margin:15px 0 10px 0;font-size:17px;">📊 OVERALL COPY PERFORMANCE</div>',
            
            # Priority sections - Colored text
            r'PRIORITY ACTION ITEMS': '<div style="color:#9370DB;font-weight:bold;margin:15px 0 10px 0;font-size:17px;">📋 PRIORITY ACTION ITEMS</div>',
            r'🚨 CRITICAL \(Must Fix Before': '<div style="color:#DC143C;font-weight:bold;margin:12px 0 6px 0;font-size:15px;">🚨 CRITICAL (Must Fix Before',
            r'⚠️ HIGH PRIORITY \(': '<div style="color:#FF8C00;font-weight:bold;margin:12px 0 6px 0;font-size:15px;">⚠️ HIGH PRIORITY (',
            r'📋 RECOMMENDED IMPROVEMENTS:': '<div style="color:#1E90FF;font-weight:bold;margin:12px 0 6px 0;font-size:15px;">📋 RECOMMENDED IMPROVEMENTS:</div>',
            
            # Status indicators - Background for final approval status only
            r'APPROVAL STATUS:': '<div style="background:#32CD32;color:#FFFFFF;padding:8px 15px;border-radius:6px;font-weight:bold;text-align:center;margin:15px 0;font-size:15px;">✅ APPROVAL STATUS:</div>',
            r'PRODUCTION STATUS:': '<div style="background:#32CD32;color:#FFFFFF;padding:8px 15px;border-radius:6px;font-weight:bold;text-align:center;margin:15px 0;font-size:15px;">✅ PRODUCTION STATUS:</div>',
            
            # Specific scores with icons - Colored text
            r'📝 COPY QUALITY:': '<span style="color:#1E90FF;font-weight:bold;font-size:15px;">📝 COPY QUALITY:</span>',
            r'🎨 DESIGN & LAYOUT:': '<span style="color:#1E90FF;font-weight:bold;font-size:15px;">🎨 DESIGN & LAYOUT:</span>',
            r'🎯 CTA EFFECTIVENESS:': '<span style="color:#1E90FF;font-weight:bold;font-size:15px;">🎯 CTA EFFECTIVENESS:</span>',
            r'🏢 BRANDING CONSISTENCY:': '<span style="color:#1E90FF;font-weight:bold;font-size:15px;">🏢 BRANDING CONSISTENCY:</span>',
            r'⭐ OVERALL IMPACT:': '<span style="color:#FFD700;font-weight:bold;font-size:15px;">⭐ OVERALL IMPACT:</span>',
        }
        
        # Apply keyword highlighting
        for pattern, replacement in keywords_map.items():
            formatted_text = re.sub(pattern, replacement, formatted_text, flags=re.IGNORECASE)
        
        # Step 4: Restore quoted text
        for placeholder, html in quote_placeholders.items():
            formatted_text = formatted_text.replace(placeholder, html)
        
        # Step 5: Convert remaining markdown
        # Divider lines
        formatted_text = re.sub(r'═+', '<hr style="border:none;border-top:2px solid #6495ED;margin:15px 0;">', formatted_text)
        formatted_text = re.sub(r'─+', '<hr style="border:none;border-top:1px dashed #9370DB;margin:10px 0;">', formatted_text)
        
        # Bullet points with better styling
        formatted_text = re.sub(r'^• (.+)$', r'<div style="margin-left:20px;margin-bottom:6px;">▪️ \1</div>', formatted_text, flags=re.MULTILINE)
        
        # Numbered lists
        formatted_text = re.sub(r'^(\d+)\. ', r'<div style="margin-left:20px;margin-bottom:6px;"><strong style="color:#4169E1;">\1.</strong> ', formatted_text, flags=re.MULTILINE)
        
        # Convert newlines
        formatted_text = formatted_text.replace('\n', '<br>')
        
        # Step 6: Final HTML wrapper with improved styling
        html_style = """
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            line-height: 1.8;
            padding: 20px;
        """
        
        html = f'<div style="{html_style}">\n{formatted_text}\n</div>'
        
        r = requests.post(
            url,
            json={"content": html},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        
        if r.ok:
            print(f"✅ Posted comment to Basecamp")
            return True
        else:
            print(f"✗ Failed to post comment: {r.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Post comment error: {e}")
        traceback.print_exc()
        return False
def get_queue_position(comment_id):
    """Get position of a comment in queue (1-indexed)"""
    with qc_queue.mutex:
        queue_list = list(qc_queue.queue)
        for i, task in enumerate(queue_list, 1):
            if task.comment_id == comment_id:
                return i
    return 0

def post_queue_notification(pid, cid, position, token):
    """Post queue position notification to Basecamp"""
    try:
        url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{pid}/recordings/{cid}/comments.json"
        
        html = f"""<div style="font-family:'Segoe UI',Arial,sans-serif;font-size:14px;color:#784067;background:#2c3e50;padding:20px;border-radius:10px;text-align:center;">
<div style="font-size:48px;margin-bottom:10px;">⏳</div>
<div style="font-size:18px;font-weight:bold;margin-bottom:10px;">Your QC request is queued</div>
<div style="font-size:32px;font-weight:bold;color:#3498db;margin:15px 0;">Position: #{position}</div>
<div style="color:#bdc3c7;font-size:13px;margin-top:10px;">You'll be notified when your analysis starts</div>
</div>"""
        
        r = requests.post(
            url,
            json={"content": html},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        
        if r.ok:
            print(f"✅ Posted queue notification (Position #{position})")
            return True
        else:
            print(f"✗ Failed to post queue notification: {r.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Queue notification error: {e}")
        return False

def post_processing_notification(pid, cid, token):
    """Notify user that their QC is starting"""
    try:
        url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{pid}/recordings/{cid}/comments.json"
        
        html = f"""<div style="font-family:'Segoe UI',Arial,sans-serif;font-size:14px;color:#784067;background:#27ae60;padding:20px;border-radius:10px;text-align:center;">
<div style="font-size:48px;margin-bottom:10px;">🤖</div>
<div style="font-size:18px;font-weight:bold;">Your QC analysis is starting now...</div>
</div>"""
        
        requests.post(
            url,
            json={"content": html},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        
    except Exception as e:
        print(f"✗ Processing notification error: {e}")

def process_qc_task(task: QCTask):
    """Process a single QC task"""
    try:
        print(f"\n{'='*60}")
        print(f"🔄 PROCESSING TASK: Comment {task.comment_id}")
        print(f"   Project: {task.project_id}, Card: {task.card_id}")
        print(f"{'='*60}\n")
        
        token = get_access_token()
        if not token:
            print("❌ FATAL: Failed to get access token - check CONFIG credentials")
            print(f"   CLIENT_ID: {CONFIG['CLIENT_ID'][:20]}...")
            print(f"   ACCOUNT_ID: {CONFIG['ACCOUNT_ID']}")
            return
        
        # Notify user that processing is starting
        post_processing_notification(task.project_id, task.card_id, token)
        
        # Get project-specific image path
        image_path = get_project_image_path(task.project_id)
        image = None

        # Check Basecamp attachments
        print("🔍 Checking Basecamp attachments...")
        for att in get_card_attachments(task.project_id, task.card_id, token):
            img = download_image_with_auth(att["download_url"], token, image_path)
            if img:
                image = img
                print("✅ Got image from Basecamp")
                break

        # Check Google Drive URLs
        if not image and task.urls:
            print("🔍 Checking Google Drive URLs...")
            for url in task.urls:
                if "drive.google.com" in url:
                    img = download_image_to_disk(url, image_path)
                    if img:
                        image = img
                        print("✅ Got image from Google Drive")
                        break

        # Perform QC
        print("🔍 Performing QC...")
        if image:
            result = perform_image_qc_with_huggingface(image, task.full_context)
        else:
            # Clean up text content
            text_content = re.sub(r'@nokk\b', '', task.content, flags=re.IGNORECASE).strip()
            
            # Check if it's a reel script
            is_reel = False
            if '[reel]' in text_content.lower():
                is_reel = True
                # Remove the [reel] marker from content
                text_content = re.sub(r'\[reel\]', '', text_content, flags=re.IGNORECASE).strip()
                print("🎬 Detected REEL/VIDEO SCRIPT content")
            
            # Remove URLs from text
            for url in task.urls:
                text_content = text_content.replace(url, "").strip()
            
            if not text_content or len(text_content) < 10:
                text_content = get_card_content(task.project_id, task.card_id, token)
                # Check for [reel] in card content too
                if text_content and '[reel]' in text_content.lower():
                    is_reel = True
                    text_content = re.sub(r'\[reel\]', '', text_content, flags=re.IGNORECASE).strip()
            
            result = perform_text_qc(text_content, task.full_context, is_reel=is_reel)

        # Post results
        print("🔍 Posting results...")
        success = post_comment_to_basecamp(task.project_id, task.card_id, result, token)
        
        if success:
            print("✅ TASK COMPLETED SUCCESSFULLY")
        else:
            print("⚠️ TASK COMPLETED WITH ERRORS")
        
    except Exception as e:
        print(f"❌ Task processing error: {e}")
        traceback.print_exc()

def queue_worker():
    """Background worker that processes queue"""
    global is_processing, current_task
    
    while True:
        try:
            # Get next task (blocks until available)
            task = qc_queue.get()
            
            with processing_lock:
                is_processing = True
                current_task = task
            
            # Process the task
            process_qc_task(task)
            
            with processing_lock:
                is_processing = False
                current_task = None
            
            # Mark task as done
            qc_queue.task_done()
            
        except Exception as e:
            print(f"❌ Queue worker error: {e}")
            traceback.print_exc()
            with processing_lock:
                is_processing = False
                current_task = None

# ==================== CARD TABLE VALIDATION ====================
# ==================== CARD TABLE VALIDATION ====================
def validate_card_table(project_id, card_id, token):
    """
    Validate that the card belongs to the correct card table for the project.
    Returns (is_valid, card_table_id, error_message)
    """
    try:
        print(f"🔍 Validating card table for ID {card_id} in project {project_id}")
        
        # CRITICAL FIX: card_id from webhook is actually a COMMENT ID
        # We need to get the parent CARD first, then check its card table
        
        # Step 1: Get the comment to find the actual card
        comment_url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{project_id}/recordings/{card_id}.json"
        print(f"   Fetching comment/card: {comment_url}")
        
        r = requests.get(
            comment_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        
        print(f"   Response status: {r.status_code}")
        
        if not r.ok:
            print(f"   ⚠️ Fetch failed: {r.status_code}")
            return True, None, None  # Allow processing if API fails
        
        # Check if response has content
        if not r.content:
            print(f"   ⚠️ Empty response from API")
            return True, None, None
        
        try:
            data = r.json()
        except Exception as json_err:
            print(f"   ⚠️ JSON decode error: {json_err}")
            print(f"   Response text: {r.text[:200]}")
            return True, None, None  # Allow processing if JSON fails
        
        print(f"   Data type: {data.get('type')}")
        
        # Step 2: Find the actual card
        # If this is a comment, get its parent (which should be the card)
        parent = data.get("parent")
        if not parent:
            print("   ⚠️ No parent found - cannot validate")
            return True, None, None
        
        actual_card_id = parent.get("id")
        parent_type = parent.get("type")
        
        print(f"   Parent ID: {actual_card_id}, Type: {parent_type}")
        
        if not actual_card_id:
            print("   ⚠️ No parent ID found")
            return True, None, None
        
        # Step 3: Get the actual card details
        card_url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{project_id}/recordings/{actual_card_id}.json"
        print(f"   Fetching actual card: {card_url}")
        
        card_r = requests.get(
            card_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        
        if not card_r.ok or not card_r.content:
            print(f"   ⚠️ Card fetch failed or empty")
            return True, None, None
        
        try:
            card_data = card_r.json()
        except:
            print(f"   ⚠️ Card JSON decode failed")
            return True, None, None
        
        # Step 4: Get the card's parent (column)
        card_parent = card_data.get("parent")
        if not card_parent:
            print("   ⚠️ Card has no parent column")
            return True, None, None
        
        column_id = card_parent.get("id")
        print(f"   Column ID: {column_id}")
        
        if not column_id:
            print("   ⚠️ No column ID found")
            return True, None, None
        
        # Step 5: Get the column to find card table
        column_url = f"https://3.basecampapi.com/{CONFIG['ACCOUNT_ID']}/buckets/{project_id}/recordings/{column_id}.json"
        print(f"   Fetching column: {column_url}")
        
        col_r = requests.get(
            column_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        
        if not col_r.ok or not col_r.content:
            print(f"   ⚠️ Column fetch failed or empty")
            return True, None, None
        
        try:
            column_data = col_r.json()
        except:
            print(f"   ⚠️ Column JSON decode failed")
            return True, None, None
        
        # Step 6: Get the card table (parent of column)
        column_parent = column_data.get("parent")
        if not column_parent:
            print("   ⚠️ Column has no parent card table")
            return True, None, None
        
        actual_card_table_id = column_parent.get("id")
        print(f"   ✅ Found card table ID: {actual_card_table_id}")
        
        if not actual_card_table_id:
            print("   ⚠️ No card table ID found")
            return True, None, None
        
        # Step 7: Validate against expected card table
        project_config = get_project_config(project_id)
        if not project_config:
            print(f"   ⚠️ No project config")
            return True, None, None
        
        expected_card_table_id = project_config.get("card_table_id")
        if not expected_card_table_id:
            print(f"   ⚠️ No expected card table configured for {project_config['name']}")
            return True, actual_card_table_id, None
        
        print(f"   Expected card table: {expected_card_table_id}")
        print(f"   Actual card table: {actual_card_table_id}")
        
        # Step 8: Compare
        if actual_card_table_id != expected_card_table_id:
            project_name = project_config["name"]
            error_msg = f"""❌ **WRONG CARD TABLE / BOARD**

This card is in the **WRONG LOCATION** for **{project_name}** QC.

**🎯 Expected Card Table ID:** `{expected_card_table_id}`
**📍 Current Card Table ID:** `{actual_card_table_id}`

**⚠️ Action Required:**
Please move this card to the correct QC board designated for **{project_name}** before requesting QC.

**Supported Projects & Their Card Tables:**
{chr(10).join([f"• {p['name']}: Card Table ID {p['card_table_id']}" for p in PROJECTS.values()])}

If you believe this is an error, contact the bot administrator."""
            
            print(f"   ❌ VALIDATION FAILED!")
            print(f"   Card is in WRONG card table!")
            return False, actual_card_table_id, error_msg
        
        print(f"   ✅ VALIDATION PASSED! Card is in correct table.")
        return True, actual_card_table_id, None
        
    except requests.exceptions.Timeout:
        print(f"   ⚠️ Request timeout")
        return True, None, None
        
    except requests.exceptions.RequestException as req_err:
        print(f"   ⚠️ Network error: {req_err}")
        return True, None, None
        
    except Exception as e:
        print(f"   ⚠️ Unexpected error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return True, None, None
# ==================== WEBHOOK ====================
@app.route("/webhook/basecamp", methods=["POST"])
def basecamp_webhook():
    """Main webhook handler - adds tasks to queue"""
    try:
        print("\n" + "="*60)
        print(f"📨 WEBHOOK RECEIVED @ {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        data = request.json
        kind = data.get("kind")
        rec = data.get("recording", {})
        cid = rec.get("id")
        
        content_raw = strip_html(rec.get("content", ""))
        content_lower = content_raw.lower()
        
        print(f"Kind: {kind}")
        print(f"Comment ID: {cid}")

        # Basic validation
        if kind != "comment_created":
            print(f"⏭️  Ignoring: not a comment")
            return jsonify({"status": "ignored", "reason": "not_comment"}), 200
            
        if cid in processed_comments:
            print(f"⏭️  Ignoring: already processed")
            return jsonify({"status": "ignored", "reason": "duplicate"}), 200
            
        if "@nokk" not in content_lower:
            print(f"⏭️  Ignoring: no @nokk trigger")
            return jsonify({"status": "ignored", "reason": "no_trigger"}), 200

        processed_comments.add(cid)
        
        pid = rec.get("bucket", {}).get("id")
        card_id = rec.get("parent", {}).get("id")
        
        if not pid or not card_id:
            print("✗ Missing project or card ID")
            return jsonify({"error": "missing_ids"}), 400

        print(f"Project ID: {pid}")
        print(f"Card ID: {card_id}")

        # Get access token first
        token = get_access_token()
        if not token:
            print("❌ Failed to get access token")
            return jsonify({"error": "auth_failed"}), 500

        # ==================== VALIDATION STEP 1: PROJECT ====================
        project_config = get_project_config(pid)
        if not project_config:
            error_msg = f"""❌ **UNSUPPORTED PROJECT**

This project (ID: {pid}) is not configured in the QC Bot.

**Supported Projects:**
{chr(10).join([f"• {p['name']} (ID: {p_id})" for p_id, p in PROJECTS.items()])}

Please contact the bot administrator to add this project."""
            
            print(f"❌ REJECTED: Unsupported project ID {pid}")
            post_comment_to_basecamp(pid, card_id, error_msg, token)
            
            return jsonify({
                "status": "rejected", 
                "reason": "unsupported_project",
                "project_id": pid
            }), 400
        
        project_name = project_config["name"]
        print(f"✅ Project validated: {project_name}")

        # ==================== VALIDATION STEP 2: CARD TABLE ====================
        is_valid_table, actual_table_id, table_error = validate_card_table(pid, card_id, token)
        
        if not is_valid_table:
            error_msg = table_error or f"""❌ **CARD TABLE VALIDATION FAILED**

Unable to verify this card is in the correct QC board for {project_name}.

**Project:** {project_name}
**Expected Card Table ID:** {project_config.get('card_table_id')}
**Actual Card Table ID:** {actual_table_id or 'Unknown'}

Please ensure:
1. The card is in the correct project
2. The card is in the designated QC board/column
3. The card table is properly configured

Contact administrator if this error persists."""
            
            print(f"❌ REJECTED: Wrong card table for {project_name}")
            print(f"   Expected: {project_config.get('card_table_id')}")
            print(f"   Actual: {actual_table_id}")
            
            post_comment_to_basecamp(pid, card_id, error_msg, token)
            
            return jsonify({
                "status": "rejected",
                "reason": "wrong_card_table",
                "project": project_name,
                "expected_table": project_config.get('card_table_id'),
                "actual_table": actual_table_id
            }), 400
        
        print(f"✅ Card table validated: {actual_table_id}")
        # ==================== END VALIDATION ====================

        # Get brand context for valid project + card table
        brand_context = project_config["brand_context"]
        
        print(f"📋 Brand context loaded: {len(brand_context)} chars")

        # Extract URLs and user context
        urls = extract_urls(content_raw)
        user_context = re.sub(r'@nokk\b', '', content_raw, count=1, flags=re.IGNORECASE).strip()
        for url in urls:
            user_context = user_context.replace(url, "").strip()
        
        # Combine contexts
        if user_context:
            full_context = f"{brand_context}\n\nUser Brief: {user_context}"
        else:
            full_context = brand_context
        
        # Create task
        task = QCTask(
            comment_id=cid,
            project_id=pid,
            card_id=card_id,
            content=content_raw,
            urls=urls,
            brand_context=brand_context,
            full_context=full_context,
            timestamp=datetime.now().timestamp()
        )
        
        # Process synchronously (Render compatible)
        print(f"🔄 Processing task synchronously for {project_name}...")
        process_qc_task(task)
        print("="*60)
        print(f"✅ WEBHOOK COMPLETED - Task processed for {project_name}")
        print("="*60 + "\n")
        return jsonify({"status": "processed", "project": project_name}), 200

    except Exception as e:
        print(f"❌ WEBHOOK ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
# ==================== STARTUP ====================
# Add this to your main block, BEFORE app.run():

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 MULTI-PROJECT QC BOT v15.0 STARTING...")
    print("="*60)
    print(f"✓ Queue system enabled")
    print(f"✓ Image base directory: {IMAGE_BASE_DIR}")
    print(f"✓ Supported projects: {len(PROJECTS)}")
    
    # Create project folders
    for pid, config in PROJECTS.items():
        folder = os.path.join(IMAGE_BASE_DIR, config["name"].replace(" ", "_").lower())
        os.makedirs(folder, exist_ok=True)
        print(f"  ✓ {config['name']}: {folder}")
    
    print("="*60 + "\n")
    
    get_access_token()
    
    # Start queue worker thread
    # Disabled: Queue-based processing doesn't work on Render free tier
    # Background threads are killed on service restart
    # Using synchronous processing in webhook instead
    # worker_thread = threading.Thread(target=queue_worker, daemon=True)
    # worker_thread.start()
    # print("✅ Queue worker started!")
    
    print("\n✅ Bot ready! Waiting for webhooks...\n")
    print("📝 Processing mode: SYNCHRONOUS (Render compatible)\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    project_list = "\n".join([f"  • {p['name']} (ID: {pid})" for pid, p in PROJECTS.items()])
    
    return f"""<pre style="font-family:monospace;padding:20px;background:#f5f5f5;">
<b>🤖 Multi-Project QC Bot v15.0</b>

Status: <span style="color:green">● RUNNING</span>
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Model: Hugging Face Llama Vision + Text

<b>Supported Projects ({len(PROJECTS)}):</b>
{project_list}

Usage:
  <b>For Image QC:</b>
  1. Comment: @nokk [optional brand brief]
  2. Attach image or provide Google Drive link
  
  <b>For Poster Copy QC:</b>
  1. Comment: @nokk
  2. Paste your poster copy text
  
  <b>For Reel/Video Script QC:</b>
  1. Comment: @nokk [reel]
  2. Paste your reel/video script
  
  3. Bot auto-detects project and applies brand context
  4. Receives QC with findings and issues

Features:
  ✓ Multi-project support
  ✓ Auto brand context detection
  ✓ Project-specific image storage
  ✓ Image + Text analysis
  ✓ Reel/Video script analysis
  ✓ Google Drive support
  ✓ Queue system for concurrent requests
</pre>"""

# ==================== STARTUP ====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 MULTI-PROJECT QC BOT v15.0 STARTING...")
    print("="*60)
    print(f"✓ Image base directory: {IMAGE_BASE_DIR}")
    print(f"✓ Supported projects: {len(PROJECTS)}")
    print(f"✓ HF_TOKEN configured: {CONFIG['GROQ_API_KEY'][:10]}...")
    
    # Create project folders
    for pid, config in PROJECTS.items():
        folder = os.path.join(IMAGE_BASE_DIR, config["name"].replace(" ", "_").lower())
        os.makedirs(folder, exist_ok=True)
        print(f"  ✓ {config['name']}: {folder}")
    
    print("="*60 + "\n")
    
    get_access_token()
    
    print("\n✅ Bot ready! Waiting for webhooks...\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
