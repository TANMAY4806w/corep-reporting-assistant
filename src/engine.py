"""
COREP Reporting Engine
Processes regulatory reporting scenarios using LLM-based extraction and structured validation.
Supports hybrid input modes: narrative scenarios and raw numerical values.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
from google import genai

# Configure structured logging for audit trail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


def _is_numeric_input(user_input: str) -> bool:
    """
    Detect if input is purely numeric (with optional whitespace, commas, decimal points).
    
    Args:
        user_input: Raw user input string
        
    Returns:
        True if input represents a single numeric value, False otherwise
    """
    # Strip whitespace and check if input matches numeric pattern
    cleaned = user_input.strip()
    # Pattern: optional negative sign, digits with optional commas/decimals
    numeric_pattern = r'^-?\d{1,3}(,?\d{3})*(\.\d+)?$'
    return bool(re.match(numeric_pattern, cleaned))


def _sanitize_json_response(raw_response: str) -> str:
    """
    Robust JSON sanitization to handle various LLM output formats.
    
    Handles:
    - Markdown code fences (```json, ```)
    - Leading/trailing whitespace and newlines
    - Nested code blocks
    - Mixed formatting artifacts
    
    Args:
        raw_response: Raw LLM response text
        
    Returns:
        Cleaned JSON string ready for parsing
    """
    cleaned = raw_response.strip()
    
    # Remove markdown code fences (multiple passes for nested blocks)
    cleaned = re.sub(r'^```json\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^```\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    
    # Remove any remaining backticks at start/end
    cleaned = cleaned.strip('`').strip()
    
    # Remove leading/trailing whitespace including newlines
    cleaned = cleaned.strip()
    
    return cleaned


def _create_numeric_result(value: float, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate structured result for numeric-only input.
    Automatically maps to R010 (Common Equity Tier 1 Capital).
    
    Args:
        value: Numeric value extracted from input
        schema: Loaded schema dictionary for validation
        
    Returns:
        Structured result dictionary with R010 mapping
    """
    # Find R010 row definition in schema
    r010_row = next(
        (row for row in schema.get('rows', []) if row['id'] == 'R010'),
        {'id': 'R010', 'name': 'Common Equity Tier 1 Capital'}
    )
    
    return {
        "results": [
            {
                "row_id": "R010",
                "field_name": r010_row['name'],
                "value": value,
                "justification": "CA1-0010 (Auto-mapped from numeric input)"
            }
        ]
    }


def process_reporting_scenario(user_scenario: str) -> Dict[str, Any]:
    """
    Process regulatory reporting scenario using hybrid input detection.
    
    Workflow:
    1. Detect input type (numeric vs narrative)
    2. For numeric: auto-map to R010 (CET1 Capital)
    3. For narrative: perform full LLM-based extraction
    4. Sanitize and validate JSON response
    5. Return structured results with audit trail
    
    Args:
        user_scenario: User input (narrative description or raw numeric value)
        
    Returns:
        Dictionary containing:
        - results: List of extracted field mappings
        - error: Error message if processing failed (optional)
    """
    try:
        # Load configuration and schema
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment")
            return {"error": "Configuration error: API key not configured"}
        
        client = genai.Client(api_key=api_key)
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        rules_path = os.path.join(base_dir, "data", "pra_rules_subset.txt")
        schema_path = os.path.join(base_dir, "data", "schema.json")
        
        # Load regulatory rules and schema
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = f.read()
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        
        # Hybrid input detection
        if _is_numeric_input(user_scenario):
            logger.info(f"Numeric input detected: {user_scenario}")
            # Parse numeric value and create R010 mapping
            numeric_value = float(user_scenario.replace(',', ''))
            return _create_numeric_result(numeric_value, schema)
        
        # Narrative input: perform full LLM extraction
        logger.info("Narrative input detected, initiating LLM extraction")
        
        # Construct structured prompt with schema context
        prompt = f"""You are a regulatory reporting specialist for UK Banks. Extract capital and own funds data from the scenario below and map to COREP template C 01.00.

REGULATORY RULES:
{rules}

SCHEMA DEFINITION:
{json.dumps(schema, indent=2)}

USER SCENARIO:
{user_scenario}

INSTRUCTIONS:
1. Identify all relevant capital components mentioned in the scenario
2. Map each component to the correct row_id from the schema
3. Extract numeric values (convert text amounts like "£50m" to 50000000)
4. Provide the specific Rule ID that justifies each mapping
5. Output ONLY valid JSON in the exact format below (no markdown, no explanations)

REQUIRED OUTPUT FORMAT:
{{
  "results": [
    {{
      "row_id": "R010",
      "field_name": "Common Equity Tier 1 Capital",
      "value": 50000000.0,
      "justification": "CA1-0010"
    }}
  ]
}}
"""
        
        # Execute LLM extraction with gemini-2.5-flash
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        
        # Robust JSON sanitization
        raw_text = response.text
        logger.debug(f"Raw LLM response: {raw_text[:200]}...")
        
        cleaned_json = _sanitize_json_response(raw_text)
        
        # Parse and validate JSON structure
        try:
            result = json.loads(cleaned_json)
        except json.JSONDecodeError as json_err:
            logger.error(f"JSON parsing failed: {json_err}")
            logger.debug(f"Cleaned JSON: {cleaned_json}")
            # Attempt fallback: extract JSON from text
            json_match = re.search(r'\{.*\}', cleaned_json, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                raise
        
        # Validate required structure
        if "results" not in result or not isinstance(result["results"], list):
            logger.error("Invalid response structure: missing 'results' array")
            return {"error": "Invalid extraction format: expected results array"}
        
        # Validate required fields in each result
        required_fields = schema.get('validation_rules', {}).get('required_fields', [])
        for idx, item in enumerate(result["results"]):
            missing_fields = [f for f in required_fields if f not in item]
            if missing_fields:
                logger.warning(f"Result {idx} missing fields: {missing_fields}")
        
        logger.info(f"Successfully extracted {len(result['results'])} field mappings")
        return result
        
    except FileNotFoundError as file_err:
        logger.error(f"Configuration file not found: {file_err}")
        return {"error": f"System configuration error: {str(file_err)}"}
    
    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decoding failed: {json_err}")
        return {"error": "Data extraction failed: invalid response format from processing engine"}
    
    except Exception as e:
        logger.error(f"Unexpected error in processing: {str(e)}", exc_info=True)
        return {"error": f"Processing error: {str(e)}"}