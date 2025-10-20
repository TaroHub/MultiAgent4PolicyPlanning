from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands_tools import swarm
import json
import re
import asyncio

app = BedrockAgentCoreApp()

def extract_json(message):
    """Extract the JSON part from the message"""
    if isinstance(message, dict):
        if 'content' in message and isinstance(message['content'], list):
            text = message['content'][0].get('text', '')
        else:
            text = str(message)
    else:
        text = str(message)
    
    json_match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
    
    try:
        return json.loads(text)
    except:
        return None

async def invoke_async_streaming(payload):
    """Multi-agent policy system (extended version, streaming supported)"""
    try:
        user_message = payload.get("prompt", "")
        
        if not user_message:
            yield {"type": "error", "data": "A prompt is required."}
            return
        
        # Step 0: Investigation of similar policies
        yield {"type": "status", "data": "[Step 0] Investigating similar policies from other municipalities..."}
        
        research_agent = Agent(
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            callback_handler=None,
            system_prompt="""You are a research expert specializing in municipal policies.  
Please investigate existing cases of policies related to citizen opinions and present relevant examples as references.

IMPORTANT: Respond entirely in English.

Research Priority:
1. Give top priority to examples from Tokyo.
2. If there are no examples from Tokyo, refer to other ordinance-designated cities or municipalities within Tokyo.
3. If none are found, refer to cases from municipalities nationwide in Japan.

Output Format:
```json
{
  "similar_policies": [
    {"municipality": "Municipality name", "policy_name": "Policy name", "summary": "Summary", "results": "Results"}
  ],
  "has_references": true/false,
  "search_scope": "Tokyo / Other municipalities / Nationwide Japan"
}
```"""
        )
        
        research_response = ""
        async for event in research_agent.stream_async(f"Citizen opinions: {user_message}\n\nFirst, please investigate similar policy cases in Tokyo. If there are no such cases in Tokyo, then investigate about three cases from other municipalities or from across Japan."):
            if "data" in event:
                chunk = event["data"]
                yield {"type": "stream", "step": "research", "data": chunk}
                research_response += chunk
        
        research_result = extract_json(research_response) or {"similar_policies": [], "has_references": False}
        yield {"type": "research", "data": research_result}
        yield {"type": "stream", "step": "research_complete", "data": f"\n\n[Investigation complete] Similar policies: {len(research_result.get('similar_policies', []))} cases"}
        
        # Step 1a: Demographic survey
        yield {"type": "status", "data": "[Step 1a] Investigating the demographic trends of the target area..."}
        
        demographics_agent = Agent(
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            callback_handler=None,
            system_prompt="""You are a demographic statistics expert.  
Identify the target area based on citizen opinions and investigate the demographic trends of that area.

IMPORTANT: Respond entirely in English.

Research Priority:
1. Give top priority to demographic trends in Tokyo.
2. If a specific area is clearly mentioned in citizen opinions, target that area.
3. If Tokyo data is unavailable, use statistics from other ordinance-designated cities or nationwide data.

Important: If data does not exist, use Fermi estimation.
- Infer from data of similar cities
- Adjust nationwide statistics considering local characteristics
- Estimate based on population size, industrial structure, and geographical features
- Clearly specify the estimation method in the data_source field

Japanese proficiency assessment criteria (for foreign residents):
- fluent: Equivalent to JLPT N1-N2. Can read administrative documents, handle complex consultations at counters, and work without problems
- conversational: Equivalent to JLPT N3-N4. Can handle daily conversations, but needs assistance with technical terms and paperwork
- basic: Equivalent to JLPT N5 or below. Limited to greetings and simple shopping; needs support in daily life
- needs_support: Little to no Japanese ability; constant need for interpretation/translation

Output format:
```json
{
  "target_area": "Target area name",
  "age_distribution": {
    "20代": 10,
    "30代": 15,
    "40代": 15,
    "50代": 20,
    "60代以上": 40
  },
  "gender_ratio": {"male": 48, "female": 52},
  "family_types": [
    {"type": "Single-person households", "percentage": 35},
    {"type": "Couples only", "percentage": 20},
    {"type": "Households with children", "percentage": 25},
    {"type": "Three-generation households", "percentage": 10},
    {"type": "Elderly-only households", "percentage": 10}
  ],
  "language_distribution": [
    {"language": "Japanese", "percentage": 60, "notes": "Remarks"},
    {"language": "English", "percentage": 15, "notes": "Mainly business sector"}
  ],
  "japanese_proficiency_levels": {
    "fluent": 30,
    "conversational": 40,
    "basic": 20,
    "needs_support": 10
  },
  "cultural_considerations": [
    {"group": "Region / Cultural sphere", "key_points": ["Consideration for religious events", "Cultural friction in schools"]},
    {"group": "Technical intern trainees", "key_points": ["Support for administrative procedures", "Management of working hours"]}
  ],
  "priority_services": [
    "Multilingual administrative procedures (Japanese, English, Chinese, Vietnamese)",
    "Assignment of multicultural support teachers in schools"
  ],
    "data_source": "Data source (describe as a string. Example: Tokyo Statistical Report 2023, Statistics Bureau of Japan 2022 Census, Fermi estimation, etc.)",
    "data_scope": "Tokyo / Other municipalities / Nationwide Japan"
}
```

Note: Please make sure to describe data_source as a string. Do not use objects or arrays."""
        )
        
        demographics_response = ""
        async for event in demographics_agent.stream_async(f"Citizen opinion: {user_message}\n\nFirst, investigate the demographic trends of Tokyo. If data for Tokyo is unavailable, use statistics from other municipalities or from all of Japan. If no data exists, calculate a reasonable estimate using Fermi estimation. Clearly specify the estimation method in the data_source."):
            if "data" in event:
                chunk = event["data"]
                yield {"type": "stream", "step": "demographics", "data": chunk}
                demographics_response += chunk
        
        demographics_data = extract_json(demographics_response)
        if not demographics_data:
            yield {"type": "error", "data": "Failed to obtain demographic data."}
            return
        yield {"type": "demographics", "data": demographics_data}
        language_distribution = demographics_data.get('language_distribution', [])
        language_summary = ", ".join(
            f"{entry.get('language', 'Unknown')}: {entry.get('percentage', '?')}%"
            for entry in language_distribution[:3]
        ) or "Unknown"
        japanese_proficiency = demographics_data.get('japanese_proficiency_levels', {})
        proficiency_summary = ", ".join(
            f"{level}: {percentage}%"
            for level, percentage in japanese_proficiency.items()
        ) or "Unknown"
        yield {"type": "stream", "step": "demographics_complete", "data": (
            f"\n\n[Investigation complete] Target area: {demographics_data.get('target_area', 'Unknown')}"
            f"\nAge distribution: {json.dumps(demographics_data.get('age_distribution', {}), ensure_ascii=False)}"
            f"\nGender ratio: {json.dumps(demographics_data.get('gender_ratio', {}), ensure_ascii=False)}"
            f"\nMain languages: {language_summary}"
            f"\nJapanese proficiency: {proficiency_summary}"
        )}
        
        # Step 1b: SV agent generates agent definitions (based on the investigated demographic trends)
        yield {"type": "status", "data": "[Step 1b] Generating agent definitions..."}
        
        demographics_text = f"""
Target area: {demographics_data.get('target_area', '不明')}
Age distribution: {json.dumps(demographics_data.get('age_distribution', {}), ensure_ascii=False)}
Gender ratio: {json.dumps(demographics_data.get('gender_ratio', {}), ensure_ascii=False)}
Family structure: {json.dumps(demographics_data.get('family_types', []), ensure_ascii=False)}
Language distribution: {json.dumps(demographics_data.get('language_distribution', []), ensure_ascii=False)}
Japanese proficiency: {json.dumps(demographics_data.get('japanese_proficiency_levels', {}), ensure_ascii=False)}
Cultural considerations: {json.dumps(demographics_data.get('cultural_considerations', []), ensure_ascii=False)}
Priority services: {json.dumps(demographics_data.get('priority_services', []), ensure_ascii=False)}
"""
        
        sv_agent = Agent(
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            callback_handler=None,
            system_prompt="""Analyze citizen opinions and design the agents necessary for policy consideration.

IMPORTANT: Respond entirely in English.

Your role:
1. Analyze the content of citizen opinions.
2. Decide on the number and areas of expertise for the required policy-making agents (guideline: 2–4 agents).
   - Make sure to include at least one agent with the perspective of Tokyo administration.
   - However, do not include “Tokyo’s” in the name field; use only general job titles or areas of expertise.
3. Set at least 10 citizen evaluation agents (based on the provided demographic data).

Naming rules for policy-making agents:
- Good examples: "Policy Planning Officer", "Welfare Policy Specialist", "Urban Planning Consultant", "DX Promotion Specialist"
- Bad examples: "Tokyo Welfare Bureau Officer", "Tokyo Urban Development Bureau Staff" (avoid specific department names)

Citizen agent design rules (as a virtual citizen agent designer):
Purpose: Based on the policy content, design 10 diverse virtual citizens who will provide varied opinions in policy reporting.

Design rules:
- Refer to demographic trends and compose agents balanced across all ages and groups
- Include 30–50% of the main target group for the policy
- Include groups indirectly involved or not targeted by the policy
- Appropriately include citizens with diverse backgrounds such as foreigners, the elderly, people with disabilities, and households with children
- Avoid stereotypes and design realistic backgrounds and opinions
- Distribute attitudes towards the policy (support/neutral/concern, etc.) evenly

Output format:
```json
{
  "policy_agents": [
    {"name": "Policy Planning Officer", "expertise": "Policy Planning & Administrative Operations", "system_prompt": "Detailed prompt"}
  ],
  "citizen_agents": [
    {
      "name": "Hanako Tanaka",
      "age": 30,
      "gender": "Female",
      "occupation": "Nursery Teacher",
      "residence": "Shibuya Ward, Tokyo",
      "family": "Dual-income, 2 children",
      "values": "Prioritizes connection with the community",
      "stance": "Strongly supportive",
      "profile": "Detailed profile",
      "is_directly_affected": true,
      "system_prompt": "Evaluation prompt"
    }
  ],
  "reviewer_agent": {
    "name": "Legal & Feasibility Reviewer",
    "expertise": "Law & Feasibility",
    "system_prompt": "Review prompt"
  }
}
```

Note: Write both JSON field names and values in English. All text content must be in English.

Notes:
- At least one policy-making agent must be an expert who considers from the perspective of Tokyo administration.
- However, do not include “Tokyo’s” in the name field; use only general job titles.
- In system_prompt, clearly state the specific perspective, such as “from the standpoint of Tokyo.”
- is_directly_affected indicates whether the agent receives direct benefits from the policy (true = receives benefits, false = does not / unrelated group).
- For citizen agents, write all JSON field names in English."""
        )
        
        sv_response = ""
        async for event in sv_agent.stream_async(f"Citizen opinions: {user_message}\n\nDemographic data:\n{demographics_text}"):
            if "data" in event:
                chunk = event["data"]
                yield {"type": "stream", "step": "sv_agent", "data": chunk}
                sv_response += chunk
        
        agent_defs = extract_json(sv_response)
        
        if not agent_defs or len(agent_defs.get("citizen_agents", [])) < 10:
            yield {"type": "error", "data": "Failed to generate agent definitions (fewer than 10 citizen agents)"}
            return
        
        # Verification and warning for the is_directly_affected field
        unaffected_count = sum(1 for a in agent_defs.get("citizen_agents", []) if a.get("is_directly_affected") == False)
        yield {"type": "status", "data": f"[Step 1b] Generation complete: {len(agent_defs.get('citizen_agents', []))} citizen agents (of which {unaffected_count} are not directly affected by the policy)"}
        
        yield {"type": "agent_defs", "data": agent_defs}
        
        # Step2: Policy planning by swarm (with reference to similar policies)
        yield {"type": "status", "data": "[Step 2] Policy planning agents collaborating..."}
        
        reference_text = ""
        if research_result.get("has_references"):
            reference_text = f"\n\nReference cases:\n{json.dumps(research_result['similar_policies'], ensure_ascii=False, indent=2)}\nPlease refer to the above cases."
        
        swarm_agent = Agent(
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            tools=[swarm],
            callback_handler=None
        )
        
        swarm_prompt = f"""Based on the following agent definitions, create a swarm and generate a policy proposal in JSON format in response to the citizen opinion ""{user_message}"".

Agent definitions:
{json.dumps(agent_defs['policy_agents'], ensure_ascii=False, indent=2)}
{reference_text}

Output format:
```json
{{
  "policy_title": "Policy title (concise and clear, within 50 characters)",
  "summary": "Policy summary (briefly explain the purpose and target of this policy, 300-500 characters)",
  "referenced_policies": ["Names of referenced municipal policies (specify municipality and policy name)"],
  "problem_analysis": "Problem analysis (explain the current issues, why this policy is needed, include data and specific examples, 500-700 characters)",
  "detailed_policy": "Policy details (describe the specific contents, support provided, eligibility criteria, implementation methods, rough budget scale, required system, considerations such as laws and relationships with existing policies in detail, 800-1000 characters)",
  "implementation_plan": "Implementation plan (describe how and over what time period the policy will be implemented, the duration and content of each phase, and the step-by-step rollout method, 500-700 characters)",
  "expected_effects": "Expected effects (quantitative effects (e.g., number of users per year, % improvement) and qualitative effects (e.g., increased citizen satisfaction, community revitalization) in detail, 400-600 characters)",
  "is_temporary": true/false (true for temporary policies, false for permanent policies)
}}
```

**Required Items**:
- Be sure to include all of the above items.
- For each item, provide specific and detailed descriptions in accordance with the explanations.
- Ensure sufficient information by using the suggested character counts as a guideline.
- IMPORTANT: Write all content in English."""
        
        policy_response = ""
        async for event in swarm_agent.stream_async(swarm_prompt):
            if "data" in event:
                chunk = event["data"]
                yield {"type": "stream", "step": "swarm", "data": chunk}
                policy_response += chunk
        
        policy_json = extract_json(policy_response)
        if not policy_json:
            policy_json = {"raw_text": policy_response}
        
        yield {"type": "policy", "data": policy_json}
        
        # Step 3: Legal and feasibility review by reviewer (up to 3 retries)
        yield {"type": "status", "data": "[Step 3] Reviewing legal compliance and feasibility..."}
        
        reviewer_agent = Agent(
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            system_prompt=agent_defs.get("reviewer_agent", {}).get("system_prompt", "Please review from the perspective of law and feasibility."),
            callback_handler=None
        )
        
        review_result = None
        for attempt in range(1, 4):
            yield {"type": "status", "data": f"[Step 3] Review attempt {attempt}/3"}
            
            review_prompt = f"""Please review the following policy proposal from the perspective of law and feasibility.

Policy proposal:
{json.dumps(policy_json, ensure_ascii=False, indent=2)}

Output format:
```json
{{
  "legal_compliance": {{"score": 85, "issues": ["Problems"], "recommendations": ["Recommendations"]}},
  "feasibility": {{"score": 80, "issues": ["Problems"], "recommendations": ["Recommendations"]}},
  "total_score": 82.5,
  "overall_assessment": "Overall evaluation",
  "approved": true/false,
  "improvement_suggestions": "Improvement suggestions (if not approved)"
}}
```

Overall Score = Legal Compliance × 0.5 + Feasibility × 0.5  
Approval Criteria: Approved if score is 80 or higher

Important: For overall_assessment and improvement_suggestions, use headings in 【】 and bullet points (・) for readability.
"""
            
            review_response = ""
            async for event in reviewer_agent.stream_async(review_prompt):
                if "data" in event:
                    chunk = event["data"]
                    yield {"type": "stream", "step": f"reviewer_attempt_{attempt}", "data": chunk}
                    review_response += chunk
            
            review_result = extract_json(review_response) or {"approved": False, "total_score": 0}
            
            # Calculate the overall score (Legal Compliance 50% + Feasibility 50%)
            if "total_score" not in review_result:
                legal_score = review_result.get("legal_compliance", {}).get("score", 0)
                feasibility_score = review_result.get("feasibility", {}).get("score", 0)
                review_result["total_score"] = legal_score * 0.5 + feasibility_score * 0.5
            
            # Approved if score is 80 or higher
            review_result["approved"] = review_result["total_score"] >= 80
            yield {"type": "review", "data": {**review_result, "attempt": attempt}}
            
            if review_result.get("approved", False):
                yield {"type": "status", "data": f"[Step 3] Review approved (attempt {attempt})"}
                break
            
            if attempt < 3:
                yield {"type": "status", "data": f"[Step 3] Not approved, revising policy proposal..."}
                
                # Revise the policy proposal
                improvement_prompt = f"""The following policy proposal was not approved in the review.

Original policy proposal:
{json.dumps(policy_json, ensure_ascii=False, indent=2)}

Review results:
{json.dumps(review_result, ensure_ascii=False, indent=2)}

Please revise the policy proposal based on the improvement suggestions.  
The output format should be the same JSON format as the original policy proposal."""
                
                policy_response = ""
                async for event in swarm_agent.stream_async(improvement_prompt):
                    if "data" in event:
                        chunk = event["data"]
                        yield {"type": "stream", "step": f"improvement_{attempt}", "data": chunk}
                        policy_response += chunk
                
                improved_policy = extract_json(policy_response)
                if improved_policy:
                    policy_json = improved_policy
                    yield {"type": "policy", "data": {**policy_json, "improved": True, "attempt": attempt}}
            else:
                yield {"type": "status", "data": "[Step 3] Proposal not approved after 3 attempts, continuing with current version..."}
        
        yield {"type": "review_final", "data": review_result}
        
        # Step 4: Citizen evaluation (detailed evaluation)
        yield {"type": "status", "data": "[Step 4] Citizen agents are evaluating..."}
        
        policy_summary = f"""
PolicyTitle: {policy_json.get('policy_title', 'N/A')}
Summary: {policy_json.get('summary', 'N/A')}
ProblemAnalysis: {policy_json.get('problem_analysis', 'N/A')}
DetailedPolicy: {policy_json.get('detailed_policy', 'N/A')}
ImplementationPlan: {policy_json.get('implementation_plan', 'N/A')}
ExpectedEffects: {policy_json.get('expected_effects', 'N/A')}
ReferencedPolicies: {', '.join(policy_json.get('referenced_policies', []))}
"""
        
        citizen_evaluations = []
        
        for i, agent_def in enumerate(agent_defs["citizen_agents"]):
            yield {"type": "status", "data": f"[Step 4] Citizen {i+1}/{len(agent_defs['citizen_agents'])}: {agent_def['name']}"}
            
            citizen_agent = Agent(
                model="us.anthropic.claude-sonnet-4-20250514-v1:0",
                system_prompt=agent_def["system_prompt"],
                callback_handler=None
            )
            
            eval_prompt = f"""{policy_summary}

Your position: {agent_def['profile']}
Age: {agent_def['age']}, Gender: {agent_def.get('gender', '')}, Family: {agent_def.get('family', '')}

Please evaluate the above policy proposal from the following five perspectives, using a scale of 0 to 100 points for each.
For each item, provide both a score and comments (specific reasons and explanation of impact).

Output format:
```json
{{
  "evaluator_name": "{agent_def['name']}",
  "age": {agent_def['age']},
  "gender": "{agent_def.get('gender', '')}",
  "occupation": "{agent_def.get('occupation', '')}",
  "residence": "{agent_def.get('residence', '')}",
  "family": "{agent_def.get('family', '')}",
  "values": "{agent_def.get('values', '')}",
  "stance": "{agent_def.get('stance', '')}",
  "personal_impact": {{"score": 75, "comment": "How this policy would affect your daily life (specifically, around 150 characters)"}},
  "family_impact": {{"score": 80, "comment": "How this policy would affect your family (specifically, around 150 characters)"}},
  "community_impact": {{"score": 70, "comment": "How this policy would affect your community (specifically, around 150 characters)"}},
  "fairness": {{"score": 65, "comment": "Evaluation of the fairness of this policy (specifically, around 150 characters)"}},
  "sustainability": {{"score": 60, "comment": "Evaluation of the sustainability of this policy (specifically, around 150 characters)"}},
  "overall_rating": 72.5,
  "expectations": "Expectations (specifically, around 100 characters)",
  "concerns": "Concerns (specifically, around 100 characters)",
  "recommendations": "Suggestions (specifically, around 100 characters)"
}}
```

Important: Be sure to output all of the above items.
IMPORTANT: Write all content in English.

Overall Evaluation = Personal Impact × 0.5 + Family Impact × 0.2 + Community Impact × 0.1 + Fairness × 0.1 + Sustainability × 0.1
"""
            
            try:
                eval_response = ""
                async for event in citizen_agent.stream_async(eval_prompt):
                    if "data" in event:
                        chunk = event["data"]
                        yield {"type": "stream", "step": f"citizen_{i}", "data": chunk}
                        eval_response += chunk
                
                evaluation = extract_json(eval_response)
                if evaluation:
                    evaluation["is_directly_affected"] = agent_def.get("is_directly_affected", True)
                    citizen_evaluations.append(evaluation)
                    yield {"type": "evaluation", "data": evaluation}
            except Exception as e:
                citizen_evaluations.append({"evaluator_name": agent_def['name'], "error": str(e), "is_directly_affected": agent_def.get("is_directly_affected", True)})
        
        # Step 5: 10-year evaluation (if not a temporary policy)
        future_evaluations = []
        if not policy_json.get("is_temporary", False):
            yield {"type": "status", "data": "[Step 5] Simulating 10-year future evaluation..."}
            
            total_citizens = len(agent_defs["citizen_agents"])
            for i, agent_def in enumerate(agent_defs["citizen_agents"]):
                yield {"type": "status", "data": f"[Step 5] 10-year evaluation {i+1}/{total_citizens}: {agent_def['name']}"}
                
                citizen_agent = Agent(
                    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
                    system_prompt=agent_def["system_prompt"],
                    callback_handler=None
                )
                
                # Estimate the situation 10 years from now based on the current family structure
                current_family = agent_def.get('family', '')
                future_family_note = ""
                if current_family:
                    future_family_note = f"\n\nCurrent family structure: {current_family}\nPlease estimate the family structure 10 years from now (e.g., children become adults, move out, get married, etc.). Assume natural changes based on current age and circumstances."
                
                future_prompt = f"""{policy_summary}

You are now {agent_def['age']+10} years old, 10 years have passed since the implementation of this policy. {future_family_note}

Please describe the changes over the past 10 years and your current evaluation.

Output format:
```json
{{
  "evaluator_name": "{agent_def['name']} (10 years later)",
  "age_now": {agent_def['age']+10},
  "ten_year_rating": 75,
  "changes_observed": "Changes observed over 10 years (including changes in family structure",
  "long_term_impact": "Assessment of long-term impact",
  "unexpected_outcomes": "Unexpected outcomes",
  "current_opinion": "Current opinion"
}}
```

Important:  
- ten_year_rating should be evaluated on a 100-point scale.  
- In changes_observed, be sure to include natural changes over 10 years in the family, such as children growing up, becoming independent, etc.
- IMPORTANT: Write all content in English.
"""
                
                try:
                    future_response = ""
                    async for event in citizen_agent.stream_async(future_prompt):
                        if "data" in event:
                            chunk = event["data"]
                            yield {"type": "stream", "step": f"future_{i}", "data": chunk}
                            future_response += chunk
                    
                    future_eval = extract_json(future_response)
                    if future_eval:
                        future_evaluations.append(future_eval)
                        yield {"type": "future_evaluation", "data": future_eval}
                except Exception as e:
                    pass
        
        # Step6: Final evaluation
        yield {"type": "status", "data": "[Step 6] Calculating final evaluation..."}
        
        # Aggregating each indicator from citizen evaluations
        citizen_personal = [e.get("personal_impact", {}).get("score", 0) for e in citizen_evaluations if "personal_impact" in e]
        citizen_family = [e.get("family_impact", {}).get("score", 0) for e in citizen_evaluations if "family_impact" in e]
        citizen_community = [e.get("community_impact", {}).get("score", 0) for e in citizen_evaluations if "community_impact" in e]
        citizen_fairness = [e.get("fairness", {}).get("score", 0) for e in citizen_evaluations if "fairness" in e]
        citizen_sustainability = [e.get("sustainability", {}).get("score", 0) for e in citizen_evaluations if "sustainability" in e]
        
        # Effectiveness and results score (directly reflecting citizen evaluations)
        effectiveness_personal = (sum(citizen_personal) / len(citizen_personal)) if citizen_personal else 50
        effectiveness_family = (sum(citizen_family) / len(citizen_family)) if citizen_family else 50
        effectiveness_community = (sum(citizen_community) / len(citizen_community)) if citizen_community else 50
        effectiveness_score = effectiveness_personal * 0.5 + effectiveness_family * 0.2 + effectiveness_community * 0.1
        
        # Fairness score (reflects 50% of citizen evaluations)
        citizen_fairness_avg = (sum(citizen_fairness) / len(citizen_fairness)) if citizen_fairness else 50
        
        # Sustainability score (reflects 50% of citizen evaluations)
        citizen_sustainability_avg = (sum(citizen_sustainability) / len(citizen_sustainability)) if citizen_sustainability else 50
        
        final_evaluator = Agent(
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            callback_handler=None,
            system_prompt="""You are a policy evaluation specialist.
Please evaluate the policy from the following five perspectives:

1. Transparency & Accountability – Weight: 20%
2. Ethical Acceptability & Social Acceptance – Weight: 10%
3. Effectiveness & Results – Weight: 25% (directly reflect citizen evaluation: 50% personal impact, 20% family impact, 10% community impact)
4. Equity – Weight: 25% (50% of this is directly reflected from citizen evaluation of fairness)
5. Sustainability & Cost Efficiency – Weight: 15% (50% of this is directly reflected from citizen evaluation of sustainability)

Output format:
```json
{{
  "equity": {{"score": 75, "comment": "Evaluation comment"}},
  "effectiveness": {{"score": 80, "comment": "Evaluation comment"}},
  "transparency": {{"score": 70, "comment": "Evaluation comment"}},
  "sustainability": {{"score": 65, "comment": "Evaluation comment"}},
  "ethical_acceptability": {{"score": 85, "comment": "Evaluation comment"}},
  "total_score": 75.5,
  "overall_comment": "Overall evaluation comment",
  "recommendation": "Recommended / Conditionally recommended / Reconsideration recommended"
}}
```

Important: Be sure to calculate total_score using the following formula:
total_score = equity.score × 0.25 + effectiveness.score × 0.25 + transparency.score × 0.20 + sustainability.score × 0.15 + ethical_acceptability.score × 0.10

IMPORTANT: Write all content in English."""
        )
        
        final_prompt = f"""Policy proposal:
{json.dumps(policy_json, ensure_ascii=False, indent=2)}

Number of citizen evaluations: {len(citizen_evaluations)}
Citizen evaluation data:
{json.dumps(citizen_evaluations, ensure_ascii=False, indent=2)}

Aggregated data from citizen evaluations:
- Average personal impact: {effectiveness_personal:.1f} points
- Average family impact: {effectiveness_family:.1f} points
- Average community impact: {effectiveness_community:.1f} points
- Average fairness: {citizen_fairness_avg:.1f} points
- Average sustainability: {citizen_sustainability_avg:.1f} points

Please evaluate the policy proposal from the following five perspectives:

1. Transparency & Accountability – Weight: 20%
   - Is the basis and process of decision-making clearly presented?
   - Evaluate the amount of supporting data and explainability.

2. Ethical Acceptability & Social Acceptance – Weight: 10%
   - Is it appropriate from the viewpoints of human rights, privacy, and ethics?

3. Effectiveness & Results – Weight: 25%
   - Directly reflect citizen evaluation: {effectiveness_score:.1f} points
   - Breakdown: Personal impact ({effectiveness_personal:.1f}) × 50% + Family impact ({effectiveness_family:.1f}) × 20% + Community impact ({effectiveness_community:.1f}) × 10%
   - Use this score as is: {effectiveness_score:.1f} points

4. Equity – Weight: 25%
   - Average citizen fairness evaluation: {citizen_fairness_avg:.1f} points (this accounts for 50%)
   - Does the policy provide benefits fairly across groups without bias? (remaining 50%)
   - Evaluate distribution of support and correction of disparities.

5. Sustainability & Cost Efficiency – Weight: 15%
   - Average citizen sustainability evaluation: {citizen_sustainability_avg:.1f} points (this accounts for 50%)
   - Is it sustainable from financial and human resource perspectives? (remaining 50%)
   - Evaluate cost-effectiveness ratio and long-term impact.

Total Score = Transparency × 0.20 + Ethical Acceptability × 0.10 + Effectiveness × 0.25 + Equity × 0.25 + Sustainability × 0.15

Recommendation criteria:
- 70 points or higher: Recommended
- 50–69 points: Conditionally recommended
- Below 50 points: Reconsideration recommended
"""
        
        final_response = ""
        async for event in final_evaluator.stream_async(final_prompt):
            if "data" in event:
                chunk = event["data"]
                yield {"type": "stream", "step": "final_assessment", "data": chunk}
                final_response += chunk
        
        final_assessment = extract_json(final_response) or {"total_score": 0}
        yield {"type": "final_assessment", "data": final_assessment}
        
        result_json = {
            "status": "success",
            "user_message": user_message,
            "research_result": research_result,
            "demographics_data": demographics_data,
            "generated_agents": {
                "policy_agents": [{"name": a["name"], "expertise": a["expertise"]} for a in agent_defs["policy_agents"]],
                "citizen_agents": [{"name": a["name"], "age": a["age"], "profile": a["profile"], "is_directly_affected": a.get("is_directly_affected", True)} for a in agent_defs["citizen_agents"]],
                "reviewer": agent_defs.get("reviewer_agent", {}).get("name", "Reviewer")
            },
            "policy_proposal": policy_json,
            "review_result": review_result,
            "citizen_evaluations": citizen_evaluations,
            "future_evaluations": future_evaluations,
            "final_assessment": final_assessment,
            "execution_status": {
                "completed": True,
                "policy_agents_count": len(agent_defs["policy_agents"]),
                "citizen_agents_count": len(agent_defs["citizen_agents"]),
                "has_future_evaluation": len(future_evaluations) > 0
            }
        }
        
        yield {"type": "complete", "data": result_json}
    
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        yield {"type": "error", "data": f"An error has occurred: {str(e)}"}
        print(f"\n\Error details:\n{error_msg}")

@app.entrypoint
async def invoke(payload):
    """AgentCore Runtime Entry point (streaming supported)"""
    async for chunk in invoke_async_streaming(payload):
        yield chunk

if __name__ == "__main__":
    # For AgentCore Runtime deployment
    app.run()
