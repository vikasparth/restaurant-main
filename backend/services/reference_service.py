async def generate_reference_number(db) -> str:
    """Generate a unique reference number using the Postgres sequence.
    Format: AKR-YYYYMMDD-XXXX (e.g. AKR-20260409-0042)
    """
    return await db.fetchval("SELECT public.generate_reference_number()")
