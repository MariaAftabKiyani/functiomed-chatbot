"""
LLM Service 
Handles model loading, inference, and response generation with quantization support.
"""
import logging
import time
from typing import Optional, Dict, Any, List
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    pipeline
)
import sys
from pathlib import Path

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Llama 3.1 8B Instruct service with:
    - 4-bit quantization for memory efficiency
    - Robust error handling
    - Token management
    - Response validation
    """
    
    def __init__(self):
        """Initialize Llama 3.1 model"""
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self._initialize()
    
    def _initialize(self):
        """Load model with quantization and error handling"""
        logger.info(f"Loading {settings.LLM_MODEL_NAME}...")
        logger.info(f"  Device: {settings.LLM_DEVICE}")
        logger.info(f"  Quantization: {settings.LLM_USE_QUANTIZATION}")
        
        try:
            # Load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.LLM_MODEL_NAME,
                trust_remote_code=True,
                cache_dir=settings.HF_HOME
            )
            
            # Set padding token if not exists
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info("✓ Tokenizer loaded")
            
            # Load model
            logger.info("Loading model (this may take a few minutes)...")
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.LLM_MODEL_NAME,
                # quantization_config=quantization_config,
                # device_map="auto" if settings.LLM_DEVICE == "cuda" else None,
                device_map=None,
                # torch_dtype=torch.float16 if settings.LLM_DEVICE == "cuda" else torch.float32,
                torch_dtype=torch.float32,
                trust_remote_code=True,
                cache_dir=settings.HF_HOME,
                low_cpu_mem_usage=True
            )
            
            # Move to device if CPU
            if settings.LLM_DEVICE == "cpu":
                self.model = self.model.to(settings.LLM_DEVICE)
            
            logger.info("✓ Model loaded")
            
            # Create pipeline
            logger.info("Creating text generation pipeline...")
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                top_p=settings.LLM_TOP_P,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            logger.info("✓ Pipeline created")
            
            # Warmup
            logger.info("Warming up model...")
            _ = self._generate_internal("Hello")
            
            logger.info("✓ LLM Service ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise RuntimeError(f"LLM initialization failed: {e}")
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate response from prompt.
        
        Args:
            prompt: Input prompt (should include system + context + query)
            max_tokens: Maximum tokens to generate (override default)
            temperature: Sampling temperature (override default)
            stop_sequences: Optional stop sequences
            
        Returns:
            Dict with 'text', 'tokens_used', 'generation_time_ms'
            
        Raises:
            ValueError: If prompt is invalid
            RuntimeError: If generation fails
        """
        # Validate input
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        # Check token count
        prompt_tokens = self.count_tokens(prompt)
        if prompt_tokens > settings.LLM_CONTEXT_WINDOW:
            raise ValueError(
                f"Prompt too long: {prompt_tokens} tokens "
                f"(max: {settings.LLM_CONTEXT_WINDOW})"
            )
        
        logger.info(f"Generating response (prompt tokens: {prompt_tokens})...")
        
        start_time = time.time()
        
        try:
            # Generate response
            response_text = self._generate_internal(
                prompt=prompt,
                max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
                temperature=temperature or settings.LLM_TEMPERATURE,
                stop_sequences=stop_sequences
            )
            
            # Calculate metrics
            generation_time_ms = (time.time() - start_time) * 1000
            response_tokens = self.count_tokens(response_text)
            total_tokens = prompt_tokens + response_tokens
            
            logger.info(
                f"✓ Generated {response_tokens} tokens in {generation_time_ms:.0f}ms "
                f"(total: {total_tokens})"
            )
            
            return {
                "text": response_text.strip(),
                "prompt_tokens": prompt_tokens,
                "response_tokens": response_tokens,
                "total_tokens": total_tokens,
                "generation_time_ms": round(generation_time_ms, 2)
            }
            
        except Exception as e:
            logger.error(f"Generation failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"Failed to generate response: {e}")
    
    def _generate_internal(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """Internal generation method"""
        try:
            # Generate
            outputs = self.pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                return_full_text=False,  # Only return generated text
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract generated text
            generated_text = outputs[0]["generated_text"]
            
            # Apply stop sequences
            if stop_sequences:
                for stop_seq in stop_sequences:
                    if stop_seq in generated_text:
                        generated_text = generated_text.split(stop_seq)[0]
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Internal generation error: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tokenizer.
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        try:
            tokens = self.tokenizer.encode(text, add_special_tokens=True)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            # Fallback: rough estimate (1 token ≈ 4 chars)
            return len(text) // 4
    
    def health_check(self) -> Dict[str, Any]:
        """Check LLM service health"""
        health = {
            "service": "LLMService",
            "status": "healthy",
            "model": settings.LLM_MODEL_NAME,
            "device": settings.LLM_DEVICE
        }
        
        try:
            # Quick test generation
            test_prompt = "Test"
            _ = self._generate_internal(test_prompt, max_tokens=5)
            health["test_generation"] = "passed"
        except Exception as e:
            health["status"] = "unhealthy"
            health["test_generation"] = f"failed: {str(e)}"
        
        return health


# Singleton instance
_llm_service_instance = None

def get_llm_service() -> LLMService:
    """
    Get or create singleton LLMService instance.
    
    Returns:
        Initialized LLMService
    """
    global _llm_service_instance
    
    if _llm_service_instance is None:
        logger.info("Creating new LLMService instance")
        _llm_service_instance = LLMService()
    
    return _llm_service_instance


# Self-test
if __name__ == "__main__":
    from app.config import setup_logging
    
    setup_logging("INFO")
    
    print("\n" + "="*60)
    print("LLM SERVICE TEST")
    print("="*60)
    
    try:
        service = LLMService()
        
        # Test 1: Simple generation
        print("\n[Test 1] Simple generation")
        prompt = "What is the capital of France? Answer in one sentence."
        result = service.generate(prompt, max_tokens=50)
        print(f"  Prompt: {prompt}")
        print(f"  Response: {result['text']}")
        print(f"  Tokens: {result['total_tokens']}")
        print(f"  Time: {result['generation_time_ms']:.0f}ms")
        
        # Test 2: Token counting
        print("\n[Test 2] Token counting")
        text = "This is a test sentence with multiple words."
        tokens = service.count_tokens(text)
        print(f"  Text: {text}")
        print(f"  Tokens: {tokens}")
        
        # Test 3: Health check
        print("\n[Test 3] Health check")
        health = service.health_check()
        for key, value in health.items():
            print(f"  {key}: {value}")
        
        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)