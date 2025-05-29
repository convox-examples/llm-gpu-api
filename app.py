import os
import json
import time
import logging
import hashlib
from typing import Optional
import torch
import redis
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig,
    pipeline
)
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLM API", 
    version="1.0.0",
    description="Production-ready Large Language Model API with GPU acceleration"
)

class GenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    max_new_tokens: int = Field(default=100, ge=1, le=500)
    temperature: float = Field(default=0.7, ge=0.1, le=2.0)
    top_p: float = Field(default=0.9, ge=0.1, le=1.0)
    do_sample: bool = Field(default=True)
    stream: bool = Field(default=False)

class GenerationResponse(BaseModel):
    prompt: str
    generated_text: str
    processing_time: float
    device_used: str
    cached: bool
    tokens_generated: int

# Initialize Redis
redis_client = None
try:
    redis_url = os.getenv('CACHE_URL')
    if redis_url:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info("Redis cache connected")
except Exception as e:
    logger.warning(f"Redis not available: {e}")

MODEL_NAME = os.getenv('MODEL_NAME', 'microsoft/DialoGPT-medium')
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_MEMORY_GB = int(os.getenv('MAX_MEMORY_GB', '12'))

tokenizer = None
model = None
text_generator = None

def initialize_model():
    """Initialize and load the LLM model"""
    global tokenizer, model, text_generator

    logger.info(f"Initializing model {MODEL_NAME} on {DEVICE}")

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"GPU: {gpu_name}, Memory: {gpu_memory:.1f}GB")

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            padding_side='left',
            cache_dir='/tmp/.transformers'
        )

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model_kwargs = {
            "cache_dir": '/tmp/.transformers',
            "torch_dtype": torch.float16 if DEVICE == "cuda" else torch.float32,
        }

        if DEVICE == "cuda":
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_enable_fp32_cpu_offload=True
            )

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            **model_kwargs
        )

        # Do NOT pass device= when using Accelerate or quantized models
        text_generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32
        )

        logger.info("Model initialized successfully")

    except Exception as e:
        logger.error(f"Model initialization failed: {e}")
        raise

def get_cache_key(prompt: str, params: dict) -> str:
    cache_data = f"{prompt}:{json.dumps(params, sort_keys=True)}"
    return f"llm:{hashlib.md5(cache_data.encode()).hexdigest()}"

def cache_response(key: str, response: dict, ttl: int = 3600):
    if redis_client:
        try:
            redis_client.setex(key, ttl, json.dumps(response))
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

def get_cached_response(key: str) -> Optional[dict]:
    if redis_client:
        try:
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
    return None

@app.on_event("startup")
async def startup_event():
    initialize_model()

@app.get("/health")
async def health_check():
    health = {
        "status": "healthy",
        "model": MODEL_NAME,
        "device": DEVICE,
        "gpu_available": torch.cuda.is_available(),
        "model_loaded": model is not None,
        "cache_available": redis_client is not None
    }

    if torch.cuda.is_available():
        health.update({
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f}GB",
            "gpu_memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f}GB"
        })

    return health

@app.get("/")
async def root():
    return {
        "message": "LLM API",
        "version": "1.0.0",
        "model": MODEL_NAME,
        "device": DEVICE,
        "endpoints": {
            "generate": "/generate",
            "health": "/health",
            "metrics": "/metrics"
        }
    }

@app.get("/metrics")
async def metrics():
    data = {
        "model": MODEL_NAME,
        "device": DEVICE,
        "requests_cached": 0
    }

    if torch.cuda.is_available():
        data.update({
            "gpu_memory_used": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f}GB",
            "gpu_temperature": "N/A"
        })

    return data

@app.post("/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest, background_tasks: BackgroundTasks):
    start = time.time()

    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    cache_params = {
        "max_new_tokens": request.max_new_tokens,
        "temperature": request.temperature,
        "top_p": request.top_p,
        "do_sample": request.do_sample
    }
    cache_key = get_cache_key(request.prompt, cache_params)

    cached = get_cached_response(cache_key)
    if cached:
        logger.info("Serving from cache")
        cached["processing_time"] = time.time() - start
        cached["cached"] = True
        return GenerationResponse(**cached)

    try:
        gen_args = {
            "max_new_tokens": request.max_new_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "do_sample": request.do_sample,
            "pad_token_id": tokenizer.eos_token_id,
            "return_full_text": False
        }

        result = text_generator(request.prompt, **gen_args)[0]
        text = result["generated_text"]
        tokens = len(tokenizer.encode(text))

        response = {
            "prompt": request.prompt,
            "generated_text": text,
            "processing_time": time.time() - start,
            "device_used": DEVICE,
            "cached": False,
            "tokens_generated": tokens
        }

        background_tasks.add_task(cache_response, cache_key, response, 3600)
        logger.info(f"Generated {tokens} tokens in {response['processing_time']:.2f}s")
        return GenerationResponse(**response)

    except Exception as e:
        logger.error(f"Generation error: {e}")
        if "out of memory" in str(e).lower():
            raise HTTPException(status_code=507, detail="GPU memory insufficient")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
