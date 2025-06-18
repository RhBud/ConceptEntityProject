import pandas as pd
import os 

from motor.motor_asyncio import AsyncIOMotorClient
# imports for langchain and Chroma and plotly

import numpy as np
import json
import re


#  environmental variables passed into service
mongouser = os.getenv('MONGO_INITDB_ROOT_USERNAME')
mongopass = os.getenv('MONGO_INITDB_ROOT_PASSWORD')

# Add these plus the key to the environmental variables
client = AsyncIOMotorClient(f"mongodb://{mongouser}:{mongopass}@mongodb:27017")

# key read in from env file at home on the local machine
from openai import AsyncOpenAI
openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

db = client["umls"]    # Replace with your database name
collection = db["mrconso"] # Replace with your collection name



# Let's start by making a useful function
# we will see if we can give it to the model

async def get_possible_ingredient_code_lookup(concept_name):
        
    pipeline = [
        {
            "$match": {
                "STR_LOWER": concept_name,
                "SAB": "RXNORM",
                "TTY":'IN'
            }
        },
        {
            "$project": {
                "_id": 0,
                "STR": 1,
                "SAB": 1,
                "STR_LOWER": 1,
                "CODE": 1
            }
        }
    ]
        # Execute the aggregation pipeline and convert to DataFrame immediately
    aggregation_result = await collection.aggregate(pipeline).to_list(length=None)
    result_codes = [ c['CODE'] + ' coded for ingredient ' + c['STR'] for c in aggregation_result ]
    return result_codes



# Confirmed from Jason, need to add a little bit of instructions to this (bare minimal) to also give the entity types

def create_improved_entity_prompt(concept_name):


    # 2. Create the Python dictionary structure for the entities


    # 3. Convert the Python dictionary to a JSON formatted string
    # Using indent=2 for readability if you were to print it, though for the LLM it's not strictly necessary.

    prompt = """
    You are an expert medical coding assistant.

    Your job is to assign medical codes from specific vocabularies to clinical concepts provided to you. Each concept should be evaluated *individually* and carefully. You must **only return codes when you are confident the concept maps clearly and specifically to a real entry in the medical coding system that capture the clinical meaning of the concept without ambiguity**.
    
    ## Your task:
    
    For an input concept, return:
    - The one or more correct **entity types**
    - A list of matching medical codes
    - A **confidence score (0-100)** for each code
    - The code **system**, human-readable **description**, and the original concept name
    
    Only include codes when your confidence is high (≥ 80). **False positives are worse than false negatives** — it's better to leave something uncoded than to assign a wrong or approximate code.
    
    If the concept does not clearly correspond to a code in the specified vocabulary, **return no codes at all for that concept. Do not guess.**
    
    ---
    
    ## Allowable vocabularies:
    - **ICD-10**: for diagnoses
    - **ICD-10-CM categories**: for diagnosis groupings
    - **CPT**: for procedures
    - **LOINC**: for labs/measurements
    - **RxNorm**: for medications 
    - **ATC**: for drug classes
    
    ---
    
    ## Allowable entity types:
    - `'diagnosis'`
    - `'procedure'`
    - `'measurements/labs'`
    - `'medication'`
    - `'drug_class'`
    
    If multiple apply, separate them with commas.
    
    ---
    
    ## Coding Strategy:
    
    1. Identify the **correct vocabulary**
    2. Confirm a **clear and valid match** — if not, skip coding. A concept that COULD be represented by a code but also may not should not be included
    3. For medications, unless a brand or dosage is specified, provide the RxNorm for the active ingredient.
    4. Use the concept as a guide to find the proper description based on that concept from the determined vocabulary in 1)
    5. Provide structured output in valid JSON
    
    ---
    
    ## Examples of concepts that should NOT be coded:
    
    - `"delayed sleep-wake phase disorder"` → Not clearly represented in ICD-10, do not code
    - `"high output cardiac failure"` → If no direct ICD-10 match, skip
    - `"combination regimens not listed as RxNorm drugs"` → do not guess component drugs
    
    ---
    
    ## Output format:
    Return only a well-formed JSON response, no prose or explanation.
    
    ```json
    {
      "entities": {
        "[ENTITY_NAME]": {
          "entity_name": "[ENTITY_NAME]",
          "types": "[ENTITY_TYPE]",
          "codes": [
            {
              "code": "[CODE_VALUE]",
              "system": "[CODE_SYSTEM]",
              "description": "[HUMAN_READABLE_DESCRIPTION]",
              "confidence": [0-100]
            }
          ]
        }
      }
    }


    The input concept name is: """
    prompt = prompt + concept_name
    return prompt

