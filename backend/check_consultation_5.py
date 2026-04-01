import asyncio
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings
from models.consultation import Consultation

async def check_consultation_5():
    """Check if consultation 5 has structured output"""
    
    # Create engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with AsyncSessionLocal() as session:
        # Query consultation 5
        result = await session.execute(
            select(Consultation).filter(Consultation.id == 5)
        )
        consultation = result.scalar_one_or_none()
        
        print("="*70)
        print("📋 CONSULTATION ID 5 - STRUCTURING CHECK")
        print("="*70)
        
        if consultation:
            print(f"\n✅ Consultation found!")
            print(f"\nID: {consultation.id}")
            print(f"Patient ID: {consultation.patient_id}")
            print(f"Doctor ID: {consultation.doctor_id}")
            print(f"Status: {consultation.status}")
            
            print(f"\n📝 TRANSCRIPT:")
            if consultation.transcript:
                preview = consultation.transcript[:150]
                print(f"✅ EXISTS")
                print(f"   Preview: {preview}...")
            else:
                print(f"❌ EMPTY or NULL")
            
            print(f"\n📊 STRUCTURED_OUTPUT:")
            if consultation.structured_output:
                print(f"✅ EXISTS (Structuring worked!)")
                print(f"   Type: {type(consultation.structured_output).__name__}")
                
                if isinstance(consultation.structured_output, dict):
                    print(f"   Keys: {list(consultation.structured_output.keys())}")
                    print(f"\n📋 Full JSON Output:")
                    print(json.dumps(consultation.structured_output, indent=2))
                else:
                    print(f"   Raw: {consultation.structured_output}")
            else:
                print(f"❌ EMPTY or NULL (Structuring did NOT work)")
                print(f"\n   This means:")
                print(f"   1. Audio was received ✓")
                print(f"   2. Transcript was created ✓")
                print(f"   3. BUT structuring with Ollama FAILED ✗")
        else:
            print(f"\n❌ Consultation ID 5 not found in database")
        
        print("\n" + "="*70)
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_consultation_5())
