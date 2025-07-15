from typing import Literal


Domain = Literal[
    "pl",
    "fr",
    "at",
    "be",
    "cz",
    "de",
    "dk",
    "es",
    "fi",
    "gr",
    "hr",
    "hu",
    "it",
    "lt",
    "lu",
    "nl",
    "pt",
    "ro",
    "se",
    "sk",
    "co.uk",
    "com",
]

Language = Literal[
  "pl-PL", 
  "fr-FR", 
  "de-DE", 
  "es-ES", 
  "fi-FI",
  "hr-HR", 
  "hu-HU", 
  "it-IT", 
  "lt-LT", 
  "nl-NL", 
  "pt-PT", 
  "ro-RO", 
  "sv-SE", 
  "sk-SK", 
  "en-US",
]

SortOption = Literal[
    "relevance", "price_high_to_low", "price_low_to_high", "newest_first"
]
