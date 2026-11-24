"""Resolve benchmark document identifiers against an external corpus inventory."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

Json = dict[str, Any]


def fingerprint(value: object) -> str:
    """Hash a JSON value with a fixed encoding."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()


@dataclass(frozen=True)
class Corpus:
    """A pinned inventory; incomplete inventories cannot establish absence."""

    revision: str
    complete: bool
    documents: dict[str, Json]
    aliases: dict[str, str]
    sha256: str

    @classmethod
    def from_json(cls, value: Json) -> Corpus:
        """Validate document identities and direct alias mappings."""
        revision = value.get("corpus_revision")
        documents = value.get("documents")
        aliases = value.get("aliases", {})
        if not isinstance(revision, str) or not revision.strip():
            raise ValueError("Corpus requires a revision")
        if type(value.get("complete")) is not bool:
            raise ValueError("Corpus requires explicit inventory completeness")
        if not isinstance(documents, dict) or not documents:
            raise ValueError("Corpus requires a nonempty document inventory")
        for key, document in documents.items():
            if not isinstance(key, str) or not key or not isinstance(document, dict):
                raise ValueError("Invalid corpus document")
            if any(
                field in document and not isinstance(document[field], str)
                for field in ("name", "statement", "context", "module")
            ):
                raise ValueError("Document evidence must be text")
        if not isinstance(aliases, dict):
            raise ValueError("Aliases must be a mapping")
        for alias, target in aliases.items():
            if (
                not isinstance(alias, str)
                or not alias
                or alias in documents
                or not isinstance(target, str)
                or target not in documents
            ):
                raise ValueError("Alias must point directly to one canonical document")
        return cls(revision, value["complete"], documents, aliases, fingerprint(value))

    def resolve(self, identifier: str) -> str | None:
        """Resolve a canonical ID or an explicitly supplied equivalent ID."""
        if identifier in self.documents:
            return identifier
        return self.aliases.get(identifier)

    def availability(self, identifier: str) -> Json:
        """Keep missing names separate from unanswerable information needs."""
        canonical = self.resolve(identifier)
        return {
            "identifier": identifier,
            "document_id": canonical,
            "status": (
                "present"
                if canonical is not None
                else "absent"
                if self.complete
                else "unresolved"
            ),
        }

    def require(self, identifier: str) -> str:
        """Refuse to score an identifier outside the verified inventory."""
        resolved = self.resolve(identifier)
        if resolved is None:
            raise ValueError("Scored document does not resolve in the corpus")
        return resolved
