import re


DOCUMENT_METADATA = {
    "01_CNC_Machine_Operation_Manual": {
        "document_name": "CNC Machine Operation Manual",
        "document_type": "manual",
        "machine_type": "CNC",
    },
    "02_Preventive_Maintenance_Manual": {
        "document_name": "CNC Preventive Maintenance Manual",
        "document_type": "maintenance",
        "machine_type": "CNC",
    },
    "03_Spindle_Bearing_Maintenance_Guide": {
        "document_name": "Spindle and Bearing Maintenance Guide",
        "document_type": "maintenance",
        "machine_type": "CNC",
    },
    "04_Motor_Troubleshooting_Guide": {
        "document_name": "Industrial Motor Troubleshooting Guide",
        "document_type": "troubleshooting",
        "machine_type": "CNC",
    },
    "05_Vibration_Troubleshooting_Guide": {
        "document_name": "Industrial Vibration Troubleshooting Guide",
        "document_type": "troubleshooting",
        "machine_type": "CNC",
    },
    "06_Hydraulic_System_Troubleshooting_Guide": {
        "document_name": "Hydraulic System Troubleshooting Guide",
        "document_type": "troubleshooting",
        "machine_type": "industrial",
    },
    "07_Industrial_Safety_and_Lockout_Tagout_Guide": {
        "document_name": "Industrial Safety and Lockout Tagout Guide",
        "document_type": "safety",
        "machine_type": "industrial",
    },
    "08_Industrial_Error_Code_Reference": {
        "document_name": "Industrial Error Code Reference",
        "document_type": "error_codes",
        "machine_type": "industrial",
    },
}


def get_metadata(document_id: str) -> dict:
    metadata = DOCUMENT_METADATA.get(document_id)

    if metadata is None:
        return {
            "document_name": document_id,
            "document_type": "unknown",
            "machine_type": "unknown",
        }

    return metadata.copy()


def detect_section(text: str) -> str:
    """
    Find the first numbered section heading.

    Example:
        3. Spindle System
    """

    match = re.search(
        r"(?m)^\s*(\d+)\.\s+(.+?)\s*$",
        text,
    )

    if match:
        return match.group(2).strip()

    return "Unknown"