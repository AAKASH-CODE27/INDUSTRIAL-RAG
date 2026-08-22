from app.models.failure import Failure
from app.models.machine import Machine


def normalize_failure_record(failure: Failure, machine: Machine | None = None) -> str:
    machine_code = machine.machine_code if machine else f"Machine-{failure.machine_id}"

    return "\n".join(
        [
            f"Machine: {machine_code}",
            f"Failure Code: {failure.failure_code}",
            f"Failure Type: {failure.failure_type}",
            f"Severity: {failure.severity}",
            f"Symptoms: {failure.symptoms}",
            f"Root Cause: {failure.root_cause}",
            f"Resolution: {failure.resolution}",
        ]
    )
