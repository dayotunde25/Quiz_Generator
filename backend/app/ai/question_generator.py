"""
AI Question Generation Service
"""
import os
import re
import json
import time
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import spacy
import openai
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')


@dataclass
class GeneratedQuestion:
    """Data class for generated questions"""
    question_text: str
    question_type: str
    options: List[str] = None
    correct_answer: str = None
    explanation: str = None
    difficulty_level: str = 'medium'
    topic: str = None
    keywords: List[str] = None
    confidence_score: float = 0.0
    source_sentence: str = None
    bloom_taxonomy_level: str = None


class QuestionGenerator:
    """AI-powered question generation service"""
    
    def __init__(self):
        self.openai_client = None
        self.nlp = None
        self.question_generation_pipeline = None
        self.summarization_pipeline = None
        self.stop_words = set(stopwords.words('english'))
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize AI models"""
        try:
            # Initialize OpenAI client if API key is available
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                openai.api_key = openai_api_key
                self.openai_client = openai
            
            # Initialize spaCy model
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("spaCy English model not found. Please install with: python -m spacy download en_core_web_sm")
            
            # Initialize Hugging Face pipelines
            try:
                # Question generation model
                self.question_generation_pipeline = pipeline(
                    "text2text-generation",
                    model="valhalla/t5-small-qg-hl",
                    tokenizer="valhalla/t5-small-qg-hl"
                )
                
                # Summarization model for long texts
                self.summarization_pipeline = pipeline(
                    "summarization",
                    model="facebook/bart-large-cnn"
                )
            except Exception as e:
                print(f"Error initializing Hugging Face models: {e}")
        
        except Exception as e:
            print(f"Error initializing AI models: {e}")
    
    def extract_key_concepts(self, text: str) -> List[Dict[str, Any]]:
        """Extract key concepts from text using NLP"""
        concepts = []
        
        if not self.nlp:
            return concepts
        
        doc = self.nlp(text)
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT', 'WORK_OF_ART', 'LAW']:
                concepts.append({
                    'text': ent.text,
                    'type': 'entity',
                    'label': ent.label_,
                    'importance': 0.8
                })
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) > 1 and chunk.text.lower() not in self.stop_words:
                concepts.append({
                    'text': chunk.text,
                    'type': 'noun_phrase',
                    'importance': 0.6
                })
        
        # Extract important keywords
        tokens = word_tokenize(text.lower())
        pos_tags = pos_tag(tokens)
        
        for word, pos in pos_tags:
            if (pos.startswith('NN') or pos.startswith('VB') or pos.startswith('JJ')) and \
               word not in self.stop_words and len(word) > 3:
                concepts.append({
                    'text': word,
                    'type': 'keyword',
                    'pos': pos,
                    'importance': 0.4
                })
        
        # Remove duplicates and sort by importance
        unique_concepts = {}
        for concept in concepts:
            key = concept['text'].lower()
            if key not in unique_concepts or concept['importance'] > unique_concepts[key]['importance']:
                unique_concepts[key] = concept
        
        return sorted(unique_concepts.values(), key=lambda x: x['importance'], reverse=True)
    
    def generate_multiple_choice_question(self, text: str, concept: str) -> Optional[GeneratedQuestion]:
        """Generate a multiple choice question"""
        try:
            if self.openai_client:
                return self._generate_mc_with_openai(text, concept)
            else:
                return self._generate_mc_with_transformers(text, concept)
        except Exception as e:
            print(f"Error generating multiple choice question: {e}")
            return None
    
    def _generate_mc_with_openai(self, text: str, concept: str) -> Optional[GeneratedQuestion]:
        """Generate multiple choice question using OpenAI"""
        prompt = f"""
        Based on the following text, create a multiple choice question about "{concept}".
        
        Text: {text[:1000]}
        
        Generate a question with 4 options (A, B, C, D) where only one is correct.
        Format your response as JSON:
        {{
            "question": "Your question here",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "explanation": "Why this answer is correct",
            "difficulty": "easy|medium|hard",
            "topic": "Main topic"
        }}
        """
        
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return GeneratedQuestion(
                question_text=result['question'],
                question_type='multiple_choice',
                options=result['options'],
                correct_answer=result['correct_answer'],
                explanation=result['explanation'],
                difficulty_level=result.get('difficulty', 'medium'),
                topic=result.get('topic'),
                keywords=[concept],
                confidence_score=0.8,
                source_sentence=text[:200]
            )
        
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
    
    def _generate_mc_with_transformers(self, text: str, concept: str) -> Optional[GeneratedQuestion]:
        """Generate multiple choice question using Transformers"""
        try:
            # Create a simple question about the concept
            sentences = sent_tokenize(text)
            relevant_sentence = None
            
            # Find sentence containing the concept
            for sentence in sentences:
                if concept.lower() in sentence.lower():
                    relevant_sentence = sentence
                    break
            
            if not relevant_sentence:
                relevant_sentence = sentences[0] if sentences else text[:200]
            
            # Generate question using template
            question_templates = [
                f"What is {concept}?",
                f"Which of the following best describes {concept}?",
                f"What is the main characteristic of {concept}?",
                f"How is {concept} defined?"
            ]
            
            question = random.choice(question_templates)
            
            # Generate plausible distractors
            correct_answer = self._extract_answer_from_text(relevant_sentence, concept)
            distractors = self._generate_distractors(concept, correct_answer)
            
            options = [correct_answer] + distractors
            random.shuffle(options)
            
            return GeneratedQuestion(
                question_text=question,
                question_type='multiple_choice',
                options=options,
                correct_answer=correct_answer,
                explanation=f"Based on the text: {relevant_sentence[:100]}...",
                difficulty_level='medium',
                topic=concept,
                keywords=[concept],
                confidence_score=0.6,
                source_sentence=relevant_sentence
            )
        
        except Exception as e:
            print(f"Error with transformers generation: {e}")
            return None
    
    def generate_true_false_question(self, text: str, concept: str) -> Optional[GeneratedQuestion]:
        """Generate a true/false question"""
        sentences = sent_tokenize(text)
        relevant_sentences = [s for s in sentences if concept.lower() in s.lower()]
        
        if not relevant_sentences:
            return None
        
        sentence = random.choice(relevant_sentences)
        
        # Create true/false variations
        if random.choice([True, False]):
            # True statement
            question = sentence.replace('.', '').strip()
            correct_answer = 'true'
            explanation = f"This statement is true based on the provided text."
        else:
            # False statement (modify the sentence)
            question = self._create_false_statement(sentence, concept)
            correct_answer = 'false'
            explanation = f"This statement is false. The correct information is: {sentence}"
        
        return GeneratedQuestion(
            question_text=question,
            question_type='true_false',
            correct_answer=correct_answer,
            explanation=explanation,
            difficulty_level='easy',
            topic=concept,
            keywords=[concept],
            confidence_score=0.7,
            source_sentence=sentence
        )
    
    def generate_short_answer_question(self, text: str, concept: str) -> Optional[GeneratedQuestion]:
        """Generate a short answer question"""
        question_starters = [
            f"Define {concept}.",
            f"Explain what {concept} means.",
            f"Describe {concept}.",
            f"What is the purpose of {concept}?",
            f"How does {concept} work?"
        ]
        
        question = random.choice(question_starters)
        answer = self._extract_answer_from_text(text, concept)
        
        return GeneratedQuestion(
            question_text=question,
            question_type='short_answer',
            correct_answer=answer,
            explanation=f"Key points should include information about {concept}",
            difficulty_level='medium',
            topic=concept,
            keywords=[concept],
            confidence_score=0.5,
            source_sentence=text[:200]
        )
    
    def _extract_answer_from_text(self, text: str, concept: str) -> str:
        """Extract answer from text for a given concept"""
        sentences = sent_tokenize(text)
        for sentence in sentences:
            if concept.lower() in sentence.lower():
                # Extract the part that defines or describes the concept
                words = sentence.split()
                concept_index = -1
                for i, word in enumerate(words):
                    if concept.lower() in word.lower():
                        concept_index = i
                        break
                
                if concept_index != -1 and concept_index < len(words) - 3:
                    return ' '.join(words[concept_index:concept_index + 10])
        
        return f"Information about {concept} from the provided text"
    
    def _generate_distractors(self, concept: str, correct_answer: str) -> List[str]:
        """Generate plausible wrong answers for multiple choice"""
        distractors = [
            f"Alternative definition of {concept}",
            f"Common misconception about {concept}",
            f"Related but incorrect information about {concept}"
        ]
        return distractors[:3]
    
    def _create_false_statement(self, sentence: str, concept: str) -> str:
        """Create a false statement by modifying a true one"""
        # Simple negation or modification
        if " is " in sentence:
            return sentence.replace(" is ", " is not ")
        elif " are " in sentence:
            return sentence.replace(" are ", " are not ")
        elif " can " in sentence:
            return sentence.replace(" can ", " cannot ")
        else:
            return f"It is incorrect that {sentence.lower()}"
    
    def generate_questions(self, text: str, num_questions: int = 10, 
                         question_types: List[str] = None, 
                         difficulty_level: str = 'medium') -> List[GeneratedQuestion]:
        """Generate multiple questions from text"""
        if not question_types:
            question_types = ['multiple_choice', 'true_false', 'short_answer']
        
        # Extract key concepts
        concepts = self.extract_key_concepts(text)
        
        if not concepts:
            return []
        
        questions = []
        concept_index = 0
        
        for i in range(num_questions):
            if concept_index >= len(concepts):
                concept_index = 0
            
            concept = concepts[concept_index]['text']
            question_type = random.choice(question_types)
            
            question = None
            if question_type == 'multiple_choice':
                question = self.generate_multiple_choice_question(text, concept)
            elif question_type == 'true_false':
                question = self.generate_true_false_question(text, concept)
            elif question_type == 'short_answer':
                question = self.generate_short_answer_question(text, concept)
            
            if question:
                question.difficulty_level = difficulty_level
                questions.append(question)
            
            concept_index += 1
        
        return questions
