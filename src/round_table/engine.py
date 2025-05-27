from pydantic import BaseModel, Field, root_validator
import json
from typing_extensions import Literal, Dict, Any
from utils.progress import progress
from utils.llm import call_llm
from colorama import Fore, Style
from langchain_core.prompts import ChatPromptTemplate
import time
import random
import re

class RoundTableOutput(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float = Field(description="Confidence level between 0 and 100")
    reasoning: str = Field(description="Detailed reasoning behind the decision")
    discussion_summary: str = Field(description="Summary of the key points from the discussion")
    consensus_view: str = Field(description="The main consensus view that emerged")
    dissenting_opinions: str = Field(description="Notable contrarian perspectives")
    conversation_transcript: str = Field(description="Transcript of the simulated conversation")

class AnalystPersona(BaseModel):
    name: str
    style: str
    background: str
    biases: str
    initial_position: str = ""

# Base response model that handles either direct text or common JSON formats
class TextResponseBase(BaseModel):
    text: str
    
    # Add a validator to handle multiple response formats
    @root_validator(pre=True)
    def extract_text_from_various_formats(cls, values):
        # If already a string, just use it
        if isinstance(values, str):
            return {"text": values}
        
        # If it's a dict, look for common patterns
        if isinstance(values, dict):
            # Format {"text": "content"} - direct mapping
            if "text" in values:
                return values
                
            # Format {"query": "content"} - extract content
            if "query" in values:
                return {"text": values["query"]}
                
            # Format {"question": "content"} - common format in our errors
            if "question" in values:
                return {"text": values["question"]}
                
            # Format {"response": "content"} - common format in our errors 
            if "response" in values:
                return {"text": values["response"]}
                
            # Format {"answer": "content"} - another common format in our errors
            if "answer" in values:
                return {"text": values["answer"]}
                
            # Format {"Analyst Name": "content"} - take the first value
            if len(values) == 1:
                return {"text": next(iter(values.values()))}
                
            # Format with message content
            if "content" in values:
                return {"text": values["content"]}
                
            # If we have a dict but can't find a standard pattern,
            # serialize it back to a string
            return {"text": str(values)}
            
        # For any other type, convert to string
        return {"text": str(values)}

# Response models for different conversation parts
class InitialPositionResponse(TextResponseBase):
    pass

class QuestionResponse(TextResponseBase):
    pass

class AnswerResponse(TextResponseBase):
    pass

class DebateResponse(TextResponseBase):
    pass

class SynthesisResponse(TextResponseBase):
    pass

class ConclusionResponse(TextResponseBase):
    pass

class TopicsResponse(BaseModel):
    topics: list[str]
    
    @root_validator(pre=True)
    def extract_topics(cls, values):
        # Handle string that might be a list
        if isinstance(values, str):
            try:
                # Try to parse as JSON
                parsed_json = json.loads(values)
                if isinstance(parsed_json, list):
                    return {"topics": parsed_json}
                if isinstance(parsed_json, dict) and "topics" in parsed_json:
                    return parsed_json
            except:
                # If parsing fails, use some default topics
                return {"topics": ["Valuation", "Growth prospects", "Competitive position"]}
        
        # If we already have a dict with topics, just use it
        if isinstance(values, dict) and "topics" in values:
            return values
            
        # For any other case, return default topics
        return {"topics": ["Valuation", "Growth prospects", "Competitive position"]}

# 移除了 model_name 和 model_provider 参数
# Removed model_name and model_provider parameters
def simulate_round_table(
    ticker: str,
    ticker_signals: dict[str, any],
    # model_name: str, # 已移除 (Removed)
    # model_provider: str, # 已移除 (Removed)
) -> RoundTableOutput:
    """Simulate a round table discussion among analysts with multiple API calls."""
    # Setup the analysts based on signals
    analysts = setup_analysts(ticker_signals)
    
    # Start with the moderator's introduction
    progress.update_status("round_table", ticker, "Starting moderated discussion")
    full_transcript = generate_moderator_intro(ticker)
    
    # Phase 1: Initial positions (separate API call for each analyst)
    progress.update_status("round_table", ticker, "Gathering initial positions")
    for analyst in analysts:
        if analyst.name in ticker_signals:
            try:
                position = generate_initial_position(
                    analyst_name=analyst.name,
                    ticker=ticker,
                    ticker_signal=ticker_signals[analyst.name],
                    analyst_style=analyst.style,
                    # model_name 和 model_provider 参数已移除
                    # model_name and model_provider parameters removed
                    # model_name=model_name,
                    # model_provider=model_provider
                )
                analyst.initial_position = position
                full_transcript += f"\n\n{analyst.name}: {position}"
                # Add small delays between analysts to simulate real discussion timing
                time.sleep(0.5)
            except Exception as e:
                # Continue with other analysts if one fails
                print(f"Error generating position for {analyst.name}: {e}")
                continue
    
    # Phase 2: Interactive questioning and debate (multiple turns)
    progress.update_status("round_table", ticker, "Starting interactive debate")
    
    conversation_turns = []
    # Select which analysts will participate most actively based on signals
    primary_debaters = select_primary_debaters(ticker_signals, analysts)
    
    # First round of questioning (focus on challenging assumptions)
    try:
        progress.update_status("round_table", ticker, "First round: Challenging assumptions")
        questions = generate_questions(
            ticker=ticker,
            transcript_so_far=full_transcript,
            analysts=primary_debaters,
            phase="questioning",
            # model_name 和 model_provider 参数已移除
            # model_name and model_provider parameters removed
            # model_name=model_name,
            # model_provider=model_provider
        )
        conversation_turns.extend(questions)
    except Exception as e:
        print(f"Error in questioning phase: {e}")
        questions = []
    
    # Second round: deeper debate on key disagreements
    try:
        progress.update_status("round_table", ticker, "Second round: Deeper debate")
        debate_exchanges = generate_debate_exchanges(
            ticker=ticker,
            transcript_so_far=full_transcript + "\n\n" + "\n\n".join(questions),
            analysts=analysts,
            primary_debaters=primary_debaters,
            # model_name 和 model_provider 参数已移除
            # model_name and model_provider parameters removed
            # model_name=model_name,
            # model_provider=model_provider
        )
        conversation_turns.extend(debate_exchanges)
    except Exception as e:
        print(f"Error in debate phase: {e}")
        debate_exchanges = []
    
    # Final round: synthesis and position refinement
    try:
        progress.update_status("round_table", ticker, "Final round: Synthesis")
        current_transcript = full_transcript + "\n\n" + "\n\n".join(conversation_turns)
        synthesis = generate_synthesis(
            ticker=ticker,
            transcript_so_far=current_transcript,
            analysts=primary_debaters,
            # model_name 和 model_provider 参数已移除
            # model_name and model_provider parameters removed
            # model_name=model_name,
            # model_provider=model_provider
        )
        conversation_turns.extend(synthesis)
    except Exception as e:
        print(f"Error in synthesis phase: {e}")
    
    # Add all conversation turns to the transcript
    full_transcript += "\n\n" + "\n\n".join(conversation_turns)
    
    # Moderator conclusion
    try:
        # model_name 和 model_provider 参数已移除
        # model_name and model_provider parameters removed
        moderator_conclusion = generate_moderator_conclusion(
            ticker=ticker,
            transcript=full_transcript,
            # model_name=model_name,
            # model_provider=model_provider
        )
        full_transcript += f"\n\n{moderator_conclusion}"
    except Exception as e:
        print(f"Error generating conclusion: {e}")
        full_transcript += f"\n\nModerator: Thank you all for your insights on {ticker}. This concludes our discussion."
    
    # Generate final analysis and decision
    progress.update_status("round_table", ticker, "Generating final analysis")
    try:
        final_analysis = generate_final_analysis(
            ticker=ticker,
            transcript=full_transcript,
            ticker_signals=ticker_signals,
            # model_name 和 model_provider 参数已移除
            # model_name and model_provider parameters removed
            # model_name=model_name,
            # model_provider=model_provider
        )
    except Exception as e:
        print(f"Error generating final analysis: {e}")
        # Create a default analysis
        final_analysis = {
            "signal": "neutral",
            "confidence": 50.0,
            "reasoning": "Based on the discussion with multiple perspectives.",
            "discussion_summary": "The round table included perspectives from various investment philosophies.",
            "consensus_view": "There were differing opinions on the stock's prospects.",
            "dissenting_opinions": "Analysts disagreed on valuation and growth potential."
        }
    
    return RoundTableOutput(
        signal=final_analysis["signal"],
        confidence=final_analysis["confidence"],
        reasoning=final_analysis["reasoning"],
        discussion_summary=final_analysis["discussion_summary"],
        consensus_view=final_analysis["consensus_view"],
        dissenting_opinions=final_analysis["dissenting_opinions"],
        conversation_transcript=full_transcript
    )

def setup_analysts(ticker_signals):
    """Setup the analyst personas based on available signals."""
    analysts = []
    
    persona_definitions = {
        "warren_buffett_agent": AnalystPersona(
            name="Warren Buffett",
            style="Patient, folksy but incisive, focused on business fundamentals and long-term value",
            background="Value investor, Berkshire Hathaway CEO, focused on business quality and management",
            biases="Prefers simple businesses with strong competitive advantages and long-term growth potential"
        ),
        "charlie_munger_agent": AnalystPersona(
            name="Charlie Munger",
            style="Blunt, no-nonsense, critical of foolishness, invokes mental models",
            background="Vice Chairman of Berkshire Hathaway, emphasis on rationality and psychology",
            biases="Skeptical of conventional wisdom, aversion to complexity"
        ),
        "ben_graham_agent": AnalystPersona(
            name="Ben Graham",
            style="Conservative, risk-averse, methodical, mathematical",
            background="Father of value investing, focuses on margin of safety and tangible assets",
            biases="Prefers stocks trading below intrinsic value with a margin of safety"
        ),
        "cathie_wood_agent": AnalystPersona(
            name="Cathie Wood",
            style="Bold, optimistic about disruptive innovation, future-focused",
            background="ARK Invest founder, focuses on disruptive innovation and technology",
            biases="Favors high-growth technology companies with disruptive potential"
        ),
        "bill_ackman_agent": AnalystPersona(
            name="Bill Ackman",
            style="Forceful, activist mindset, confident, pushes for concrete action",
            background="Pershing Square founder, activist investor, concentrated portfolio",
            biases="Prefers companies with potential for operational improvements or corporate actions"
        ),
        "nancy_pelosi_agent": AnalystPersona(
            name="Nancy Pelosi",
            style="Political insider, pragmatic, calm, policy-focused",
            background="Political leader with insight into regulatory and policy developments",
            biases="Attuned to companies that benefit from government policy and spending"
        ),
        "technical_analyst_agent": AnalystPersona(
            name="Technical Analyst",
            style="Chart-focused, pattern-oriented, dismissive of fundamentals when trends are clear",
            background="Professional technical analyst specializing in price patterns and momentum",
            biases="Believes price action and chart patterns predict future movements"
        ),
        "fundamentals_agent": AnalystPersona(
            name="Fundamental Analyst",
            style="By-the-numbers, methodical, skeptical of hype",
            background="Specializes in financial statement analysis and business valuation",
            biases="Focuses primarily on financial metrics and quantitative measures"
        ),
        "sentiment_agent": AnalystPersona(
            name="Sentiment Analyst",
            style="Attuned to market psychology and news flow",
            background="Expert in market sentiment, social media trends, and investor psychology",
            biases="Believes market perception often trumps fundamentals in the short term"
        ),
        "valuation_agent": AnalystPersona(
            name="Valuation Analyst",
            style="Focused on price vs. value, multiple-based comparisons",
            background="Specializes in valuation methodologies and comparative analysis",
            biases="Emphasizes relative and absolute valuation metrics"
        ),
        "wsb_agent": AnalystPersona(
            name="WSB",
            style="Irreverent, momentum-driven, contrarian, uses distinctive slang",
            background="Retail trader focused on high-conviction momentum plays and contrarian bets",
            biases="Favors high short interest stocks, options leverage, and unconventional catalysts"
        )
    }
    
    # Add analysts that have signals
    for agent_name, signal in ticker_signals.items():
        # Convert agent name to persona key (remove "_agent" suffix if present)
        persona_key = agent_name
        if persona_key.endswith("_agent"):
            persona_key = persona_key
            
        if persona_key in persona_definitions:
            analysts.append(persona_definitions[persona_key])
    
    return analysts

def generate_moderator_intro(ticker):
    """Generate the moderator's introduction."""
    return f"Moderator: Welcome everyone to our investment round table discussion on {ticker}. Today we'll examine the bull and bear cases, analyze the company's fundamentals, technical indicators, and reach a consensus investment decision. Let's begin with each of you sharing your initial position."

# 移除了 model_name 和 model_provider 参数
# Removed model_name and model_provider parameters
def generate_initial_position(analyst_name, ticker, ticker_signal, analyst_style): #, model_name, model_provider):
    """Generate initial position statement for an analyst (separate API call)."""
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""You are {analyst_name}, an investment analyst with the following style: {analyst_style}.
            
            You are participating in an investment round table discussion about {ticker}.
            Based on your analysis, you have a {ticker_signal.get('signal', 'neutral')} outlook on the stock.
            
            Generate ONLY your opening statement at the investment round table. Keep it concise (3-5 sentences) 
            but include:
            1. Your overall position (bullish/bearish/neutral)
            2. 1-2 key reasons for your position
            3. A mention of what you're most concerned about or what could change your view
            
            DO NOT speak for others or refer to what others have said yet as this is your opening statement.
            DO NOT prefix your response with your name - that will be added separately.
            Write in first person and maintain your authentic voice and investment philosophy.
            
            IMPORTANT: Return only a plain text response with no JSON formatting.
            """
        ),
        (
            "human",
            f"""As {analyst_name}, provide your opening statement about {ticker} at the investment round table.
            
            Your signal: {ticker_signal.get('signal', 'neutral')}
            Your confidence: {ticker_signal.get('confidence', 50)}
            Your reasoning: {ticker_signal.get('reasoning', 'Based on my analysis')}
            
            Remember to maintain your authentic voice and speak only as yourself in the first person.
            Do not include any JSON formatting, quotation marks, or your name in the response.
            """
        )
    ])

    prompt = template.invoke({})
    
    def create_default_position():
        return InitialPositionResponse(text=f"I'm {ticker_signal.get('signal', 'neutral')} on {ticker} based on my analysis.")
    
    # 调用 call_llm 时不再传递 model_name 和 model_provider
    # model_name and model_provider are no longer passed when calling call_llm
    response = call_llm(
        prompt=prompt,
        # model_name=model_name, # 已移除 (Removed)
        # model_provider=model_provider, # 已移除 (Removed)
        pydantic_model=InitialPositionResponse,
        agent_name="round_table",
        default_factory=create_default_position
    )
    
    return response.text.strip()

def select_primary_debaters(ticker_signals, analysts):
    """Select which analysts will lead the debate based on signals and conviction."""
    # Pick analysts with strongest conviction (highest/lowest confidence) and contradictory views
    bullish_analysts = []
    bearish_analysts = []
    neutral_analysts = []
    
    for analyst in analysts:
        if analyst.name in ticker_signals:
            signal = ticker_signals[analyst.name].get('signal', '').lower()
            confidence = ticker_signals[analyst.name].get('confidence', 50)
            
            if signal == 'bullish':
                bullish_analysts.append((analyst, confidence))
            elif signal == 'bearish':
                bearish_analysts.append((analyst, confidence))
            else:
                neutral_analysts.append((analyst, confidence))
    
    # Sort by confidence
    bullish_analysts.sort(key=lambda x: x[1], reverse=True)
    bearish_analysts.sort(key=lambda x: x[1], reverse=True)
    
    # Select top 2 from each category if available
    primary_debaters = []
    for category in [bullish_analysts, bearish_analysts, neutral_analysts]:
        for analyst, _ in category[:2]:
            if analyst not in primary_debaters:
                primary_debaters.append(analyst)
    
    # Ensure we have enough debaters (add more if needed)
    if len(primary_debaters) < 4 and len(analysts) >= 4:
        remaining = [a for a in analysts if a not in primary_debaters]
        primary_debaters.extend(remaining[:4-len(primary_debaters)])
    
    return primary_debaters

# 移除了 model_name 和 model_provider 参数
# Removed model_name and model_provider parameters
def generate_questions(ticker, transcript_so_far, analysts, phase): #, model_name, model_provider):
    """Generate probing questions between analysts with better error handling."""
    questions = []
    
    # Select who asks questions (we want to have at least 3 good questions)
    questioners = random.sample(analysts, min(3, len(analysts)))
    
    for questioner in questioners:
        # Select who to question (someone other than the questioner)
        eligible_responders = [a for a in analysts if a.name != questioner.name]
        if not eligible_responders:
            continue
        responder = random.choice(eligible_responders)
        
        # Create a fixed question format without template variables
        question_prompt = """You are an investment analyst participating in a round table discussion.

You are discussing """ + ticker + """.
You are going to ask a challenging question to another analyst.

Your question should:
1. Be specific and targeted to their expressed views
2. Challenge a key assumption or methodology
3. Require them to defend their position with evidence

Format your response EXACTLY as:
"""+ questioner.name + """: [Your question to """ + responder.name + """]"

Do not include any JSON formatting or additional text."""
        
        # Create a simple template with no variables that could cause conflicts
        simple_prompt = ChatPromptTemplate.from_template(question_prompt)
        final_prompt = simple_prompt.invoke({})
        
        def create_default_question():
            return QuestionResponse(text=f"{questioner.name}: {responder.name}, could you elaborate on your thesis for {ticker}? I'm particularly interested in your assumptions about growth and valuation.")
        
        try:
            # 调用 call_llm 时不再传递 model_name 和 model_provider
            # model_name and model_provider are no longer passed when calling call_llm
            question_result = call_llm(
                prompt=final_prompt,
                # model_name=model_name, # 已移除 (Removed)
                # model_provider=model_provider, # 已移除 (Removed)
                pydantic_model=QuestionResponse,
                agent_name="round_table",
                default_factory=create_default_question
            )
            
            question = question_result.text
            questions.append(question.strip())
            
            # Generate an answer using a similar simple template approach
            answer_prompt = """You are an investment analyst participating in a round table discussion.

You are discussing """ + ticker + """.
Another analyst has just asked you a challenging question.

Answer the question thoughtfully but defend your position. Your response should:
1. Directly address the question asked
2. Provide specific evidence or reasoning to support your view
3. Be concise (3-5 sentences)

Format your response EXACTLY as:
"""+ responder.name + """: [Your answer]"

Do not include any JSON formatting or additional text."""
            
            answer_template = ChatPromptTemplate.from_template(answer_prompt)
            answer_final_prompt = answer_template.invoke({})
            
            def create_default_answer():
                return AnswerResponse(text=f"{responder.name}: Based on my analysis of {ticker}, I believe my position is justified by the fundamentals and market conditions.")
            
            try:
                # 调用 call_llm 时不再传递 model_name 和 model_provider
                # model_name and model_provider are no longer passed when calling call_llm
                answer_result = call_llm(
                    prompt=answer_final_prompt,
                    # model_name=model_name, # 已移除 (Removed)
                    # model_provider=model_provider, # 已移除 (Removed)
                    pydantic_model=AnswerResponse,
                    agent_name="round_table",
                    default_factory=create_default_answer
                )
                
                answer = answer_result.text
                questions.append(answer.strip())
            except Exception as e:
                print(f"Error generating answer, using default: {e}")
                default_answer = create_default_answer().text
                questions.append(default_answer)
                
        except Exception as e:
            # Fallback to default question/answer
            print(f"Error generating question/answer, using defaults: {e}")
            default_q = create_default_question().text
            questions.append(default_q)
            questions.append(f"{responder.name}: My analysis of {ticker} is based on careful consideration of the fundamentals and market conditions.")
            
        # Add a small delay
        time.sleep(0.5)
    
    return questions

# 移除了 model_name 和 model_provider 参数
# Removed model_name and model_provider parameters
def identify_debate_topics(ticker, transcript): #, model_name, model_provider):
    """Identify key topics for debate from the discussion so far."""
    # Default topics to fall back on
    default_topics = ["Valuation", "Growth Prospects", "Competitive Position"]
    
    # Create a simple prompt without template variables
    topic_prompt = """You are an investment analyst moderating a round table discussion about """ + ticker + """.

Based on the transcript, identify the 3 most important topics for deeper debate.
These should be areas where analysts seem to disagree or have different perspectives.

Return ONLY a simple list of 3 topics, with no additional text.
Example: ["Valuation multiples", "AI market growth", "Competitive threats"]"""
    
    simple_prompt = ChatPromptTemplate.from_template(topic_prompt)
    final_prompt = simple_prompt.invoke({})
    
    try:
        # Modified approach: Use a string response and parse it separately
        class SimpleTextResponse(TextResponseBase):
            pass
            
        def create_default_topics_text():
            return SimpleTextResponse(text=json.dumps(default_topics))
        
        # Get response as plain text
        # 调用 call_llm 时不再传递 model_name 和 model_provider
        # model_name and model_provider are no longer passed when calling call_llm
        response_result = call_llm(
            prompt=final_prompt,
            # model_name=model_name, # 已移除 (Removed)
            # model_provider=model_provider, # 已移除 (Removed)
            pydantic_model=SimpleTextResponse,
            agent_name="round_table",
            default_factory=create_default_topics_text
        )
        
        response_text = response_result.text
        
        # Try to parse the response in multiple ways
        try:
            # First attempt: Try to parse as JSON directly
            parsed_topics = json.loads(response_text)
            if isinstance(parsed_topics, list) and len(parsed_topics) > 0:
                return parsed_topics[:3]
        except json.JSONDecodeError:
            # Second attempt: If the text isn't valid JSON, look for patterns
            lines = response_text.strip().split('\n')
            extracted_topics = []
            
            for line in lines:
                line = line.strip()
                # Skip empty lines
                if not line:
                    continue
                    
                # Try to extract from markdown list format (e.g., "1. Topic")
                if line[0].isdigit() and '. ' in line:
                    extracted_topics.append(line.split('. ', 1)[1].strip())
                # Try to extract from bullet points
                elif line.startswith('- ') or line.startswith('* '):
                    extracted_topics.append(line[2:].strip())
                # Just use the line if it seems to be a topic
                elif not line.startswith('[') and not line.startswith('{'):
                    extracted_topics.append(line)
            
            if extracted_topics:
                return extracted_topics[:3]
                
            # Third attempt: If we got a string that looks like a list but isn't valid JSON
            # Try to manually extract topics
            if '[' in response_text and ']' in response_text:
                list_content = response_text[response_text.find('[')+1:response_text.rfind(']')]
                potential_topics = [t.strip().strip('"\'') for t in list_content.split(',')]
                if potential_topics:
                    return [t for t in potential_topics if t][:3]
    
    except Exception as e:
        print(f"Error identifying debate topics: {e}")
    
    # Return default topics if all else fails
    return default_topics

# 移除了 model_name 和 model_provider 参数
# Removed model_name and model_provider parameters
def generate_debate_exchanges(ticker, transcript_so_far, analysts, primary_debaters): #, model_name, model_provider):
    """Generate deeper debate exchanges between analysts focusing on key disagreements."""
    exchanges = []
    
    # Extract key topics for debate based on initial positions
    progress.update_status("round_table", ticker, "Identifying key debate topics")
    # 调用 identify_debate_topics 时不再传递 model_name 和 model_provider
    # model_name and model_provider are no longer passed when calling identify_debate_topics
    topics = identify_debate_topics(ticker, transcript_so_far) #, model_name, model_provider)
    
    # Add a moderator message to transition to focused debate
    moderator_message = f"Moderator: Now let's dig deeper into some key areas of disagreement. Let's start by discussing {topics[0]}."
    exchanges.append(moderator_message)
    
    # For each topic, set up a focused exchange between analysts with opposite views
    for topic_idx, topic in enumerate(topics[:2]):  # Limit to top 2 topics to keep it simpler
        progress.update_status("round_table", ticker, f"Debating {topic}")
        
        if len(primary_debaters) < 2:
            continue
            
        # Select two different analysts for the debate
        debater1 = primary_debaters[0]
        debater2 = primary_debaters[1]
        
        # Generate a simple bullish point
        bullish_prompt = """You are an investment analyst participating in a round table discussion.

You are discussing """ + ticker + """ and the topic of """ + topic + """.

Make a strong, bullish argument about this topic. Your argument should:
1. Present specific evidence supporting your bullish view
2. Connect this specific topic to your overall investment thesis

Format your response EXACTLY as:
"""+ debater1.name + """: [Your bullish argument about """ + topic + """]"

Do not include any JSON formatting or additional text."""
        
        # Create the prompt without variables
        simple_prompt = ChatPromptTemplate.from_template(bullish_prompt)
        final_prompt = simple_prompt.invoke({})
        
        def create_default_argument():
            return DebateResponse(text=f"{debater1.name}: Regarding {topic}, I see strong potential for {ticker} based on the fundamentals and market trends.")
        
        try:
            # 调用 call_llm 时不再传递 model_name 和 model_provider
            # model_name and model_provider are no longer passed when calling call_llm
            argument_result = call_llm(
                prompt=final_prompt,
                # model_name=model_name, # 已移除 (Removed)
                # model_provider=model_provider, # 已移除 (Removed)
                pydantic_model=DebateResponse,
                agent_name="round_table",
                default_factory=create_default_argument
            )
            
            bullish_argument = argument_result.text
            exchanges.append(bullish_argument.strip())
        except Exception as e:
            print(f"Error generating bullish argument: {e}")
            default_arg = create_default_argument().text
            exchanges.append(default_arg)
        
        # Generate a bearish counterpoint
        bearish_prompt = """You are an investment analyst participating in a round table discussion.

You are discussing """ + ticker + """ and the topic of """ + topic + """.
Another analyst just made a bullish argument.

Respond with a strong bearish counterargument. Your counterargument should:
1. Present contrary evidence or different interpretations
2. Challenge the bullish assumption

Format your response EXACTLY as:
"""+ debater2.name + """: [Your counterargument]"

Do not include any JSON formatting or additional text."""
        
        # Create the prompt without variables
        simple_prompt = ChatPromptTemplate.from_template(bearish_prompt)
        final_prompt = simple_prompt.invoke({})
        
        def create_default_counterargument():
            return DebateResponse(text=f"{debater2.name}: I disagree with the bullish view on {topic}. The evidence actually suggests caution for {ticker}.")
        
        try:
            # 调用 call_llm 时不再传递 model_name 和 model_provider
            # model_name and model_provider are no longer passed when calling call_llm
            counterpoint_result = call_llm(
                prompt=final_prompt,
                # model_name=model_name, # 已移除 (Removed)
                # model_provider=model_provider, # 已移除 (Removed)
                pydantic_model=DebateResponse,
                agent_name="round_table",
                default_factory=create_default_counterargument
            )
            
            counterpoint = counterpoint_result.text
            exchanges.append(counterpoint.strip())
        except Exception as e:
            print(f"Error generating bearish argument: {e}")
            default_counter = create_default_counterargument().text
            exchanges.append(default_counter)
    
    return exchanges

# 移除了 model_name 和 model_provider 参数
# Removed model_name and model_provider parameters
def generate_synthesis(ticker, transcript_so_far, analysts): #, model_name, model_provider):
    """Generate synthesis statements where analysts refine their positions."""
    synthesis = []
    
    # Moderator transition to synthesis phase
    moderator_transition = "Moderator: We've had a thorough debate. Now I'd like each of you to briefly share your final position. Has anyone's view changed based on our discussion?"
    synthesis.append(moderator_transition)
    
    # Have each analyst provide a refined position (limit to a few to keep it focused)
    for analyst in analysts[:3]:
        synthesis_prompt = """You are an investment analyst participating in a round table discussion.

You are discussing """ + ticker + """.
The discussion is nearing its end, and you need to provide your final position.

Synthesize what you've heard and provide your final view.
- Include your final recommendation (buy/sell/hold)
- Keep it concise (3-5 sentences)

Format your response EXACTLY as:
"""+ analyst.name + """: [Your final position]"

Do not include any JSON formatting or additional text."""
        
        # Create the prompt without variables
        simple_prompt = ChatPromptTemplate.from_template(synthesis_prompt)
        final_prompt = simple_prompt.invoke({})
        
        def create_default_synthesis():
            return SynthesisResponse(text=f"{analyst.name}: After considering all perspectives, I maintain my position on {ticker}.")
        
        try:
            # 调用 call_llm 时不再传递 model_name 和 model_provider
            # model_name and model_provider are no longer passed when calling call_llm
            position_result = call_llm(
                prompt=final_prompt,
                # model_name=model_name, # 已移除 (Removed)
                # model_provider=model_provider, # 已移除 (Removed)
                pydantic_model=SynthesisResponse,
                agent_name="round_table",
                default_factory=create_default_synthesis
            )
            
            synthesis.append(position_result.text.strip())
        except Exception as e:
            print(f"Error generating synthesis: {e}")
            default_synthesis = create_default_synthesis().text
            synthesis.append(default_synthesis)
        
        # Small delay between analysts
        time.sleep(0.5)
    
    return synthesis

# 移除了 model_name 和 model_provider 参数
# Removed model_name and model_provider parameters
def generate_moderator_conclusion(ticker, transcript): #, model_name, model_provider):
    """Generate the moderator's conclusion."""
    conclusion_prompt = """You are the moderator of an investment round table discussion.

The discussion about """ + ticker + """ is now complete.
Provide a brief conclusion that:
1. Summarizes key points of agreement and disagreement
2. Notes the balance of bullish vs bearish views
3. Thanks the participants

Format your response EXACTLY as:
"Moderator: [Your conclusion]"

Do not include any JSON formatting or additional text."""
    
    # Create the prompt without variables
    simple_prompt = ChatPromptTemplate.from_template(conclusion_prompt)
    final_prompt = simple_prompt.invoke({})
    
    def create_default_conclusion():
        return ConclusionResponse(text=f"Moderator: Thank you all for your thoughtful analysis of {ticker}. We've heard a range of perspectives today, from bullish to bearish, each supported by different analytical approaches.")
    
    try:
        # 调用 call_llm 时不再传递 model_name 和 model_provider
        # model_name and model_provider are no longer passed when calling call_llm
        conclusion_result = call_llm(
            prompt=final_prompt,
            # model_name=model_name, # 已移除 (Removed)
            # model_provider=model_provider, # 已移除 (Removed)
            pydantic_model=ConclusionResponse,
            agent_name="round_table",
            default_factory=create_default_conclusion
        )
        
        return conclusion_result.text.strip()
    except Exception as e:
        print(f"Error generating conclusion: {e}")
        return create_default_conclusion().text

# 移除了 model_name 和 model_provider 参数
# Removed model_name and model_provider parameters
def generate_final_analysis(ticker, transcript, ticker_signals): #, model_name, model_provider):
    """Generate the final analysis and decision with retry logic for rate limits."""
    # Create a prompt that clearly includes the transcript and requests raw JSON
    analysis_prompt = "You are an objective investment analyst reviewing this round table discussion transcript:\n\n" + \
        "=== TRANSCRIPT START ===\n" + \
        transcript + "\n" + \
        "=== TRANSCRIPT END ===\n\n" + \
        "Based on this discussion about " + ticker + ", provide your immediate analysis with:\n" + \
        "1. The overall investment signal (bullish/bearish/neutral)\n" + \
        "2. A confidence level (0-100)\n" + \
        "3. Your reasoning for the decision\n" + \
        "4. A summary of the key points\n" + \
        "5. The main consensus view that emerged\n" + \
        "6. Notable dissenting opinions\n\n" + \
        "DO NOT WAIT FOR MORE INFORMATION. Analyze the transcript above and respond immediately.\n\n" + \
        "IMPORTANT: Response MUST be valid JSON with this EXACT format:\n\n" + \
        '{\n' + \
        '  "signal": "bullish",\n' + \
        '  "confidence": 75,\n' + \
        '  "reasoning": "your reasoning here",\n' + \
        '  "discussion_summary": "summary here",\n' + \
        '  "consensus_view": "consensus here",\n' + \
        '  "dissenting_opinions": "dissenting views here"\n' + \
        '}\n\n' + \
        "Use DOUBLE QUOTES for all keys and string values, not single quotes."
    
    # Define default analysis
    default_analysis = {
        "signal": "neutral",
        "confidence": 50.0,
        "reasoning": "Balanced mix of positive and negative factors with no clear consensus.",
        "discussion_summary": "The discussion covered various aspects of the company without a clear resolution.",
        "consensus_view": "No strong consensus emerged from the discussion.",
        "dissenting_opinions": "Various perspectives were presented with different analytical frameworks."
    }
    
    try:
        # Skip the ChatPromptTemplate entirely and create a HumanMessage directly
        from langchain_core.messages import HumanMessage, SystemMessage
        import time
        
        # Create messages directly without template
        system_message = SystemMessage(content="You are an objective investment analyst. Respond with raw JSON.")
        human_message = HumanMessage(content=analysis_prompt)
        
        # Get the text response directly from the LLM
        from langchain_core.language_models import BaseChatModel
        from llm.models import get_model
        from utils.progress import progress
        
        # Get the LLM model
        try:
            from llm.models import ModelProvider
            model_provider_enum = ModelProvider(model_provider)
            llm = get_model(model_name, model_provider_enum)
            
            # Add retry logic with exponential backoff
            max_retries = 5
            base_delay = 2  # Start with 2 seconds
            
            for retry_count in range(max_retries):
                try:
                    # Call the LLM directly with retry logic
                    progress.update_status("round_table", ticker, f"Generating final analysis (attempt {retry_count+1}/{max_retries})")
                    raw_response = llm.invoke([system_message, human_message])
                    response_text = raw_response.content
                    
                    # If we got here, the API call was successful
                    break
                
                except Exception as api_error:
                    # Check if it's a rate limit error (429)
                    if "429" in str(api_error) or "RESOURCE_EXHAUSTED" in str(api_error):
                        if retry_count < max_retries - 1:
                            # Calculate exponential backoff delay
                            delay = base_delay * (2 ** retry_count)
                            print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                            progress.update_status("round_table", ticker, f"Rate limited. Waiting {delay}s before retry {retry_count+2}/{max_retries}")
                            time.sleep(delay)
                            continue
                    
                    # If it's not a rate limit error or we've exhausted retries, re-raise
                    print(f"Error calling LLM: {api_error}")
                    # If all retries failed, use a simpler fallback approach
                    print("Using fallback analysis based on signals")
                    return generate_fallback_analysis(ticker_signals)
            
            # APPROACH 1: Try to extract JSON from markdown code blocks
            import re
            code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            code_block_matches = re.findall(code_block_pattern, response_text)
            
            if code_block_matches:
                for match in code_block_matches:
                    try:
                        analysis_json = json.loads(match)
                        # If we successfully parsed JSON, use it
                        break
                    except json.JSONDecodeError:
                        continue
            
            # APPROACH 2: Try to extract anything that looks like JSON object
            if 'analysis_json' not in locals():
                # Find anything that looks like a JSON object (starts with { and ends with })
                json_pattern = r'\{[\s\S]*?\}'
                json_matches = re.findall(json_pattern, response_text)
                
                if json_matches:
                    for match in json_matches:
                        try:
                            # Replace single quotes with double quotes
                            fixed_match = match.replace("'", '"')
                            analysis_json = json.loads(fixed_match)
                            # If we successfully parsed JSON, use it
                            break
                        except json.JSONDecodeError:
                            continue
            
            # APPROACH 3: Manual key-value extraction
            if 'analysis_json' not in locals():
                # Try to extract key-value pairs manually
                keys = ["signal", "confidence", "reasoning", "discussion_summary", "consensus_view", "dissenting_opinions"]
                extracted_values = {}
                
                for key in keys:
                    # Look for patterns like "key": "value" or "key":value
                    key_pattern = r'"' + key + r'"\s*:\s*("([^"]*)"|(\d+(?:\.\d+)?))'
                    key_match = re.search(key_pattern, response_text)
                    
                    if key_match:
                        if key_match.group(2):  # String value
                            extracted_values[key] = key_match.group(2)
                        elif key_match.group(3):  # Numeric value
                            extracted_values[key] = float(key_match.group(3))
                
                if extracted_values:
                    # Fill in missing values from default
                    for key in keys:
                        if key not in extracted_values:
                            extracted_values[key] = default_analysis[key]
                    
                    analysis_json = extracted_values
                else:
                    analysis_json = default_analysis
            
            # APPROACH 4: Last resort - use default values
            if 'analysis_json' not in locals():
                analysis_json = default_analysis
            
            # Validate the result
            required_keys = ["signal", "confidence", "reasoning", "discussion_summary", 
                           "consensus_view", "dissenting_opinions"]
            
            # If any key is missing, use the default value for that key
            for key in required_keys:
                if key not in analysis_json:
                    analysis_json[key] = default_analysis[key]
                    
            # Validate signal value
            if analysis_json["signal"] not in ["bullish", "bearish", "neutral"]:
                analysis_json["signal"] = default_analysis["signal"]
                
            # Ensure confidence is a number
            try:
                analysis_json["confidence"] = float(analysis_json["confidence"])
            except:
                analysis_json["confidence"] = default_analysis["confidence"]
            
            return analysis_json
        
        except Exception as e:
            print(f"Error in generate_final_analysis: {e}")
            return generate_fallback_analysis(ticker_signals)
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        return default_analysis

def generate_fallback_analysis(ticker_signals):
    """Generate an analysis based solely on the signals without using the LLM."""
    # Count the signals by type
    signal_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
    total_confidence = {"bullish": 0, "bearish": 0, "neutral": 0}
    reasonings = {"bullish": [], "bearish": [], "neutral": []}
    
    # Gather all the signals data
    for analyst, signal_data in ticker_signals.items():
        signal = signal_data.get("signal", "neutral").lower()
        if signal not in signal_counts:
            signal = "neutral"  # Default to neutral for any invalid signals
        
        signal_counts[signal] += 1
        total_confidence[signal] += signal_data.get("confidence", 50)
        
        # Collect reasoning if available
        if "reasoning" in signal_data and len(signal_data["reasoning"]) > 10:
            reasonings[signal].append(f"{analyst}: {signal_data['reasoning']}")
    
    # Determine the overall signal (most common)
    overall_signal = max(signal_counts.items(), key=lambda x: x[1])[0]
    
    # If there's a tie, use the one with highest average confidence
    tied_signals = [s for s, count in signal_counts.items() if count == signal_counts[overall_signal]]
    if len(tied_signals) > 1:
        overall_signal = max(tied_signals, key=lambda s: total_confidence[s] / max(1, signal_counts[s]))
    
    # Calculate the overall confidence
    if signal_counts[overall_signal] > 0:
        overall_confidence = total_confidence[overall_signal] / signal_counts[overall_signal]
    else:
        overall_confidence = 50.0
    
    # Generate a simple reasoning
    if reasonings[overall_signal]:
        overall_reasoning = "Based on multiple analysts: " + reasonings[overall_signal][0]
    else:
        overall_reasoning = f"The majority of analysts ({signal_counts[overall_signal]}) had a {overall_signal} outlook."
    
    # Generate discussion summary
    discussion_summary = f"The analysis included {sum(signal_counts.values())} perspectives: {signal_counts['bullish']} bullish, {signal_counts['bearish']} bearish, and {signal_counts['neutral']} neutral."
    
    # Generate consensus view and dissenting opinions
    consensus_view = f"The majority view was {overall_signal} with an average confidence of {overall_confidence:.1f}."
    
    dissenting_signals = [s for s in signal_counts.keys() if s != overall_signal and signal_counts[s] > 0]
    if dissenting_signals:
        dissenting_opinions = f"Dissenting views included {', '.join(dissenting_signals)} perspectives."
    else:
        dissenting_opinions = "There were no significant dissenting opinions."
    
    return {
        "signal": overall_signal,
        "confidence": overall_confidence,
        "reasoning": overall_reasoning,
        "discussion_summary": discussion_summary,
        "consensus_view": consensus_view,
        "dissenting_opinions": dissenting_opinions
    } 