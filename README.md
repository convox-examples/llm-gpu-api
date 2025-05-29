# GPU-Accelerated LLM API with Convox

Deploy a production-ready Large Language Model (LLM) API with GPU auto-scaling using Convox. This example demonstrates how to build and deploy a text generation service that automatically scales GPU resources based on demand.

## 🚀 What This Example Demonstrates

- **GPU-accelerated inference** using NVIDIA CUDA
- **Auto-scaling** based on GPU resource utilization
- **Production-ready FastAPI** with comprehensive health checks
- **Redis caching** for improved performance
- **Zero-downtime deployments** with rolling updates
- **Cost optimization** through intelligent scaling

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   LLM API        │────│     Redis       │
│   (Auto SSL)    │    │   (GPU Enabled)  │    │   (Cache)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────────────────┐
                       │   NVIDIA GPU     │
                       │   (Auto-scaling) │
                       └──────────────────┘
```

## 📋 Prerequisites

- [Convox account](https://console.convox.com/signup) (free)
- AWS account with GPU instance access
- Docker (for local development - optional)

## 🎯 Model Information

This example uses **Microsoft DialoGPT-medium**, a free conversational AI model that:
- ✅ **Requires no API keys** - completely open source
- ✅ **Downloads automatically** during deployment (~350MB)
- ✅ **Runs efficiently** on a single GPU
- ✅ **Generates human-like responses**

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/convox-examples/llm-gpu-api.git
cd llm-gpu-api
```

### 2. Set Up Convox