# instead of evaluating itself while searching for the answer lets add another agent who is the REVIEWER who hopefully can see with more clarity 
# if I have time demonstrate how I would use a bidirectional autoencoder to help here especially for RXNORM codes which are syntactically kind of meaningless as they are just integers

def create_reviewer_entity_result_prompt(concept_name, initial_model_json):
    '''The reviewer will never Add in if it is missing, its job is to reduce false positives '''
    prompt = """
    You are an expert medical coding Reviewer.
    You work at the end of a chain of agents and your job is to provide the highest quality to our staff and clients who rely on your results to help build powerful software that drives key medical research.

    The input you will receive is the output of the previous agent
     {
      "entities": {
        "[ENTITY_NAME]": {
          "entity_name": "[ENTITY_NAME]",
          "types": "[ENTITY_TYPE]",
          "codes": [
            {
              "code": "[CODE_VALUE]",
              "system": "[CODE_SYSTEM]",
              "description": "[HUMAN_READABLE_DESCRIPTION]",
              "confidence": [0-100]
            }
          ]
        }
      }
    }
    Where [ENTITY_NAME] is the original input concept and the other elements are the results given by the previous agent. Below I outline the previous agents task for clarity for you, and then your key tasks

    
    ## Previous Agent task:
    The previous agents task was to 
    1) First determine what entity type the concept belogs, and procedure to step 2 given one specific vocabulary that can be used for that entity type
    The Allowable entity types with corresponding allowable vocabulary:
    - `'diagnosis'` -> for **ICD-10** and **ICD-10CM** vocabularies only
    - `'procedure'` -> for the **CPT**  vocabulary only
    - `'measurements/labs'` -> for the **LOINC**  vocabulary only
    - `'medication'` -> for the **RxNorm**  vocabulary only
    - `'drug_class'` -> for the **ATC** vocabulary only

    2) Confirm a **clear and valid match** — if not, skip coding. A concept that COULD be represented by a code but also may not should not be included
    ** Your Task

    3)  Use the concept as a guide to find the proper description based on that concept from **only** the determined vocabulary in 1) and:
    For an input concept, return:
    - The one or more correct **entity types**
    - A list of matching medical codes
    - A **confidence score (0-100)** for each code
    - The code **system**, human-readable **description**, and the original concept name
    
    The previous agent should only include codes when their confidence is high. **False positives are worse than false negatives** — it's better to leave something uncoded than to assign a wrong or approximate code.
    
    If the concept does not clearly correspond to a code in the specified vocabulary, **they should return no codes at all for that concept. Do not guess.**

    ---

    ## YOUR TASK NOW
    Perform a review of the previous agent's work and help REDUCE false positives. You will make modifications of the output of the previous agent if necessary, and provide an output in the same form.  If the previous agent made a mistake or deviated from its instructions in any way, return no concept 

    Follow these steps and either approave (and return the input as your result) or modify the output. Here are your two main tasks

    1) Check for drastic error: If the input for the "[ENTITY_TYPE] and [CODE_SYSTEM] valuse are not from the previous agent's approved entity type and vocabulary lists, return no concept as the correct output

    2) Check for clinical meaning error of codes and modify if necessary: If your first check has passed 
        a) Keeping in mind  **clear and valid clinical match** — if the vocabulary in question is likely not able to succesfully capture the specificity of the original medical concept, return no output
        b) If the code provided is not quite correct, but with a high degree of certainty a better alternative exists, you can modify and correct the output for "[CODE_VALUE], and official [HUMAN_READABLE_DESCRIPTION] that would go with that code. With the goal in mind of obtaining an overall correct set of codes

    **Known limitatoins of previous agent**
    - Sometimes uses an invalid vocabulary which should be invalidated and no codes returned
    - Often for medications provides a totally incorrect RXNorm value. Efforts should be made to make sure the correct Rxnorm of the active ingredient is provdided
    ---
    
    ## Your Final Output format:
    Return only a well-formed JSON response, no prose or explanation.
    
    ```json
    {
      "entities": {
        "[ENTITY_NAME]": {
          "entity_name": "[ENTITY_NAME]",
          "types": "[ENTITY_TYPE]",
          "codes": [
            {
              "code": "[CODE_VALUE]",
              "system": "[CODE_SYSTEM]",
              "description": "[HUMAN_READABLE_DESCRIPTION]",
              "confidence": [0-100]
            }
          ]
        }
      }
    }


    The initial concept name is: """
    prompt = prompt + concept_name

    prompt += """
    And the previous agents output is:
    
    """

    prompt += initial_model_json
    return prompt

    
