"""
Seed Model Pricing Data - Simplified Version
Uses raw SQL to avoid SQLAlchemy model issues

File: backend/scripts/seed_model_pricing.py
Version: 2.1 SIMPLIFIED
"""

import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add backend to path
# sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, text
from app.core.config import settings


def seed_pricing():
    """
    Seed pricing data for popular LLM models using raw SQL
    """
    
    # Create engine
    engine = create_engine("postgresql://postgres:postgres@localhost:5433/agenticbase2")
    
    print("=" * 70)
    print("🌱 MODEL PRICING SEEDER")
    print("=" * 70)
    # print(f"Database: {settings.DATABASE_URL.split('@')[1]}")
    print("=" * 70)
    
    try:
        with engine.connect() as conn:
            # Define all models with pricing
            models = [
                # ============================================================
                # OpenAI Models
                # ============================================================
                ('openai', 'gpt-4', '0613', 0.03, 0.06, 0, 0, 
                 'GPT-4 (8K context)', 'https://openai.com/pricing'),
                
                ('openai', 'gpt-4-32k', '0613', 0.06, 0.12, 0, 0,
                 'GPT-4 (32K context)', 'https://openai.com/pricing'),
                
                ('openai', 'gpt-4-turbo', 'turbo-2024-04-09', 0.01, 0.03, 0, 0,
                 'GPT-4 Turbo (128K context)', 'https://openai.com/pricing'),
                
                ('openai', 'gpt-4o', '2024-08-06', 0.0025, 0.01, 0, 0,
                 'GPT-4o (optimized)', 'https://openai.com/pricing'),
                
                ('openai', 'gpt-4o-mini', '2024-07-18', 0.00015, 0.0006, 0, 0,
                 'GPT-4o Mini (fast and affordable)', 'https://openai.com/pricing'),
                
                ('openai', 'gpt-3.5-turbo', '0125', 0.0005, 0.0015, 0, 0,
                 'GPT-3.5 Turbo (16K context)', 'https://openai.com/pricing'),
                
                ('openai', 'gpt-3.5-turbo-16k', '0125', 0.001, 0.002, 0, 0,
                 'GPT-3.5 Turbo 16K', 'https://openai.com/pricing'),
                
                # ============================================================
                # Anthropic Models
                # ============================================================
                ('anthropic', 'claude-3-opus', '20240229', 0.015, 0.075, 0.0015, 0.00375,
                 'Claude 3 Opus (200K context)', 'https://anthropic.com/pricing'),
                
                ('anthropic', 'claude-3-sonnet', '20240229', 0.003, 0.015, 0.0003, 0.00075,
                 'Claude 3 Sonnet (200K context)', 'https://anthropic.com/pricing'),
                
                ('anthropic', 'claude-3-haiku', '20240307', 0.00025, 0.00125, 0.000025, 0.0000625,
                 'Claude 3 Haiku (200K context)', 'https://anthropic.com/pricing'),
                
                ('anthropic', 'claude-3.5-sonnet', '20241022', 0.003, 0.015, 0.0003, 0.00075,
                 'Claude 3.5 Sonnet (200K context)', 'https://anthropic.com/pricing'),
                
                ('anthropic', 'claude-3.5-haiku', '20241022', 0.0008, 0.004, 0.00008, 0.0002,
                 'Claude 3.5 Haiku (200K context)', 'https://anthropic.com/pricing'),
                
                # ============================================================
                # Google Models
                # ============================================================
                ('google', 'gemini-pro', '1.0', 0.00025, 0.00075, 0, 0,
                 'Gemini Pro', 'https://ai.google.dev/pricing'),
                
                ('google', 'gemini-pro-vision', '1.0', 0.00025, 0.00075, 0, 0,
                 'Gemini Pro Vision', 'https://ai.google.dev/pricing'),
                
                # ============================================================
                # Mistral Models
                # ============================================================
                ('mistral', 'mistral-small', 'latest', 0.0006, 0.0018, 0, 0,
                 'Mistral Small', 'https://mistral.ai/pricing'),
                
                ('mistral', 'mistral-medium', 'latest', 0.0027, 0.0081, 0, 0,
                 'Mistral Medium', 'https://mistral.ai/pricing'),
                
                ('mistral', 'mistral-large', 'latest', 0.004, 0.012, 0, 0,
                 'Mistral Large', 'https://mistral.ai/pricing'),
                
                # ============================================================
                # Meta/Llama Models (via providers like Together, Replicate)
                # ============================================================
                ('meta', 'llama-3-8b', '3.0', 0.0002, 0.0003, 0, 0,
                 'Llama 3 8B', 'https://www.llama.com/pricing'),
                
                ('meta', 'llama-3-70b', '3.0', 0.0007, 0.0009, 0, 0,
                 'Llama 3 70B', 'https://www.llama.com/pricing'),
                
                # ============================================================
                # Self-Hosted Models (estimated infrastructure costs)
                # ============================================================
                ('self-hosted', 'llama-2-7b', '2.0', 0.0001, 0.0001, 0, 0,
                 'Llama 2 7B (infrastructure cost estimate)', 'internal'),
                
                ('self-hosted', 'llama-2-13b', '2.0', 0.0002, 0.0002, 0, 0,
                 'Llama 2 13B (infrastructure cost estimate)', 'internal'),
                
                ('self-hosted', 'llama-2-70b', '2.0', 0.001, 0.001, 0, 0,
                 'Llama 2 70B (infrastructure cost estimate)', 'internal'),
                
                ('self-hosted', 'mistral-7b', '0.1', 0.0001, 0.0001, 0, 0,
                 'Mistral 7B (infrastructure cost estimate)', 'internal'),
                
                ('self-hosted', 'mixtral-8x7b', '0.1', 0.0005, 0.0005, 0, 0,
                 'Mixtral 8x7B (infrastructure cost estimate)', 'internal'),
            ]
            
            inserted_count = 0
            updated_count = 0
            
            print(f"\n🔍 Processing {len(models)} models...")
            print("-" * 70)
            
            for model_data in models:
                (provider, name, version, input_cost, output_cost, 
                 cache_read, cache_write, notes, source) = model_data
                
                # Check if model exists
                check_query = text("""
                    SELECT id FROM public.model_pricing
                    WHERE model_provider = :provider
                        AND model_name = :name
                        AND active = true
                """)
                
                result = conn.execute(check_query, {
                    'provider': provider,
                    'name': name
                })
                existing = result.fetchone()
                
                if existing:
                    # Update existing
                    update_query = text("""
                        UPDATE public.model_pricing
                        SET 
                            input_cost_per_1k = :input_cost,
                            output_cost_per_1k = :output_cost,
                            cache_read_per_1k = :cache_read,
                            cache_write_per_1k = :cache_write,
                            model_version = :version,
                            notes = :notes,
                            source_url = :source,
                            updated_at = NOW()
                        WHERE id = :id
                    """)
                    
                    conn.execute(update_query, {
                        'input_cost': input_cost,
                        'output_cost': output_cost,
                        'cache_read': cache_read,
                        'cache_write': cache_write,
                        'version': version,
                        'notes': notes,
                        'source': source,
                        'id': existing[0]
                    })
                    
                    updated_count += 1
                    print(f"  ⬆️  Updated: {provider:15s} {name:25s} (${input_cost:.6f} / ${output_cost:.6f})")
                else:
                    # Insert new
                    insert_query = text("""
                        INSERT INTO public.model_pricing (
                            model_provider, model_name, model_version,
                            input_cost_per_1k, output_cost_per_1k,
                            cache_read_per_1k, cache_write_per_1k,
                            effective_from, currency, active,
                            notes, source_url,
                            created_at, updated_at
                        ) VALUES (
                            :provider, :name, :version,
                            :input_cost, :output_cost,
                            :cache_read, :cache_write,
                            NOW(), 'USD', true,
                            :notes, :source,
                            NOW(), NOW()
                        )
                    """)
                    
                    conn.execute(insert_query, {
                        'provider': provider,
                        'name': name,
                        'version': version,
                        'input_cost': input_cost,
                        'output_cost': output_cost,
                        'cache_read': cache_read,
                        'cache_write': cache_write,
                        'notes': notes,
                        'source': source
                    })
                    
                    inserted_count += 1
                    print(f"  ➕ Inserted: {provider:15s} {name:25s} (${input_cost:.6f} / ${output_cost:.6f})")
            
            # Commit transaction
            conn.commit()
            
            print("-" * 70)
            print(f"\n✅ SEEDING COMPLETE!")
            print(f"   📊 Total models processed: {len(models)}")
            print(f"   ➕ Inserted: {inserted_count}")
            print(f"   ⬆️  Updated: {updated_count}")
            
            # Display summary by provider
            print(f"\n📈 Summary by provider:")
            summary_query = text("""
                SELECT 
                    model_provider,
                    COUNT(*) as count,
                    MIN(input_cost_per_1k) as min_input,
                    MAX(output_cost_per_1k) as max_output
                FROM public.model_pricing
                WHERE active = true
                GROUP BY model_provider
                ORDER BY model_provider
            """)
            
            results = conn.execute(summary_query)
            for row in results:
                print(f"   {row.model_provider:15s}: {row.count:2d} models "
                      f"(${row.min_input:.6f} - ${row.max_output:.6f})")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("=" * 70)


if __name__ == '__main__':
    seed_pricing()


# END OF FILE - Simplified seed script (no ORM dependency)