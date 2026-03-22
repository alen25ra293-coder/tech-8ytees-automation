import os
from datetime import datetime
from src.generators.script import _get_model, NICHE, TARGET_AUDIENCE

def _generate_with_retry(prompt: str, attempt: int = 1) -> str:
    model = _get_model()
    if not model:
        return "Error: No Gemini model configured or available."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        if attempt <= 3:
            print(f"   ⚠️ Gemini error: {e}. Retrying ({attempt}/3)...")
            return _generate_with_retry(prompt, attempt + 1)
        return f"Error: Failed to generate content after 3 attempts. Exception: {e}"

def generate_channel_audit(channel_context: str) -> str:
    print("📊 Executing Deep Channel Audit...")
    prompt = f"""Act as a YouTube growth and optimization expert. Perform a deep audit of my YouTube channel using the channel link and videos I provide. Analyze branding, positioning, niche clarity, channel name, banner, about section, playlists, upload consistency, and overall value proposition. Then evaluate individual videos for titles, thumbnails, hooks, retention structure, pacing, video length, CTR signals, and alignment with audience intent. Identify friction points that reduce clicks or watch time. Compare my channel against top competitors in the niche to spot gaps and missed opportunities. Finally, deliver clear, prioritized optimization actions—what to fix immediately, what to test next, and what to scale—specifically tailored for a faceless channel focused on growth and compounding views.
    
    CHANNEL CONTEXT:
    Niche: {NICHE}
    Target Audience: {TARGET_AUDIENCE}
    Channel Info: {channel_context}
    """
    return _generate_with_retry(prompt)

def generate_competitor_analysis() -> str:
    print("🕵️ Executing Competitor Analysis...")
    prompt = f"""Act as a YouTube competitive intelligence analyst. Analyze the top-performing competitors in this niche. Identify what each competitor is doing differently across content strategy, positioning, video formats, upload frequency, length, pacing, hooks, titles, thumbnails, and audience targeting. Map patterns that are working across multiple channels versus tactics unique to individual creators. Highlight gaps, weaknesses, and overlooked opportunities in their strategies. Then translate the analysis into actionable insights: what to copy, what to avoid, and how to position a new faceless channel to stand out while still riding proven demand.
    
    NICHE CONTEXT:
    {NICHE}
    """
    return _generate_with_retry(prompt)

def analyze_thumbnails() -> str:
    print("🖼️ Executing Thumbnail Analysis...")
    prompt = f"""Act as a YouTube thumbnail optimization expert. Analyze the theoretical top-performing thumbnails in this niche. Break down what's driving high click-through rates, including composition, focal hierarchy, facial vs non-facial elements, text usage (or absence), color contrast, emotional signaling, symbolism, framing, and visual simplicity. Identify repeatable patterns and anti-patterns. Then translate the analysis into clear, actionable rules I can follow to recreate thumbnails with similar performance—covering layout templates, do/don't guidelines, and a step-by-step checklist for designing faceless, scroll-stopping thumbnails optimized for YouTube.
    
    NICHE CONTEXT:
    {NICHE}
    """
    return _generate_with_retry(prompt)

def analyze_scripts(competitor_analysis: str) -> str:
    print("📜 Executing Script Analysis...")
    prompt = f"""Act as a YouTube retention and storytelling strategist. Analyze the script structures of successful videos in this niche with over 500,000 views. Break down the script structure step by step, including the opening hook, curiosity gaps, pacing, pattern interruptions, information reveals, escalation, and the ending (CTA or deliberate lack of one). Identify the exact techniques used to hold attention, such as open loops, contrasts, stakes, re-hooks, and resets. Extract repeatable frameworks, structural formulas, and line-level patterns that can be reused across multiple videos. Then synthesize your findings into a clear, repeatable script template, with section-by-section guidance, timing suggestions, and example placeholder lines optimized for faceless narration and high retention.
    
    NICHE CONTEXT:
    {NICHE}
    
    COMPETITOR CONTEXT TO CONSIDER:
    {competitor_analysis}
    """
    return _generate_with_retry(prompt)

def generate_script_outlines(script_framework: str) -> str:
    print("📝 Generating Script Outlines...")
    prompt = f"""Using the frameworks, patterns, and script blueprint extracted from the previous analysis, generate high-retention script outlines for my YouTube videos in this niche. Each outline should follow the proven structure exactly, adapted to a new topic. Break each script into clear sections (hook, escalation beats, information reveals, re-hooks, payoff, ending), include approximate timing for each segment, and note the specific retention technique being used at every step. Write short example placeholder lines for each section that are optimized for faceless narration and curiosity-driven delivery. The goal is not full scripts, but repeatable, plug-and-play outlines designed to maximize watch time and scalability.
    
    NICHE CONTEXT:
    {NICHE}
    
    SCRIPT FRAMEWORK EXTRACTED:
    {script_framework}
    """
    return _generate_with_retry(prompt)

def generate_viral_ideas(competitor_analysis: str) -> str:
    print("💡 Generating 30 Viral Video Ideas...")
    prompt = f"""Using the high-velocity niche selected and competitive analysis, generate 30 viral-designed video ideas for a faceless YouTube channel. Each idea should be built around proven viral mechanics (curiosity gaps, polarity, authority, trend-surfing, or pattern interruption). For every idea, include a compelling working title, the core hook in one sentence, and the primary emotional trigger driving clicks. Favor formats that are fast to produce, repeatable, and optimized for retention. Avoid generic ideas—each concept should feel native to the niche and capable of standing out in a crowded feed.
    
    NICHE CONTEXT:
    {NICHE}
    
    COMPETITIVE INSIGHTS:
    {competitor_analysis}
    """
    return _generate_with_retry(prompt)

def run_full_strategy_pipeline(channel_context: str = "Tech 8ytees channel. 24-26 second vertical shorts."):
    print("\n" + "="*50)
    print("🚀 INITIALIZING YOUTUBE STRATEGY AI PIPELINE")
    print("="*50 + "\n")
    
    # 1. Channel Audit
    audit = generate_channel_audit(channel_context)
    
    # 2. Competitor Analysis
    comp_analysis = generate_competitor_analysis()
    
    # 3. Ideas using Competitor Context
    ideas = generate_viral_ideas(comp_analysis)
    
    # 4. Thumbnail Analysis
    thumbnails = analyze_thumbnails()
    
    # 5. Script Framework Analysis
    script_analysis = analyze_scripts(comp_analysis)
    
    # 6. Actionable Script Outlines
    script_outlines = generate_script_outlines(script_analysis)
    
    print("\n✅ All AI components generated successfully. Compiling report...")
    
    # Compile the final document
    report = f"""# Comprehensive YouTube Growth Strategy
*Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

## 1. Deep Channel Audit
{audit}

---
## 2. Competitor Intelligence
{comp_analysis}

---
## 3. 30 Viral Video Ideas
{ideas}

---
## 4. Thumbnail Strategy (Faceless)
{thumbnails}

---
## 5. High-Retention Script Framework
{script_analysis}

---
## 6. Plug-and-Play Script Outlines
{script_outlines}
"""

    os.makedirs("reports", exist_ok=True)
    filename = f"reports/strategy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"🎉 Strategy Report successfully exported to: {filename}")
    return filename

if __name__ == "__main__":
    run_full_strategy_pipeline()
