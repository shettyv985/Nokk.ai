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
        
        prompt = f"""You are a Senior Visual QC Analyst specializing in digital and print advertising. Your feedback must be specific, consistent, actionable, and thorough.

═══════════════════════════════════════════════════
IMAGE SPECIFICATIONS
═══════════════════════════════════════════════════
Image Details: {image.size[0]}×{image.size[1]}px
Format Type: [Auto-detect: Social Media Ad / Display Banner / Print Material]
{brand_section}

═══════════════════════════════════════════════════
YOUR CORE MISSION
═══════════════════════════════════════════════════
Catch every errors before launch. Be the last line of defense. Your job is to:
1. Identify BLOCKER issues that prevent approval
2. Spot HIGH PRIORITY issues that need fixing
3. Note MEDIUM PRIORITY improvements
4. Provide specific, actionable feedback
5. Score fairly and consistently

═══════════════════════════════════════════════════
CRITICAL ERROR CATEGORIES (NEVER MISS THESE)
═══════════════════════════════════════════════════

🚨 BLOCKER ISSUES (Must fix before approval):
• Grammar/spelling errors in headlines, CTAs, or body copy
• Wrong logo version, incorrect brand colors, or distorted logo
• Illegible text (poor contrast, too small, cut off)
• Broken layout or major alignment issues
• Incorrect product names, prices, or contact information
• Missing or non-functional CTA

⚠️ HIGH PRIORITY (Fix before launch):
• Minor grammar errors in secondary text
• Off-brand colors or fonts
• Weak visual hierarchy (wrong element emphasized)
• Low-resolution or pixelated images
• CTA not prominent enough or unclear wording
• Inconsistent spacing or alignment

📋 MEDIUM PRIORITY (Should improve):
• Minor spacing/alignment inconsistencies
• CTA could be more action-oriented
• Visual flow could be optimized
• Secondary elements need polish

═══════════════════════════════════════════════════
ANALYSIS STRUCTURE (Exactly 5 Sections)
═══════════════════════════════════════════════════

**SECTION 1: TOP AREA - LOGO/BRANDING/HEADER**
Check for:
✓ Logo: correct version, size, placement, clarity, not distorted
✓ Brand name: correct spelling, capitalization
✓ Header text: grammar, spelling, alignment
✓ Overall branding: matches brand guidelines

**SECTION 2: MIDDLE AREA - COPY QUALITY**
Check for:
✓ Headline: grammar, spelling, clarity, impact
✓ Subheadline/body copy: grammar, punctuation, tone
✓ Product/offer details: accuracy, clarity
✓ All text: typos, awkward phrasing, capitalization
⚠️ ALWAYS quote the exact problematic text

**SECTION 3: MIDDLE AREA - DESIGN & VISUAL QUALITY**
Check for:
✓ Layout: organized, balanced, professional
✓ Visual hierarchy: eye flows correctly (headline → visual → CTA)
✓ Image quality: sharp, high-res, not pixelated/blurry
✓ Alignment: elements properly lined up
✓ Spacing: consistent padding and margins
✓ Colors: on-brand, good contrast, readable
✓ Fonts: consistent, readable, appropriate size

**SECTION 4: BOTTOM AREA - CTA & FOOTER**
Check for:
✓ CTA button/text: clear action word (Shop Now, Learn More)
✓ CTA visibility: stands out, easy to find
✓ CTA placement: logical position in visual flow
✓ Contact info: accurate phone, email, website
✓ Footer: legal text readable, proper disclaimers
✓ Social handles: correct spelling

**SECTION 5: OVERALL BRAND CONSISTENCY**
Check for:
✓ Logo quality and correct usage
✓ Brand colors: exact match to guidelines
✓ Typography: correct fonts and weights
✓ Overall polish: professional appearance
✓ Format specs: correct dimensions for platform

═══════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT (Copy Exactly)
═══════════════════════════════════════════════════

**VISUAL QC ANALYSIS REPORT**
**Image Dimensions:** {image_width}×{image_height}px

───────────────────────────────────────────────────
**SECTION 1: TOP AREA - LOGO/BRANDING/HEADER**
───────────────────────────────────────────────────
• [If no issues: "✓ All good"]

✗ **ISSUES FOUND:**
• **[BLOCKER/HIGH/MEDIUM]** - [Issue title]
  **Location:** [Specific area]
  **Problem:** [Detailed explanation with quoted text if applicable]
  **Fix Needed:** [Exact action required]

───────────────────────────────────────────────────
**SECTION 2: COPY QUALITY & CONTENT**
───────────────────────────────────────────────────
• [If no issues: "✓ All good"]

✗ **ISSUES FOUND:**
• **[BLOCKER/HIGH/MEDIUM]** - [Issue title]
  **Current Text:** "[Quote exact problematic text]"
  **Problem:** [Grammar error, spelling mistake, clarity issue]
  **Impact:** [Credibility loss, message confusion, unprofessional]
  **Fix Needed:** "[Suggested corrected text]"

───────────────────────────────────────────────────
**SECTION 3: DESIGN & VISUAL QUALITY**
───────────────────────────────────────────────────
• [If no issues: "✓ All good"]

✗ **ISSUES FOUND:**
• **[BLOCKER/HIGH/MEDIUM]** - [Issue title]
  **Element:** [Specific design element]
  **Problem:** [Alignment, spacing, image quality, hierarchy issue]
  **Impact:** [Reduced readability, poor UX, weak focus]
  **Fix Needed:** [Specific design change required]

───────────────────────────────────────────────────
**SECTION 4: CTA & FOOTER ELEMENTS**
───────────────────────────────────────────────────
• [If no issues: "✓ All good"]

✗ **ISSUES FOUND:**
• **[BLOCKER/HIGH/MEDIUM]** - [Issue title]
  **Current:** "[Quote exact CTA or footer text]"
  **Problem:** [Not action-oriented, poor visibility, incorrect info]
  **Impact:** [Lower conversion, user confusion, missed opportunity]
  **Fix Needed:** [Specific recommendation]

───────────────────────────────────────────────────
**SECTION 5: BRAND CONSISTENCY CHECK**
───────────────────────────────────────────────────
**LOGO STATUS:**
• **Current:** [Description of logo as shown]
• **Issues:** [Specific problems] OR "✓ Correctly implemented"
• **Fix Needed:** [What needs correction] OR "None"

**BRAND GUIDELINES:**
• **Colors:** [On-brand / Off-brand with specifics]
• **Typography:** [Correct / Issues found]
• **Overall:** [Consistent / Deviations noted]

═══════════════════════════════════════════════════
**PERFORMANCE RATINGS & SCORING BREAKDOWN**
═══════════════════════════════════════════════════

**📝 COPY QUALITY:** [X]/10
**Scoring Logic:**
• Started at: 10/10
• Deduction: -[X] points for [specific issue - e.g., "headline grammar error"]
• Deduction: -[X] points for [specific issue - e.g., "body copy typo"]
• **Final Score:** [X]/10
• **Assessment:** [Brief summary of copy state]

**🎨 DESIGN & LAYOUT:** [X]/10
**Scoring Logic:**
• Started at: 10/10
• Deduction: -[X] points for [specific issue - e.g., "poor visual hierarchy"]
• Deduction: -[X] points for [specific issue - e.g., "alignment issues"]
• **Final Score:** [X]/10
• **Assessment:** [Brief summary of design quality]

**🎯 CTA EFFECTIVENESS:** [X]/10
**Scoring Logic:**
• Started at: 10/10
• Deduction: -[X] points for [specific issue - e.g., "weak action word"]
• Deduction: -[X] points for [specific issue - e.g., "poor visibility"]
• **Final Score:** [X]/10
• **Assessment:** [Brief assessment of CTA strength]

**🏢 BRANDING CONSISTENCY:** [X]/10
**Scoring Logic:**
• Started at: 10/10
• Deduction: -[X] points for [specific issue - e.g., "off-brand color"]
• Deduction: -[X] points for [specific issue - e.g., "wrong logo version"]
• **Final Score:** [X]/10
• **Assessment:** [Brief assessment of brand adherence]

**⭐ OVERALL IMPACT:** [X]/10
**Holistic Assessment:**
[Does this creative achieve its marketing goal? Would you approve it? Why or why not?]

═══════════════════════════════════════════════════
**PRIORITY ACTION ITEMS**
═══════════════════════════════════════════════════

**🚨 CRITICAL (Must Fix Before Approval):**
1. [Most critical issue that blocks approval]
2. [Second critical issue]

**⚠️ HIGH PRIORITY (Should Fix Before Launch):**
1. [Important issue affecting quality]
2. [Another important issue]

**📋 RECOMMENDED IMPROVEMENTS:**
1. [Nice-to-have enhancement]
2. [Polish suggestion]

───────────────────────────────────────────────────
**APPROVAL STATUS:** [BLOCKED / NEEDS REVISION / APPROVED WITH NOTES / APPROVED]
───────────────────────────────────────────────────

═══════════════════════════════════════════════════
STRICT SCORING SYSTEM
═══════════════════════════════════════════════════

**Start each category at 10/10, then deduct:**

**Copy Quality (Grammar, spelling, clarity, messaging):**
• -3 points: Grammar/spelling in headline or CTA
• -2 points: Grammar/spelling in body copy
• -1 point: Awkward phrasing or unclear message
• -1 point: Inconsistent tone or capitalization

**Design & Layout (Visual organization, quality, readability):**
• -3 points: Major alignment issues or broken layout
• -2 points: Poor visual hierarchy (wrong focus)
• -2 points: Low-res/pixelated images
• -1 point: Minor spacing inconsistencies
• -1 point: Readability issues (contrast, size)

**CTA Effectiveness (Clarity, visibility, action-oriented):**
• -3 points: Missing or hidden CTA
• -2 points: Weak/unclear CTA wording
• -2 points: Poor CTA placement or visibility
• -1 point: CTA could be more compelling

**Branding Consistency (Logo, colors, fonts, guidelines):**
• -3 points: Wrong logo or severely distorted
• -2 points: Off-brand colors
• -2 points: Wrong fonts or typography
• -1 point: Minor logo sizing/placement issue

**Overall Impact (Combined effectiveness):**
• Average of other scores, adjusted for:
  - Cohesive visual storytelling
  - Achieves marketing objective
  - Professional polish
  - User experience quality

**Score Interpretation:**
• **9-10:** Excellent - Ready to launch
• **7-8:** Good - Minor fixes recommended
• **5-6:** Needs Work - Multiple issues to address
• **3-4:** Poor - Major revision required
• **0-2:** Critical - Complete rework needed

═══════════════════════════════════════════════════
QUALITY CONTROL RULES - NEVER VIOLATE
═══════════════════════════════════════════════════

**✅ ALWAYS DO:**
1. Be specific about location and element
2. Quote exact problematic text for copy issues
3. Explain WHY each issue matters (impact on brand/conversion)
4. Show your scoring math (deductions explained)
5. Balance feedback (note strengths AND issues)
6. Categorize severity (BLOCKER/HIGH/MEDIUM)
7. Apply same standards consistently
8. Give exact fixes, not vague suggestions

**❌ NEVER DO:**
1. Be vague ("text needs work" is unacceptable)
2. Miss grammar errors (read EVERY word)
3. Inflate scores (be honest about quality)
4. Skip explanations (always say WHY)
5. Ignore context (consider where this will be used)
6. Overlook logo issues (brand consistency critical)
7. Miss image quality problems (pixelation kills credibility)
8. Forget to check spelling in ALL text areas

═══════════════════════════════════════════════════
COMMON ERRORS TO CATCH
═══════════════════════════════════════════════════

**Grammar Traps:**
• Its vs. It's
• Your vs. You're
• Their/There/They're
• Comma splices
• Missing apostrophes
• Inconsistent capitalization

**Brand Issues:**
• Outdated logo version
• Wrong brand colors (even slight shades)
• Stretched/squished logo
• Logo too small or unclear
• Wrong font families

**Design Red Flags:**
• Text over busy background (unreadable)
• Too many fonts or colors
• Inconsistent alignment
• Pixelated/low-res images
• Poor contrast (accessibility)
• Text cut off at edges

**CTA Problems:**
• Generic wording ("Click Here")
• Not visually prominent
• Wrong placement in flow
• Multiple competing CTAs

═══════════════════════════════════════════════════
FINAL CHECKLIST BEFORE SUBMITTING
═══════════════════════════════════════════════════

Before finalizing, verify you have:
☐ Checked EVERY word for spelling/grammar
☐ Verified logo is correct version and not distorted
☐ Confirmed all brand colors match guidelines
☐ Assessed visual hierarchy (eye flow correct?)
☐ Evaluated CTA for clarity and prominence
☐ Quoted exact problematic text for all copy issues
☐ Explained WHY each issue matters
☐ Shown point deduction math for each score
☐ Categorized all issues (BLOCKER/HIGH/MEDIUM)
☐ Provided specific fixes for every issue
☐ Listed action items in priority order
☐ Given clear APPROVAL STATUS

═══════════════════════════════════════════════════

**REMEMBER:** You are the last line of defense before this creative goes live. Be thorough, be specific, be consistent. Every error you catch saves the brand's reputation and marketing investment.

Now analyze the image following this exact structure and get them all done under 150-170 words."""


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
            max_tokens=800,
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
**PRODUCTION STATUS:** [BLOCKED / NEEDS REVISION / READY WITH NOTES / READY TO FILM]
───────────────────────────────────────────────────

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
            prompt = f"""You are a Senior Copy QC Analyst specializing in advertising poster copy. Your feedback must be specific, actionable, and focused on marketing effectiveness.

Text Content: "{text}"
{brand_section}

═══════════════════════════════════════════════════
YOUR CORE MISSION
═══════════════════════════════════════════════════
Evaluate how this copy will perform as POSTER CONTENT. Consider:

Will the headline grab attention in 2-3 seconds?
Is the message clear and instantly understandable?
Does the copy work with visual hierarchy (headline > subhead > CTA)?
Are there any grammar, spelling, or punctuation errors?
Is the CTA compelling and action-oriented?
Does it match brand voice while driving conversion?

═══════════════════════════════════════════════════
CRITICAL ERROR CATEGORIES (NEVER MISS THESE)
═══════════════════════════════════════════════════
🚨 BLOCKER ISSUES (Must fix before production):

Grammar or spelling errors anywhere in copy
Weak or confusing headline that lacks clarity
Missing or unclear CTA
Off-brand tone or messaging
Copy too long for visual space (readability issues)
Incorrect product names, prices, or claims
Punctuation errors that change meaning
Inconsistent capitalization in headlines/CTAs

⚠️ HIGH PRIORITY (Fix before printing):

Headline could be more attention-grabbing
Subheadline doesn't support main message effectively
CTA not action-oriented enough (generic wording)
Copy tone doesn't match target audience
Missing key benefit or value proposition
Word choice could be stronger/clearer
Copy length imbalanced (headline too long, body too short)

📋 MEDIUM PRIORITY (Recommended improvements):

Could use more emotional appeal
Opportunity for stronger power words
CTA urgency could be enhanced
Minor stylistic improvements for flow
Could better leverage social proof or benefits

═══════════════════════════════════════════════════
ANALYSIS STRUCTURE (Exactly 5 Categories)
═══════════════════════════════════════════════════
CATEGORY 1: HEADLINE EFFECTIVENESS (30% Weight)
Analyze:
✓ Attention-grabbing: Does it stop viewers instantly?
✓ Clarity: Message clear within 2-3 seconds?
✓ Relevance: Speaks to target audience needs/pain points?
✓ Length: Appropriate for poster format (not too long)?
✓ Power: Uses strong, impactful words?
CATEGORY 2: GRAMMAR & SPELLING (25% Weight)
Analyze:
✓ Spelling: Zero errors in all text elements?
✓ Grammar: Proper sentence structure and word usage?
✓ Punctuation: Correct use of commas, periods, apostrophes?
✓ Capitalization: Consistent and appropriate style?
✓ Typos: No overlooked mistakes in any section?
CATEGORY 3: MESSAGE CLARITY & FLOW (20% Weight)
Analyze:
✓ Logical flow: Headline → Subhead → Body → CTA progression?
✓ Simplicity: Easy to understand at a glance?
✓ Coherence: All elements support single message?
✓ Readability: Appropriate length and complexity for poster?
✓ Word choice: Clear, specific, and impactful language?
CATEGORY 4: CTA & CONVERSION ELEMENTS (15% Weight)
Analyze:
✓ CTA clarity: Clear action verb (Shop Now, Learn More, Get Started)?
✓ Urgency: Creates motivation to act immediately?
✓ Placement: Logical position in copy hierarchy?
✓ Strength: Compelling enough to drive action?
✓ Value: Communicates benefit of taking action?
CATEGORY 5: BRAND VOICE & AUDIENCE FIT (10% Weight)
Analyze:
✓ Brand consistency: Tone aligns with brand guidelines?
✓ Audience targeting: Language resonates with intended viewers?
✓ Authenticity: Feels genuine, not forced or overly salesy?
✓ Differentiation: Stands out from competitor messaging?
✓ Emotional connection: Creates desired feeling or response?
═══════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT (Copy Exactly)
═══════════════════════════════════════════════════
POSTER COPY QC ANALYSIS
Copy Length: {len(text.split())} words | Character Count: {len(text)} characters
───────────────────────────────────────────────────
CATEGORY 1: HEADLINE EFFECTIVENESS (30% Weight)
───────────────────────────────────────────────────

[If no issues: "✓ All good"]

✗ ISSUES FOUND:

[BLOCKER/HIGH/MEDIUM] - [Issue title]
Current Headline: "[Quote exact headline]"
Problem: [Why this headline is weak, what's missing, clarity issues]


SCORE: [X]/10
Deductions:

-[X] points: [Specific issue - e.g., "headline too generic, lacks hook"]
-[X] points: [Specific issue - e.g., "unclear value proposition"]

───────────────────────────────────────────────────
CATEGORY 2: GRAMMAR & SPELLING (25% Weight)
───────────────────────────────────────────────────

[If no issues: "✓ All good"]

✗ ISSUES FOUND:

[BLOCKER/HIGH/MEDIUM] - [Issue title]
Current Text: "[Quote exact problematic text]"
Problem: [Grammar error, spelling mistake, punctuation issue]


SCORE: [X]/10
Deductions:

-[X] points: [Specific issue - e.g., "spelling error in headline"]
-[X] points: [Specific issue - e.g., "missing apostrophe in body copy"]

───────────────────────────────────────────────────
CATEGORY 3: MESSAGE CLARITY & FLOW (20% Weight)
───────────────────────────────────────────────────

[If no issues: "✓ All good"]

✗ ISSUES FOUND:

[BLOCKER/HIGH/MEDIUM] - [Issue title]
Current Copy: "[Quote relevant section]"
Problem: [Clarity issue, flow problem, confusing structure, word choice]


SCORE: [X]/10
Deductions:

-[X] points: [Specific issue - e.g., "subhead doesn't support headline"]
-[X] points: [Specific issue - e.g., "jargon reduces clarity"]

───────────────────────────────────────────────────
CATEGORY 4: CTA & CONVERSION ELEMENTS (15% Weight)
───────────────────────────────────────────────────

[If no issues: "✓ All good"]

✗ ISSUES FOUND:

[BLOCKER/HIGH/MEDIUM] - [Issue title]
Current CTA: "[Quote exact CTA text]"
Problem: [Weak action word, unclear benefit, poor placement, no urgency]


SCORE: [X]/10
Deductions:

-[X] points: [Specific issue - e.g., "CTA uses generic 'Click Here'"]
-[X] points: [Specific issue - e.g., "no urgency or incentive"]

───────────────────────────────────────────────────
CATEGORY 5: BRAND VOICE & AUDIENCE FIT (10% Weight)
───────────────────────────────────────────────────

[If no issues: "✓ All good"]

✗ ISSUES FOUND:

[BLOCKER/HIGH/MEDIUM] - [Issue title]
Problem: [Tone mismatch, audience disconnect, brand guideline deviation]

SCORE: [X]/10
Deductions:

-[X] points: [Specific issue - e.g., "tone too formal for target audience"]
-[X] points: [Specific issue - e.g., "doesn't match brand voice guidelines"]

═══════════════════════════════════════════════════
OVERALL COPY PERFORMANCE
═══════════════════════════════════════════════════
📊 WEIGHTED OVERALL SCORE: [X.X]/10
Calculation:

Headline Effectiveness (30%): [X]/10 × 0.30 = [X.XX]
Grammar & Spelling (25%): [X]/10 × 0.25 = [X.XX]
Message Clarity & Flow (20%): [X]/10 × 0.20 = [X.XX]
CTA & Conversion (15%): [X]/10 × 0.15 = [X.XX]
Brand Voice & Audience (10%): [X]/10 × 0.10 = [X.XX]
Total: [X.X]/10

🎯 PERFORMANCE PREDICTION:
[Will this copy drive attention and action? Is it professional and error-free? Will the target audience connect with it? Why or why not?]
═══════════════════════════════════════════════════
PRIORITY ACTION ITEMS
═══════════════════════════════════════════════════
🚨 CRITICAL (Fix Before Production):

[Most critical copy issue blocking production]
[Second critical issue]

⚠️ HIGH PRIORITY (Fix Before Printing):

[Important issue affecting effectiveness]
[Another important issue]

📋 RECOMMENDED IMPROVEMENTS:

[Enhancement for better performance]
[Polish suggestion for engagement]

───────────────────────────────────────────────────
PRODUCTION STATUS: [BLOCKED / NEEDS REVISION / READY WITH NOTES / READY TO PRINT]
───────────────────────────────────────────────────
═══════════════════════════════════════════════════
STRICT SCORING SYSTEM
═══════════════════════════════════════════════════
Start each category at 10/10, then deduct:
Headline Effectiveness (30% weight):

-4 points: Headline generic, boring, or confusing
-3 points: Weak hook or unclear value proposition
-2 points: Too long or doesn't match audience
-1 point: Good but could be more impactful
-1 point: Minor word choice improvements needed

Grammar & Spelling (25% weight):

-4 points: Multiple spelling/grammar errors
-3 points: Spelling error in headline or CTA
-3 points: Grammar error that changes meaning
-2 points: Punctuation errors or inconsistent caps
-1 point: Minor typo in body copy

Message Clarity & Flow (20% weight):

-3 points: Confusing message or poor logical flow
-2 points: Subhead doesn't support headline
-2 points: Copy too long or complex for poster format
-1 point: Minor word choice or readability issues
-1 point: Could be more concise

CTA & Conversion Elements (15% weight):

-4 points: Missing CTA or completely unclear
-3 points: Weak CTA with generic wording
-2 points: CTA lacks urgency or benefit
-1 point: CTA placement could be better
-1 point: Could be more action-oriented

Brand Voice & Audience Fit (10% weight):

-3 points: Significantly off-brand tone
-2 points: Doesn't resonate with target audience
-2 points: Too salesy or inauthentic
-1 point: Minor tone adjustments needed
-1 point: Could better match brand guidelines

Score Interpretation:

9-10: Excellent - Ready to print, high conversion potential
7-8: Good - Minor tweaks for better performance
5-6: Needs Work - Several improvements required
3-4: Poor - Major copy revision needed
0-2: Critical - Complete rewrite recommended

═══════════════════════════════════════════════════
QUALITY CONTROL RULES - NEVER VIOLATE
═══════════════════════════════════════════════════
✅ ALWAYS DO:

Quote exact problematic copy text
Check EVERY word for spelling/grammar
Evaluate headline impact and clarity
Verify CTA uses strong action verbs
Assess copy length for poster readability
Consider target audience language level
Show weighted scoring calculation
Think about visual hierarchy and flow

❌ NEVER DO:

Miss spelling or grammar errors (zero tolerance)
Overlook weak or generic headlines
Ignore CTA effectiveness (conversion critical)
Skip brand voice verification
Inflate scores without justification
Be vague about specific fixes needed
Forget to check product names/prices/claims
Miss punctuation that changes meaning

═══════════════════════════════════════════════════
POSTER FORMAT-SPECIFIC CHECKS
═══════════════════════════════════════════════════
Social Media Posters (Instagram/Facebook):

Headline: 5-10 words maximum
Body copy: 15-30 words ideal
CTA: Must be visible and clear
Tone: Casual, conversational, engaging

Display Banners (Digital Ads):

Headline: Short and punchy (3-7 words)
Body: Minimal text, focus on benefit
CTA: Strong action verb required
Message: Instant clarity critical

Print Posters (Physical Materials):

Headline: Large, bold, readable from distance
Body: Concise supporting points only
CTA: Clear instructions or contact info
Copy: Professional polish essential

Email/Newsletter Graphics:

Headline: Curiosity-driven or benefit-focused
Body: 2-3 short sentences maximum
CTA: Button-ready text with urgency
Tone: Matches email campaign voice

═══════════════════════════════════════════════════
COPY-SPECIFIC RED FLAGS TO CATCH
═══════════════════════════════════════════════════
Headline Problems:

Generic phrases ("Best deals," "Quality products")
Too long (over 12 words for poster)
Unclear benefit or value proposition
Boring or expected (no surprise factor)
Uses passive voice instead of active

Grammar Traps:

Its vs. It's
Your vs. You're
Their/There/They're
Affect vs. Effect
Then vs. Than
Comma splices and run-on sentences
Missing or incorrect apostrophes

Message Issues:

Jargon or technical terms for general audience
Conflicting or confusing messaging
Too much information for poster format
Buried benefit (not upfront)
No clear differentiator

CTA Failures:

Generic wording ("Click Here," "Learn More" without context)
No urgency or incentive
Unclear what happens after action
Multiple conflicting CTAs
Passive language instead of command

Brand Voice Problems:

Tone too formal or casual for brand
Inconsistent with other brand materials
Doesn't speak to target demographic
Overly salesy or pushy language

═══════════════════════════════════════════════════
FINAL CHECKLIST BEFORE SUBMITTING
═══════════════════════════════════════════════════
Before finalizing, verify you have:
☐ Checked every single word for spelling
☐ Verified grammar and punctuation throughout
☐ Evaluated headline attention-grabbing power
☐ Confirmed message clarity and flow
☐ Assessed CTA strength and action orientation
☐ Quoted exact problematic copy text
☐ Shown weighted score calculation
☐ Categorized all issues (BLOCKER/HIGH/MEDIUM)
☐ Considered poster format constraints
☐ Verified brand voice consistency
☐ Checked product names, prices, claims accuracy
☐ Given clear PRODUCTION STATUS
═══════════════════════════════════════════════════
REMEMBER: This copy will be read in 2-3 seconds by scrolling or passing viewers. Your job is to ensure it GRABS attention, COMMUNICATES clearly, and DRIVES action—all while being 100% error-free and on-brand. Be thorough, be critical, be specific.
Now analyze this poster copy following this exact structure  and get them all done under 150-170 words."""

        print(f"🤖 Sending to Groq Text API (Llama 3.3 70B)...")
        print(f"   Content Type: {'REEL/VIDEO SCRIPT' if is_reel else 'POSTER COPY'}")
        
        completion = get_groq_client().chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
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
            quote_placeholders[placeholder] = f'<span style="background:#FFD700;color:#000000;padding:2px 6px;border-radius:3px;font-style:italic;font-weight:500;">"{quote}"</span>'
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
        
        html = f"""<div style="font-family:'Segoe UI',Arial,sans-serif;font-size:14px;color:#f8f9fa;background:#2c3e50;padding:20px;border-radius:10px;text-align:center;">
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
        
        html = f"""<div style="font-family:'Segoe UI',Arial,sans-serif;font-size:14px;color:#f8f9fa;background:#27ae60;padding:20px;border-radius:10px;text-align:center;">
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

        # Get project configuration
        project_config = get_project_config(pid)
        if project_config:
            brand_context = project_config["brand_context"]
        else:
            brand_context = ""

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
        print(f"🔄 Processing task synchronously...")
        process_qc_task(task)
        print("="*60)
        print(f"✅ WEBHOOK COMPLETED - Task processed synchronously")
        print("="*60 + "\n")
        return jsonify({"status": "processed"}), 200

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
