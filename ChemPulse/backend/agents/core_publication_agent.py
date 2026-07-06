from __future__ import annotations

import argparse
import os
import uuid

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.config import get_config, get_secret_env, is_api_key_configured
from backend.data.core_publication_repository import CorePublicationRepository
from backend.data.publication_relevance import DEFAULT_MIN_INGESTION_RELEVANCE_SCORE, is_ingestion_relevant
from backend.data.scaffold_publication_matcher import default_scaffold_list_path, refresh_scaffold_matches
from backend.integrations.core_api import CoreApiClient, CoreApiSettings, normalize_core_work

# Fallback Query
fallback_query = (
    ("chemistry" OR 
     "chemical synthesis" OR 
     "catalyst" OR 
     "scaffold" OR 
     "molecule") AND 
    yearPublished:{year})

# Default Query
default_query = (
'(( '
    # General 
    "catalyst" OR "catalysts" OR "catalysis" OR "catalytic" OR
    "organic synthesis catalysis" OR "organic synthesis catalyst" OR
    "chemical synthesis catalysis" OR "chemical synthesis catalyst" OR
    "chemical reaction catalysis" OR "chemical reaction catalyst" OR
    "chemical transformation catalysis" OR "chemical transformation catalyst" OR
    "chemical synthesis reaction catalysis" OR "chemical synthesis reaction catalyst" OR
    "chemical synthesis transformation catalysis" OR "chemical synthesis transformation catalyst" OR
            
    # Transition Metal and Metal-Organic Framework 
    "transition metal catalyst" OR "transition metal catalysis" OR
    "metal-organic framework" OR "metal organic framework" OR
    "metal organic frameworks" OR "metal-organic frameworks" OR
    "metal-organic framework catalysis" OR "metal organic framework catalyst" OR
            
    # Molecular Scaffold and Drug Discovery 
    "molecular scaffold" OR "molecular scaffolds" OR
    "molecular scaffold catalysis" OR "molecular scaffold catalyst" OR
    "chemical scaffold" OR "chemical scaffolds" OR
    "chemical scaffold catalysis" OR "chemical scaffold catalyst" OR
    "medicinal chemistry catalysis" OR "medicinal chemistry catalyst" OR
    "drug discovery" OR "drug discoveries" OR
    "drug discovery catalysis" OR "drug discovery catalyst" OR
            
    # Chemical Engineering
    "chemical process catalysis" OR "chemical process catalyst" OR
    "chemical engineering catalysis" OR "chemical engineering catalyst" OR
    "chemical technology catalysis" OR "chemical technology catalyst" OR
    "chemical industry catalysis" OR "chemical industry catalyst" OR
    "chemical manufacturing catalysis" OR "chemical manufacturing catalyst" OR
    "chemical production catalysis" OR "chemical production catalyst" OR
    "chemical synthesis process catalysis" OR "chemical synthesis process catalyst" OR
    "chemical synthesis engineering catalysis" OR "chemical synthesis engineering catalyst" OR
    "chemical synthesis technology catalysis" OR "chemical synthesis technology catalyst" OR
    "chemical synthesis industry catalysis" OR "chemical synthesis industry catalyst" OR
    "chemical synthesis manufacturing catalysis" OR "chemical synthesis manufacturing catalyst" OR
    "chemical synthesis production catalysis" OR "chemical synthesis production catalyst" OR
            
    # Stereoinvolvment Catalysis - Regioselective, Diastereoselective, Enantioselective
    "asymmetric catalyst" OR "asymmetric catalysis" OR
    "stereogentic catalyst" OR "stereogentic catalysis" OR
    "enantioselective catalyst" OR "enantioselective catalysis" OR
    "enantioselective synthesis" OR "enantioselective syntheses" OR
    "enantioselective synthesis catalysis" OR "enantioselective synthesis catalyst" OR
    "enantioselective reaction" OR "enantioselective reactions" OR
    "enantioselective reaction catalysis" OR "enantioselective reaction catalyst" OR
    "enantioselective transformation" OR "enantioselective transformations" OR
    "enantioselective transformation catalysis" OR "enantioselective transformation catalyst OR
    "diastereoselective catalyst" OR "diastereoselective catalysis" OR
    "diastereoselective synthesis" OR "diastereoselective syntheses" OR
    "diastereoselective synthesis catalysis" OR "diastereoselective synthesis catalyst" OR
    "diastereoselective reaction" OR "diastereoselective reactions" OR
    "diastereoselective reaction catalysis" OR "diastereoselective reaction catalyst" OR
    "diastereoselective transformation" OR "diastereoselective transformations" OR
    "diastereoselective transformation catalysis" OR "diastereoselective transformation catalyst" OR
    "regioselective catalyst" OR "regioselective catalysis" OR
    "regioselective synthesis" OR "regioselective syntheses" OR
    "regioselective synthesis catalysis" OR "regioselective synthesis catalyst" OR
    "regioselective reaction" OR "regioselective reactions" OR
    "regioselective reaction catalysis" OR "regioselective reaction catalyst" OR
    "regioselective transformation" OR "regioselective transformations" OR
    "regioselective transformation catalysis" OR "regioselective transformation catalyst" OR
       
    # Total Synthesis
    "total synthesis" OR "total syntheses" OR ' )'
    
    'AND (chemistry OR synthesis OR reaction OR molecular OR compound) '
    
    'AND publishedDate>={since})'
)


