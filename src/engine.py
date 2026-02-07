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
        ],
        "validation_errors": [],
        "retrieved_rules": []
    }


def retrieve_relevant_rules(user_scenario: str, all_rules: str) -> List[Dict[str, str]]:
    """
    Retrieve relevant regulatory rules based on user scenario using keyword matching.
    
    This implements a simple but effective retrieval mechanism that:
    1. Extracts key financial terms from the user scenario
    2. Matches them against rule descriptions
    3. Returns the most relevant rules for LLM processing
    
    Args:
        user_scenario: User input text
        all_rules: Complete regulatory rules text
        
    Returns:
        List of relevant rule dictionaries with id, field, and instruction
    """
    # Parse rules into structured format
    rules = []
    current_rule = {}
    
    for line in all_rules.split('\n'):
        line = line.strip()
        if line.startswith('Rule ID:'):
            if current_rule:
                rules.append(current_rule)
            current_rule = {'id': line.replace('Rule ID:', '').strip()}
        elif line.startswith('Field:'):
            current_rule['field'] = line.replace('Field:', '').strip()
        elif line.startswith('Row/Column:'):
            current_rule['row_column'] = line.replace('Row/Column:', '').strip()
        elif line.startswith('Instruction:'):
            current_rule['instruction'] = line.replace('Instruction:', '').strip()
    
    if current_rule:
        rules.append(current_rule)
    
    # Extract keywords from user scenario (case-insensitive)
    scenario_lower = user_scenario.lower()
    
    # Financial keywords to look for
    keywords = [
        'common equity', 'cet1', 'tier 1', 'tier 2', 'capital',
        'retained earnings', 'comprehensive income', 'intangible',
        'deferred tax', 'deduction', 'securitisation', 'pension',
        'additional tier', 'subordinated', 'minority', 'goodwill'
    ]
    
    # Score each rule based on keyword matches
    scored_rules = []
    for rule in rules:
        score = 0
        rule_text = f"{rule.get('field', '')} {rule.get('instruction', '')}".lower()
        
        # Check for keyword matches
        for keyword in keywords:
            if keyword in scenario_lower and keyword in rule_text:
                score += 2
            elif keyword in rule_text:
                score += 1
        
        # Boost score if row/column is mentioned
        if 'row_column' in rule and any(rc in scenario_lower for rc in rule.get('row_column', '').split(',')):
            score += 3
        
        if score > 0:
            scored_rules.append((score, rule))
    
    # Sort by score and return top 10 rules
    scored_rules.sort(reverse=True, key=lambda x: x[0])
    top_rules = [rule for score, rule in scored_rules[:10]]
    
    # If no matches, return first 5 rules as fallback
    if not top_rules:
        top_rules = rules[:5]
    
    logger.info(f"Retrieved {len(top_rules)} relevant rules from {len(rules)} total rules")
    return top_rules


def validate_results(results: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Validate extracted results against schema validation rules.
    
    Checks for:
    - Negative values where not allowed
    - Missing required fields
    - Duplicate row IDs
    - Invalid row IDs not in schema
    - Data type mismatches
    
    Args:
        results: List of extracted field mappings
        schema: COREP schema with validation rules
        
    Returns:
        List of validation error dictionaries with severity and message
    """
    errors = []
    validation_rules = schema.get('validation_rules', {})
    schema_rows = {row['id']: row for row in schema.get('rows', [])}
    
    seen_row_ids = set()
    
    for idx, result in enumerate(results):
        row_id = result.get('row_id', '')
        value = result.get('value', 0)
        
        # Check for required fields
        required_fields = validation_rules.get('required_fields', [])
        for field in required_fields:
            if field not in result or result[field] is None:
                errors.append({
                    'severity': 'error',
                    'row_id': row_id,
                    'message': f"Missing required field: {field}"
                })
        
        # Check for duplicate row IDs
        if row_id in seen_row_ids:
            errors.append({
                'severity': 'error',
                'row_id': row_id,
                'message': f"Duplicate row ID: {row_id}"
            })
        seen_row_ids.add(row_id)
        
        # Check if row ID exists in schema
        if row_id not in schema_rows:
            errors.append({
                'severity': 'warning',
                'row_id': row_id,
                'message': f"Row ID {row_id} not found in schema"
            })
            continue
        
        # Get row-specific validation rules
        row_schema = schema_rows[row_id]
        row_validation = row_schema.get('validation', {})
        
        # Check for negative values
        allow_negative = row_validation.get('allow_negative', validation_rules.get('allow_negative', False))
        if not allow_negative and value < 0:
            errors.append({
                'severity': 'error',
                'row_id': row_id,
                'message': f"Negative value not allowed for {row_schema.get('name', row_id)}: {value}"
            })
        
        # Check minimum value constraints
        if 'min_value' in row_validation and value < row_validation['min_value']:
            errors.append({
                'severity': 'error',
                'row_id': row_id,
                'message': f"Value {value} below minimum {row_validation['min_value']}"
            })
        
        # Check data type
        expected_type = row_schema.get('data_type', 'numeric')
        if expected_type == 'numeric' and not isinstance(value, (int, float)):
            errors.append({
                'severity': 'error',
                'row_id': row_id,
                'message': f"Expected numeric value, got {type(value).__name__}"
            })
    
    # Check for minimum number of fields
    min_fields = validation_rules.get('min_fields', 0)
    if len(results) < min_fields:
        errors.append({
            'severity': 'warning',
            'row_id': 'GENERAL',
            'message': f"Only {len(results)} fields extracted, minimum {min_fields} expected"
        })
    
    logger.info(f"Validation complete: {len(errors)} issues found")
    return errors


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
            result = _create_numeric_result(numeric_value, schema)
            # Add validation
            validation_errors = validate_results(result['results'], schema)
            result['validation_errors'] = validation_errors
            return result
        
        # Narrative input: perform full LLM extraction
        logger.info("Narrative input detected, initiating LLM extraction")
        
        # RETRIEVAL: Get relevant rules instead of using all rules
        relevant_rules = retrieve_relevant_rules(user_scenario, rules)
        
        # Format retrieved rules for prompt
        rules_text = "\n\n".join([
            f"Rule ID: {r.get('id', 'N/A')}\n"
            f"Field: {r.get('field', 'N/A')}\n"
            f"Row/Column: {r.get('row_column', 'N/A')}\n"
            f"Instruction: {r.get('instruction', 'N/A')}"
            for r in relevant_rules
        ])
        
        # Construct structured prompt with RETRIEVED rules
        prompt = f"""You are a regulatory reporting specialist for UK Banks. Extract capital and own funds data from the scenario below and map to COREP template C 01.00.

RELEVANT REGULATORY RULES (Retrieved):
{rules_text}

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
        
        # Execute LLM extraction with gemini-2.0-flash-exp
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
        
        # Perform validation on extracted results
        validation_errors = validate_results(result["results"], schema)
        result['validation_errors'] = validation_errors
        
        # Add retrieved rules info for audit trail
        result['retrieved_rules'] = [
            {'id': r.get('id'), 'field': r.get('field')} 
            for r in relevant_rules
        ]
        
        logger.info(f"Successfully extracted {len(result['results'])} field mappings with {len(validation_errors)} validation issues")
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