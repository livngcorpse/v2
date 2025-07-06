def determine_intent(text: str) -> str:
    lowered = text.lower()
    if any(x in lowered for x in ["create", "make", "build"]):
        return "CREATE"
    elif any(x in lowered for x in ["edit", "modify"]):
        return "EDIT"
    elif "recode" in lowered:
        return "RECODE"
    return "UNSURE"