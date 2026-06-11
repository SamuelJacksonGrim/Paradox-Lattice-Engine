"""Contract enforcement errors for the Paradox Lattice Engine."""


class ContractViolation(Exception):
    """Raised when any module attempts an operation forbidden by a PLE contract.

    Per the contracts: "If a module violates these rules, it is not part of PLE."
    """


class InvalidParadox(ContractViolation):
    """Raised when an object fails the paradox validity conditions."""


class InvalidLifecycleTransition(ContractViolation):
    """Raised on a lifecycle state transition not permitted by the contracts."""


class UnauthorizedMutation(ContractViolation):
    """Raised when a module other than the authorized processor mutates an object."""


class InvalidEvent(ContractViolation):
    """Raised when an invalid event type is emitted (e.g. 'resolved', 'deleted')."""
