"""
Kimi LLM Provider for Sisters-Multilingual-Coach
Used for: Writing correction, Speaking feedback, Sister responses
"""

import os
from typing import Optional
from openai import OpenAI


class KimiLLM:
    """Kimi (Moonshot AI) LLM Provider"""

    def __init__(self):
        self.api_key = os.getenv("KIMI_API_KEY")
        if not self.api_key:
            raise ValueError("KIMI_API_KEY not set in environment")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.moonshot.ai/v1"
        )
        self.model = os.getenv("KIMI_MODEL", "moonshot-v1-8k")

    def generate(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
        """
        Generic text generation method.

        Args:
            prompt: User prompt
            system_prompt: System instruction

        Returns:
            Generated text response
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content

    def correct_writing(self, native_text: str, target_text: str, native_lang: str = "日本語", target_lang: str = "English") -> dict:
        """
        Correct user's writing in target language based on native language intent.

        Args:
            native_text: What the user wants to say in their native language
            target_text: User's attempt in the target language
            native_lang: User's native language name
            target_lang: Target language being learned

        Returns:
            dict with corrected text and explanation
        """
        prompt = f"""You are a {target_lang} writing tutor for {native_lang} speakers.

The student wants to say (in {native_lang}): "{native_text}"
They wrote (in {target_lang}): "{target_text}"

Please:
1. Correct any grammar, spelling, or word choice errors in their {target_lang}
2. Explain each correction in {native_lang} (briefly)
3. Rate the attempt (1-5 stars)

Respond in this JSON format:
{{
    "original": "student's original text",
    "corrected": "corrected {target_lang} text",
    "is_correct": true/false,
    "corrections": [
        {{"error": "what was wrong", "fix": "how to fix", "explanation": "explanation in {native_lang}"}}
    ],
    "rating": 4,
    "encouragement": "encouraging message in {native_lang}"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a helpful {target_lang} tutor. Always respond in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        import json
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "original": target_text,
                "corrected": target_text,
                "is_correct": True,
                "corrections": [],
                "rating": 3,
                "encouragement": "Keep going!"
            }

    def correct_speaking(self, target_text: str, spoken_text: str, native_lang: str = "日本語", target_lang: str = "English") -> dict:
        """
        Compare what user should have said vs what they actually said.

        Args:
            target_text: Target sentence to speak
            spoken_text: What was recognized from speech
            native_lang: User's native language for feedback
            target_lang: Language being practiced

        Returns:
            dict with comparison and pronunciation tips
        """
        prompt = f"""You are a pronunciation coach for {native_lang} speakers learning {target_lang}.

Target sentence: "{target_text}"
What the student said (from speech recognition): "{spoken_text}"

Please:
1. Compare word by word
2. Identify pronunciation issues common to {native_lang} speakers
3. Give specific tips in {native_lang}

Respond in this JSON format:
{{
    "target": "target text",
    "spoken": "what was recognized",
    "accuracy_percent": 85,
    "word_comparison": [
        {{"target": "word", "spoken": "what was said", "correct": false, "tip": "tip in {native_lang}"}}
    ],
    "overall_feedback": "overall feedback in {native_lang}",
    "focus_point": "focus point in {native_lang}"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a helpful {target_lang} pronunciation coach. Always respond in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        import json
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {
                "target": target_text,
                "spoken": spoken_text,
                "accuracy_percent": 100,
                "word_comparison": [],
                "overall_feedback": "Could not analyze",
                "focus_point": "Please try again"
            }

    def generate_conversation_starter(
        self,
        sister_name: str,
        target_language: str = "English",
        native_language: str = "日本語",
        cefr_level: str = "A2"
    ) -> dict:
        """
        Generate a conversation starter from the character (for listening mode).
        The character initiates the conversation with a question or statement.
        """
        sister_personalities = {
            "Botan": "cheerful, trendy, uses casual language, loves entertainment and social topics. Might ask about weekend plans, favorite shows, or social media",
            "Kasho": "professional, logical, uses formal language, expert in business and music. Might ask about work, career goals, or professional topics",
            "Yuri": "analytical, curious, interested in technology, programming, and science. Might ask about tech gadgets, coding, or interesting scientific topics",
            "Ojisan": "friendly American uncle in his 50s, uses simple and clear language, loves sports (especially baseball and football), BBQ, cars, and dad jokes. Might ask about the game last night, weekend BBQ plans, or tell a dad joke"
        }

        level_guidelines = {
            "A1": "Use very simple words and short sentences. Basic greetings and simple questions.",
            "A2": "Use simple everyday vocabulary. Basic questions about daily life.",
            "B1": "Use intermediate vocabulary. Can discuss familiar topics with some detail.",
            "B2": "Use varied vocabulary and more complex sentences. Can discuss abstract topics.",
            "C1": "Use advanced vocabulary, idioms, and nuanced expressions.",
            "C2": "Use sophisticated language with cultural references and subtle nuances."
        }

        personality = sister_personalities.get(sister_name, sister_personalities["Botan"])
        level_guide = level_guidelines.get(cefr_level, level_guidelines["A2"])

        prompt = f"""You are {sister_name}, starting a conversation with a language learner.
Personality: {personality}

The learner's level: CEFR {cefr_level}
Language guideline: {level_guide}

Generate a natural conversation starter in {target_language} that {sister_name} would say.
This should be a question or statement that invites a response.
Keep it appropriate for the learner's level.

Respond in this JSON format:
{{
    "prompt_target": "Your conversation starter in {target_language}",
    "prompt_native": "Translation in {native_language}",
    "context_hint": "Brief hint about what kind of response is expected (in {native_language})",
    "words_to_highlight": ["key", "vocabulary", "words"]
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are {sister_name}, starting a friendly conversation. Always respond in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )

        import json
        try:
            result = json.loads(response.choices[0].message.content)
            return {
                "prompt_en": result.get("prompt_target", result.get("prompt_en", "")),
                "prompt_jp": result.get("prompt_native", result.get("prompt_jp", "")),
                "context_hint": result.get("context_hint", ""),
                "words_to_highlight": result.get("words_to_highlight", [])
            }
        except json.JSONDecodeError:
            # Fallback prompts per character
            fallbacks = {
                "Botan": {"prompt_en": "Hey! What are you up to this weekend?", "prompt_jp": "ねえ！今週末は何するの？"},
                "Kasho": {"prompt_en": "Good morning. How is your project progressing?", "prompt_jp": "おはようございます。プロジェクトの進捗はいかがですか？"},
                "Yuri": {"prompt_en": "I just read about a new AI model. Have you heard about it?", "prompt_jp": "新しいAIモデルについて読んだんだけど、聞いたことある？"},
                "Ojisan": {"prompt_en": "Hey buddy! Did you catch the game last night?", "prompt_jp": "よお！昨日の試合見た？"}
            }
            fb = fallbacks.get(sister_name, fallbacks["Botan"])
            return {
                "prompt_en": fb["prompt_en"],
                "prompt_jp": fb["prompt_jp"],
                "context_hint": "",
                "words_to_highlight": []
            }

    def sister_response(
        self,
        sister_name: str,
        user_message: str,
        conversation_history: list = None,
        target_language: str = "English",
        native_language: str = "日本語"
    ) -> dict:
        """
        Generate sister's response in target language with native language translation.
        """
        sister_personalities = {
            "Botan": "cheerful, trendy, uses casual language, loves entertainment and social topics",
            "Kasho": "professional, logical, uses formal language, expert in business and music",
            "Yuri": "analytical, curious, interested in technology, programming, and science",
            "Ojisan": "friendly American uncle in his 50s, uses simple and clear language, loves sports (especially baseball and football), BBQ, cars, and dad jokes. Speaks in a warm, encouraging way like a supportive neighbor"
        }

        personality = sister_personalities.get(sister_name, sister_personalities["Botan"])

        prompt = f"""You are {sister_name}, a friendly language learning partner.
Personality: {personality}

The student said (in {target_language}): "{user_message}"

Respond naturally in {target_language} as {sister_name} would.
Keep your response conversational and encouraging (2-3 sentences).
Also provide translation in {native_language}.

Respond in this JSON format:
{{
    "response_target": "Your response in {target_language}",
    "response_native": "Translation in {native_language}",
    "words_to_highlight": ["key", "vocabulary", "words"]
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are {sister_name}, a language learning partner. Always respond in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        import json
        try:
            result = json.loads(response.choices[0].message.content)
            # Normalize keys for compatibility
            return {
                "response_en": result.get("response_target", result.get("response_en", "")),
                "response_jp": result.get("response_native", result.get("response_jp", "")),
                "words_to_highlight": result.get("words_to_highlight", [])
            }
        except json.JSONDecodeError:
            return {
                "response_en": "That's interesting! Tell me more.",
                "response_jp": "Interesting!",
                "words_to_highlight": ["interesting", "more"]
            }

    def generate_placement_test(self, test_type: str = "grammar", target_language: str = "English") -> dict:
        """
        Generate CEFR placement test questions.

        Args:
            test_type: "grammar", "vocabulary", or "listening"
            target_language: Language being tested
        """
        import random

        # Random topics for variety
        grammar_topics = [
            "travel and vacation", "work and career", "food and cooking",
            "sports and hobbies", "technology and internet", "family and relationships",
            "shopping and money", "health and fitness", "weather and seasons",
            "movies and entertainment", "education and learning", "city life"
        ]
        vocab_themes = [
            "emotions and feelings", "nature and environment", "business and finance",
            "art and culture", "science and technology", "daily routines",
            "social media", "travel experiences", "food and dining", "fashion and style"
        ]
        listening_scenarios = [
            "at a coffee shop", "booking a hotel", "at the airport",
            "job interview", "doctor's appointment", "restaurant order",
            "asking for directions", "phone conversation", "meeting a friend",
            "at a store", "travel planning", "weekend plans"
        ]

        topic = random.choice(grammar_topics)
        theme = random.choice(vocab_themes)
        scenario = random.choice(listening_scenarios)

        prompts = {
            "grammar": f"""Generate 5 UNIQUE {target_language} grammar questions for a placement test.
Topic theme: {topic}

Include questions ranging from A1 (beginner) to C1 (advanced) level.
Make sure questions are DIFFERENT from typical textbook examples.
All questions and options must be in {target_language}.

Create questions in this format:
- 2 easy questions (A1-A2): basic verb tenses, simple sentences
- 2 medium questions (B1-B2): conditionals, passive voice, relative clauses
- 1 hard question (C1): complex structures, nuanced grammar

Respond in JSON:
{{
    "questions": [
        {{
            "level": "A1",
            "question": "Choose the correct word: [sentence in {target_language}]",
            "options": ["option1", "option2", "option3", "option4"],
            "correct": 1,
            "explanation": "Brief explanation"
        }}
    ]
}}""",
            "vocabulary": f"""Generate 5 UNIQUE {target_language} vocabulary questions for a placement test.
Theme: {theme}

Include questions ranging from A1 (beginner) to C1 (advanced) level.
Make sure to use DIFFERENT words each time, not common textbook examples.
All questions and options must be in {target_language}.

Create questions testing word meaning and usage:
- 2 easy questions (A1-A2): common everyday words
- 2 medium questions (B1-B2): academic/business vocabulary
- 1 hard question (C1): nuanced words, idioms, phrasal verbs

Respond in JSON:
{{
    "questions": [
        {{
            "level": "A1",
            "question": "Question in {target_language}",
            "options": ["option1", "option2", "option3", "option4"],
            "correct": 2,
            "explanation": "Brief explanation"
        }}
    ]
}}""",
            "listening": f"""Generate 3 UNIQUE {target_language} listening comprehension scenarios for a placement test.
Scenario setting: {scenario}

Create short dialogues/sentences in {target_language} that would be read aloud.
Make the conversations natural and realistic.
All audio_text, questions, and options must be in {target_language}.

- 1 easy (A1-A2): simple greeting or basic question
- 1 medium (B1-B2): everyday conversation with some detail
- 1 hard (C1): complex statement with nuance or implied meaning

Respond in JSON:
{{
    "questions": [
        {{
            "level": "A1",
            "audio_text": "Sentence in {target_language} to be read aloud",
            "question": "Question about the audio in {target_language}",
            "options": ["option1", "option2", "option3", "option4"],
            "correct": 1,
            "explanation": "Brief explanation"
        }}
    ]
}}"""
        }

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an English test generator. Always respond in valid JSON."},
                {"role": "user", "content": prompts.get(test_type, prompts["grammar"])}
            ],
            temperature=0.7
        )

        import json
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"questions": []}

    def calculate_cefr_level(self, results: dict) -> dict:
        """
        Calculate CEFR level based on test results.

        Args:
            results: dict with correct answers per level
                {"A1": 2, "A2": 1, "B1": 1, "B2": 0, "C1": 0}
        """
        prompt = f"""Based on these English placement test results, determine the CEFR level.

Test Results (correct answers per level):
{results}

Total questions per category:
- Grammar: 5 questions (2 A1-A2, 2 B1-B2, 1 C1)
- Vocabulary: 5 questions (2 A1-A2, 2 B1-B2, 1 C1)
- Listening: 3 questions (1 A1-A2, 1 B1-B2, 1 C1)

Determine the appropriate CEFR level (A1, A2, B1, B2, C1, or C2).

Respond in JSON:
{{
    "level": "B1",
    "level_name_en": "Intermediate",
    "level_name_jp": "中級",
    "description_en": "Can understand main points of clear standard input on familiar matters.",
    "description_jp": "日常的な話題について、要点を理解できるレベルです。",
    "strengths_jp": ["基本的な文法は理解している", "日常語彙は十分"],
    "areas_to_improve_jp": ["複雑な文構造", "ビジネス語彙"],
    "confidence": 0.85
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an English level assessment expert. Always respond in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        import json
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {
                "level": "A2",
                "level_name_en": "Elementary",
                "level_name_jp": "初級",
                "description_jp": "レベル判定ができませんでした。A2として開始します。",
                "confidence": 0.5
            }

    def analyze_performance(self, session_data: dict) -> dict:
        """
        Analyze learning session performance for continuous level adjustment.

        Args:
            session_data: Performance metrics from learning sessions
        """
        prompt = f"""Analyze this English learning session performance:

Performance Data:
- Writing accuracy: {session_data.get('writing_accuracy', 0)}%
- Speaking accuracy: {session_data.get('speaking_accuracy', 0)}%
- Quiz correct rate: {session_data.get('quiz_correct_rate', 0)}%
- Current CEFR level: {session_data.get('current_level', 'A2')}
- Sessions completed: {session_data.get('sessions_completed', 0)}

Based on this data, recommend if the level should be adjusted.

Respond in JSON:
{{
    "should_adjust": true/false,
    "recommended_level": "B1",
    "adjustment_reason_jp": "理由の説明",
    "confidence": 0.8
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an English learning analyst. Always respond in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        import json
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"should_adjust": False, "confidence": 0.5}

    def generate_quiz(self, sister_response: str) -> dict:
        """
        Generate a comprehension quiz based on sister's response.
        """
        prompt = f"""Based on this English sentence, create a simple comprehension quiz:

"{sister_response}"

Create a multiple choice question to check if the student understood.

Respond in this JSON format:
{{
    "question_en": "What did the speaker ask/say?",
    "question_jp": "話者は何を聞きましたか？",
    "options": [
        {{"text": "option A", "correct": false}},
        {{"text": "option B", "correct": true}},
        {{"text": "option C", "correct": false}},
        {{"text": "option D", "correct": false}}
    ],
    "explanation_jp": "正解の解説"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a quiz generator. Always respond in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        import json
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {
                "question_en": "Did you understand?",
                "question_jp": "理解できましたか？",
                "options": [
                    {"text": "Yes", "correct": True},
                    {"text": "No", "correct": False}
                ],
                "explanation_jp": "クイズを生成できませんでした"
            }
