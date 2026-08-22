from app.models.machine import Machine
from app.models.maintenance import MaintenanceRecord


def normalize_maintenance_record(record: MaintenanceRecord, machine: Machine | None = None) -> str:
    machine_code = machine.machine_code if machine else f"Machine-{record.machine_id}"

    return "\n".join(
        [
            f"Machine: {machine_code}",
            f"Maintenance Type: {record.maintenance_type}",
            f"Description: {record.description}",
            f"Findings: {record.findings}",
            f"Action Taken: {record.action_taken}",
            f"Parts Replaced: {record.parts_replaced or 'None'}",
            f"Technician: {record.technician}",
        ]
    )