def flatten_entity_to_df(response_json):
    '''Convert entity-type-only LLM output JSON to a DataFrame including regime flag.
    '''
    
        
    # Prepare a list to hold all the records
    records = []
    
    # Iterate through each entity in the 'entities' dictionary
    for entity_key, entity_value in response_json['entities'].items():
        # Extract common entity details
        entity_name = entity_value['entity_name']
        entity_types = entity_value['types']
    
        # Iterate through each code within the current entity
        for code_entry in entity_value['codes']:
            # Create a dictionary for the current record
            record = {
                'entity_name': entity_name,
                'types': entity_types,
                'code': code_entry.get('code'),  # Use .get() for safer access
                'system': code_entry.get('system'),
                'description': code_entry.get('description'),
                'confidence': code_entry.get('confidence')
            }
            records.append(record)
    
    # Create the DataFrame from the list of records
    df_long_form_entities = pd.DataFrame(records)
    return df_long_form_entities



async def get_completion(prompt, model="gpt-4-turbo"):
    try:
        print(f"Making OpenAI API call with model: {model}")
        print(f"API Key present: {bool(os.getenv('OPENAI_API_KEY'))}")
        
        messages = [{"role": "user", "content": prompt}]
        response = await openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )
        content = response.choices[0].message.content
        print(f"OpenAI response received: {content[:100]}...")  # Print first 100 chars
        return content
    except Exception as e:
        print(f"Error in get_completion: {str(e)}")
        print(f"Error type: {type(e)}")
        # Return a default empty response structure
        return '{"entities": {}}'

def strip_markdown_fences(text):
    # Remove triple backticks and optional "json" label around the JSON block
    return re.sub(r"^```json\s*|```$", "", text.strip(), flags=re.MULTILINE)



async def get_single_response(concept_text):
    prompt = create_improved_entity_prompt(concept_text)
    response_json = await get_completion(prompt, model='gpt-4.1')  # get raw JSON/dict

    ent_clean = json.loads(strip_markdown_fences(response_json))
    print(f"ent_clean: {ent_clean}")
    print(f"entities: {ent_clean.get('entities')}")
    print(f"positive_prediction (len): {len(ent_clean.get('entities', {}))}")
    # if non zero, pass to our reviewer
    positive_prediction = len(ent_clean['entities'].items())

    if positive_prediction == 0:
        # Return an empty, properly structured response
        return {"entities": {}}
    else:
        # send to revieier
        
         # Build a lookup string only if there's a medication
        lookup_str = ""
        all_types = [ent_data["types"] 
                     for ent_data in ent_clean["entities"].values()]
        codes_found = []
        if "medication" in all_types:   # match exactly your earlier prompt's "medication"
            all_codes = [
                c["description"]
                for ent_data in ent_clean["entities"].values()
                for c in ent_data["codes"]
            ]
            if len(all_codes) > 0:
                # consider adding this to the prompt to expect if found
                lookup_str = "Database tool results (if any) as supporting evidence to help your response:\n"
                for c in all_codes:
                    codes_found = []
                    codes_found = await get_possible_ingredient_code_lookup(c.lower())
                    # codes_found is always a list; join them with newline + a leading space
                    lookup_str += "\n".join(f"  {code}" for code in codes_found) + "\n"
            

        # Now pass the original ent_clean *and* the lookup_str into your reviewer prompt
        # prompt in this case will be lookup_str + JSON
        if len(codes_found)>0:
            # insert a blank line between lookup_str and the JSON dump
            prompt_for_reviewer = lookup_str + "\n" + json.dumps(ent_clean)
        else:
            prompt_for_reviewer = json.dumps(ent_clean)
            
        review_prompt = create_reviewer_entity_result_prompt(concept_text, prompt_for_reviewer)
        review_response_json = await get_completion(review_prompt, model='gpt-4.1')  # get raw JSON/dict
        print(f"review_response_json: {review_response_json}")
        review_ent_clean = json.loads(strip_markdown_fences(review_response_json))
        print(f"review_ent_clean: {review_ent_clean}")
        return review_ent_clean