1. [Sign up for Convox](https://console.convox.com/signup)
2. Create a **Runtime Integration** for AWS
3. Install a **GPU-enabled Rack**:
   - Name: `ai-production`
   - Region: `us-east-1` (or region with GPU availability)
   - Instance type: `g4dn.xlarge` or `p3.2xlarge`
   - **Important**: Set `nvidia_device_plugin_enable=true`

### 3. Deploy the Application

```bash
# Install Convox CLI
curl -L https://github.com/convox/convox/releases/latest/download/convox-linux -o /tmp/convox
sudo mv /tmp/convox /usr/local/bin/convox
sudo chmod 755 /usr/local/bin/convox

# Login to Convox (get command from Console)
convox login console.convox.com -t YOUR_API_KEY

# Switch to your GPU rack
convox switch ai-production

# Create and deploy the app
convox apps create llm-api
convox deploy
```

### 4. Test Your API

```bash
# Get your app URL
convox services

# Test the API
python test_api.py https://api.llm-api.YOUR_RACK_DOMAIN.convox.cloud
```

## 🧪 API Usage

### Health Check
```bash
curl https://your-api-url/health
```

### Generate Text
```bash
curl -X POST https://your-api-url/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "The future of AI is",
    "max_new_tokens": 50,
    "temperature": 0.7
  }'
```

### Response Format
```json
{
  "prompt": "The future of AI is",
  "generated_text": "bright and full of possibilities...",
  "processing_time": 1.234,
  "device_used": "cuda",
  "cached": false,
  "tokens_generated": 45
}
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `microsoft/DialoGPT-medium` | HuggingFace model to use |
| `MAX_MEMORY_GB` | `12` | Maximum GPU memory to use |
| `PORT` | `8000` | API server port |

### Scaling Configuration

The app automatically scales from 1-5 GPU instances based on:
- **CPU utilization**: 70% target
- **Memory utilization**: 75% target
- **Request volume**: Automatic scaling

### Resource Allocation

Each instance gets:
- **1 GPU** (NVIDIA)
- **4 CPU cores** (4000 millicores)
- **16GB RAM**
- **Redis cache** (shared)

## 🔧 Customization

### Using Different Models

Change the model in `convox.yml`:

```yaml
environment:
  - MODEL_NAME=microsoft/DialoGPT-large  # Larger model
  # or
  - MODEL_NAME=EleutherAI/gpt-neo-125M   # GPT-style generation
```

Popular free models:
- `microsoft/DialoGPT-large` - More capable conversational AI
- `facebook/blenderbot-400M-distill` - Facebook's conversational model
- `EleutherAI/gpt-neo-125M` - GPT-style text generation
- `distilgpt2` - Smaller, faster GPT-2 variant

### Adjusting Resources

For larger models, update `convox.yml`:

```yaml
services:
  api:
    scale:
      count: 1-3     # Fewer instances for larger models
      cpu: 8000      # More CPU
      memory: 32768  # 32GB RAM
      gpu: 1         # Or gpu: 2 for multi-GPU models
```

### Adding Persistent Storage

For training data or model fine-tuning:

```yaml
resources:
  database:
    type: postgres
    options:
      storage: 100
  cache:
    type: redis

services:
  api:
    resources:
      - database
      - cache
    volumeOptions:
      - awsEfs:
          id: "model-storage"
          accessMode: ReadWriteMany
          mountPath: "/app/models"
```

## 📊 Monitoring

### Built-in Endpoints

- **Health**: `/health` - Model status and GPU info
- **Metrics**: `/metrics` - GPU utilization and performance
- **Root**: `/` - API information

### Convox Console

Monitor through the Convox Console:
- **Real-time logs**: Application and system logs
- **Resource usage**: CPU, memory, and GPU utilization
- **Scaling events**: Automatic scaling history
- **Health status**: Service health and uptime

### GPU Monitoring

The API provides GPU metrics:

```json
{
  "gpu_name": "Tesla T4",
  "gpu_memory_used": "8.24GB",
  "gpu_utilization": "75%"
}
```

## 💰 Cost Optimization

### Automatic Scaling
- Scales down to 1 instance during low traffic
- Scales up to 5 instances during peak usage
- Uses spot instances when configured

### Instance Types
- **g4dn.xlarge**: ~$0.526/hour (good for development)
- **g4dn.2xlarge**: ~$0.752/hour (production workloads)
- **p3.2xlarge**: ~$3.06/hour (high-performance training)

### Cost-Saving Tips
1. **Use mixed instance types**: Combine spot and on-demand
2. **Configure auto-scaling**: Let Convox scale down unused resources
3. **Enable caching**: Reduce duplicate inference costs
4. **Right-size instances**: Match GPU memory to model requirements

## 🔒 Production Considerations

### Security
- HTTPS enabled by default
- Environment variable management
- Private VPC deployment
- API authentication (add as needed)

### Reliability
- Health checks with appropriate timeouts
- Graceful shutdown handling
- Redis failover support
- Multi-AZ deployment

### Performance
- Model quantization for memory efficiency
- Response caching with Redis
- Optimized Docker images
- GPU memory management

## 🐛 Troubleshooting

### Common Issues

**GPU Not Available**
```bash
# Check if NVIDIA plugin is enabled
convox rack params | grep nvidia_device_plugin_enable
# Should show: nvidia_device_plugin_enable=true
```

**Out of Memory Errors**
- Reduce `max_new_tokens` in requests
- Use model quantization (enabled by default)
- Scale to more instances with fewer concurrent requests

**Slow Model Loading**
- Health check grace period is set to 180s
- First deployment takes longer due to model download
- Subsequent deployments use cached models

**API Timeouts**
- Request timeout is set to 600s for inference
- Adjust `timeout` in `convox.yml` if needed
- Consider using streaming responses for long generations

### Debugging Commands

```bash
# View application logs
convox logs -f

# Check resource usage
convox ps

# Monitor scaling events
convox logs --filter scaling

# Test API locally
python test_api.py http://localhost:8000
```

## 📚 Additional Resources

- [Convox Documentation](https://docs.convox.com)
- [GPU Scaling Guide](https://docs.convox.com/deployment/scaling#gpu-scaling)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `python test_api.py`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Ready to deploy your own GPU-accelerated LLM API?** 

[🚀 Start with Convox](https://console.convox.com/signup) | [📖 Read the Full Guide](https://docs.convox.com/example-apps/llm-gpu-api)