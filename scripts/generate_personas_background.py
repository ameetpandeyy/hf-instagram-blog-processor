#!/usr/bin/env python3
"""
TeAmo Background Persona Image Generator CLI
Generates unique persona avatars and romantic gallery photos using Gemini API / Hugging Face.
- Auto-compresses every image to strictly under 200 KB
- Direct upload to Supabase Storage 'persona-media' bucket
- Can run locally or inside GitHub Actions / CI workflows
"""

import sys
import os
import asyncio
import argparse
import time

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.image_gen import (
    generate_and_store_persona_image,
    PERSONA_PROMPT_BLUEPRINTS,
    SUPABASE_BUCKET,
)
from app.config import settings

GALLERY_SCENES = ["beach", "club", "travel", "music", "cafe"]

async def main():
    parser = argparse.ArgumentParser(description="TeAmo Persona Image Generator")
    parser.add_argument(
        "--personas",
        type=str,
        default="all",
        help="Comma-separated persona IDs (e.g. sara,nia,zoya) or 'all'"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="all",
        choices=["all", "avatars", "gallery"],
        help="Generate avatars, gallery scenes, or all"
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="auto",
        choices=["auto", "gemini", "huggingface"],
        help="Image generation engine to prioritize"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay in seconds between requests to avoid rate limits"
    )

    args = parser.parse_args()

    print("=" * 65)
    print("✨ TeAmo AI Persona Image Generation Pipeline ✨")
    print(f"• Engine: {args.engine.upper()} (with auto-fallback)")
    print(f"• Mode: {args.mode}")
    print(f"• Supabase Bucket: {SUPABASE_BUCKET}")
    print("=" * 65)

    if args.personas.lower() == "all":
        target_personas = list(PERSONA_PROMPT_BLUEPRINTS.keys())
    else:
        target_personas = [p.strip().lower() for p in args.personas.split(",") if p.strip()]

    total_tasks = 0
    if args.mode in ("all", "avatars"):
        total_tasks += len(target_personas)
    if args.mode in ("all", "gallery"):
        total_tasks += len(GALLERY_SCENES)

    print(f"📋 Total generation tasks queued: {total_tasks}")
    completed = 0
    failed = 0

    # 1. Generate Avatars
    if args.mode in ("all", "avatars"):
        print("\n📸 [1/2] Generating Unique Persona Avatars (1:1)...")
        for idx, pid in enumerate(target_personas, start=1):
            meta = PERSONA_PROMPT_BLUEPRINTS.get(pid, {"name": pid.capitalize(), "city": "India"})
            print(f"\n  [{idx}/{len(target_personas)}] Generating {meta['name']} ({meta['city']})...")
            try:
                res = await generate_and_store_persona_image(
                    persona_id=pid,
                    category="avatars",
                    scene_tag="avatar",
                    engine=args.engine,
                    aspect_ratio="1:1"
                )
                completed += 1
                print(f"  ✓ Success! [{res['engine_used']}] {res['size_kb']} KB")
                print(f"    CDN URL: {res['url']}")
            except Exception as e:
                failed += 1
                print(f"  ❌ Failed for {pid}: {e}")

            if args.delay > 0:
                time.sleep(args.delay)

    # 2. Generate Romantic Gallery Scenes
    if args.mode in ("all", "gallery"):
        print("\n🌅 [2/2] Generating Romantic Gallery Scenes (3:4)...")
        for idx, tag in enumerate(GALLERY_SCENES, start=1):
            print(f"\n  [{idx}/{len(GALLERY_SCENES)}] Generating Scene: '{tag.upper()}'...")
            try:
                sample_pid = target_personas[idx % len(target_personas)]
                res = await generate_and_store_persona_image(
                    persona_id=sample_pid,
                    category="gallery",
                    scene_tag=tag,
                    engine=args.engine,
                    aspect_ratio="3:4"
                )
                completed += 1
                print(f"  ✓ Success! [{res['engine_used']}] {res['size_kb']} KB")
                print(f"    CDN URL: {res['url']}")
            except Exception as e:
                failed += 1
                print(f"  ❌ Failed for scene {tag}: {e}")

            if args.delay > 0:
                time.sleep(args.delay)

    print("\n" + "=" * 65)
    print(f"🏁 Generation Finished: {completed} successful, {failed} failed.")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
