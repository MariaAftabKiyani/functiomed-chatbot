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
    LLM service supporting Llama 3.2 1B Instruct with:
    - CPU-only inference
    - Automatic input truncation for long contexts
    - Robust error handling
    - Token management
    - Response validation
    """

    def __init__(self):
        """Initialize LLM model for CPU inference"""
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self._initialize()
    
    def _initialize(self):
        """Load model for CPU inference"""
        logger.info(f"Loading {settings.LLM_MODEL_NAME}...")
        logger.info(f"  Device: CPU")
        logger.info(f"  Mode: Full precision (FP32)")

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

            # Load model for CPU
            logger.info("Loading model (this may take a few minutes)...")
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.LLM_MODEL_NAME,
                torch_dtype=torch.float32,  # FP32 for CPU
                trust_remote_code=True,
                cache_dir=settings.HF_HOME,
                low_cpu_mem_usage=True
            )

            # Move to CPU
            self.model = self.model.to("cpu")
            
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

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if not text:
            return 0

        return len(self.tokenizer.encode(text, add_special_tokens=False))

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
        """Internal generation method with detailed error handling"""
        try:
            # Validate pipeline exists
            if self.pipeline is None:
                logger.error("Pipeline is not initialized!")
                raise RuntimeError("Text generation pipeline not initialized")

            if self.model is None:
                logger.error("Model is not loaded!")
                raise RuntimeError("Model not loaded")

            if self.tokenizer is None:
                logger.error("Tokenizer is not loaded!")
                raise RuntimeError("Tokenizer not loaded")

            # Get model's max position embeddings (context limit)
            model_max_length = getattr(self.model.config, 'max_position_embeddings', 2048)

            # Tokenize to check length
            input_ids = self.tokenizer.encode(prompt, add_special_tokens=True)
            input_length = len(input_ids)

            # Calculate safe max length (leave room for generation)
            safe_max_input = model_max_length - max_tokens - 10  # Safety buffer

            # Truncate if needed
            if input_length > safe_max_input:
                logger.warning(
                    f"Input too long ({input_length} tokens), truncating to {safe_max_input} tokens "
                    f"(model max: {model_max_length}, max_new_tokens: {max_tokens})"
                )
                # Truncate from the beginning, keeping the most recent context
                input_ids = input_ids[-safe_max_input:]
                prompt = self.tokenizer.decode(input_ids, skip_special_tokens=True)
                logger.debug(f"Truncated prompt length: {len(input_ids)} tokens")

            logger.debug(f"Pipeline parameters:")
            logger.debug(f"  input_tokens: {len(input_ids)}")
            logger.debug(f"  max_new_tokens: {max_tokens}")
            logger.debug(f"  temperature: {temperature}")
            logger.debug(f"  do_sample: {temperature > 0}")
            logger.debug(f"  return_full_text: False")

            # Generate with explicit error handling
            logger.debug("Calling pipeline...")
            try:
                outputs = self.pipeline(
                    prompt,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0,
                    return_full_text=False,  # Only return generated text
                    pad_token_id=self.tokenizer.eos_token_id,
                    truncation=True,  # Enable truncation in pipeline
                    max_length=model_max_length  # Set explicit max length
                )
            except Exception as pipe_error:
                logger.error(f"Pipeline execution failed: {type(pipe_error).__name__}")
                logger.error(f"  Error details: {str(pipe_error)}")
                import traceback
                logger.error(f"  Traceback:\n{traceback.format_exc()}")
                raise RuntimeError(f"Pipeline execution failed: {str(pipe_error)}") from pipe_error

            logger.debug(f"Pipeline returned {len(outputs)} outputs")

            # Validate outputs
            if not outputs or len(outputs) == 0:
                logger.error("Pipeline returned empty outputs!")
                return ""

            # Extract generated text
            try:
                generated_text = outputs[0]["generated_text"]
                logger.debug(f"Extracted text: '{generated_text[:100]}...'")
            except (KeyError, IndexError, TypeError) as extract_error:
                logger.error(f"Failed to extract generated text: {extract_error}")
                logger.error(f"  Output structure: {outputs}")
                raise RuntimeError(f"Invalid output structure from pipeline: {extract_error}") from extract_error

            # Apply stop sequences
            if stop_sequences:
                logger.debug(f"Applying stop sequences: {stop_sequences}")
                for stop_seq in stop_sequences:
                    if stop_seq in generated_text:
                        logger.debug(f"  Found stop sequence '{stop_seq}', truncating")
                        generated_text = generated_text.split(stop_seq)[0]

            result = generated_text.strip()
            logger.debug(f"Final generated text length: {len(result)} characters")
            return result

        except RuntimeError:
            # Re-raise RuntimeErrors as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error in _generate_internal: {type(e).__name__}")
            logger.error(f"  Error message: {str(e)}")
            import traceback
            logger.error(f"  Full traceback:\n{traceback.format_exc()}")
            raise RuntimeError(f"Internal generation error: {type(e).__name__}: {str(e)}") from e
    
    
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
        print(f"  Tokens: {result['tokens_used']} (prompt: {result['prompt_tokens']}, completion: {result['completion_tokens']})")
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