"""Engineer safety guidance tool."""


def safety_notice() -> tuple[str, list[str], list[str], str]:
    return (
        "Engineering safety guidance: isolate and lock out the equipment, verify zero energy state, "
        "consult the applicable model manual, and escalate unresolved faults to the service lead.",
        ["Jenga engineering safety procedure"],
        ["Follow site-specific isolation procedures and applicable Kenyan safety regulations."],
        "medium",
    )
