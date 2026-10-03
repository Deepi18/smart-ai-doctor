import os
import json
from config import Config

class SymptomOntologyManager:
    """Centralized Symptom Normalization & Canonical Ontology Manager."""

    def __init__(self):
        self.ontology_path = os.path.join(Config.DATA_DIR, 'symptom_ontology.json')
        self.ontology = {}
        self.synonym_lookup = {}
        self._load_ontology()

    def _load_ontology(self):
        """Loads symptom_ontology.json and indexes synonyms."""
        if not os.path.exists(self.ontology_path):
            print(f"[Ontology Manager] Warning: {self.ontology_path} not found.")
            return

        with open(self.ontology_path, 'r', encoding='utf-8') as f:
            self.ontology = json.load(f)

        # Build fast lower-case synonym lookup dictionary
        for sym_id, data in self.ontology.items():
            canonical_name = data["canonical_name"]
            # Map canonical name to itself
            self.synonym_lookup[canonical_name.lower()] = data
            
            # Map all synonyms
            for syn in data.get("synonyms", []):
                self.synonym_lookup[syn.lower()] = data

    def normalize_symptom(self, symptom_text):
        """
        Maps raw symptom phrase to its canonical symptom metadata dictionary.
        Returns None if phrase is not recognized in ontology.
        """
        if not symptom_text:
            return None
        clean_text = symptom_text.strip().lower()
        return self.synonym_lookup.get(clean_text, None)

    def get_canonical_name(self, symptom_text):
        """Returns normalized canonical symptom string or original string if unmatched."""
        matched = self.normalize_symptom(symptom_text)
        return matched["canonical_name"] if matched else symptom_text.strip()

    def get_all_canonical_symptoms(self):
        """Returns list of all canonical symptom names."""
        return [data["canonical_name"] for data in self.ontology.values()]

# Singleton Manager Instance
ontology_manager = SymptomOntologyManager()
