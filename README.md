# GPU-Accelerated LLM API with Convox

Deploy a production-ready Large Language Model (LLM) API with GPU auto-scaling using Convox. This example demonstrates how to build and deploy a text generation service that automatically scales GPU resources based on demand.

## 🚀 What This Example Demonstrates

- **GPU-accelerated inference** using NVIDIA CUDA
- **Auto-scaling** based on CPU/memory utilization with dedicated GPU nodes
- **Production-ready FastAPI** with comprehensive health checks and error handling
- **Redis caching** for improved performance and cost optimization
- **Zero-downtime deployments** with rolling updates
- **Intelligent workload placement** on dedicated GPU node groups
- **Cost optimization** through scale-to-zero GPU nodes and spot instances

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   LLM API        │────│     Redis       │
│   (Auto SSL)    │    │   (GPU Enabled)  │    │   (Cache)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                    ┌─────────────────────┐
                    │  Dedicated GPU      │
                    │  Node Groups        │
                    │  (Auto-scaling)     │
                    └─────────────────────┘
```

## 📋 Prerequisites

- [Convox account](https://console.convox.com/signup) (free)
- AWS account with GPU instance access (g4dn.xlarge or p3.2xlarge recommended)
- Docker (for local development - optional)
- Basic familiarity with containerized deployments

## 🎯 Model Information

This example uses **Microsoft DialoGPT-medium**, a free conversational AI model that:

- ✅ **No API keys required** - completely open source
- ✅ **Auto-downloads** during first deployment (~350MB)
- ✅ **GPU optimized** with 8-bit quantization for memory efficiency
- ✅ **Conversational responses** - great for chatbots and interactive applications
- ✅ **Production ready** with proper error handling and caching

### Alternative Models

Easily switch models by changing the `MODEL_NAME` environment variable:

- `microsoft/DialoGPT-large` - More capable, requires more GPU memory
- `microsoft/DialoGPT-small` - Smaller, faster inference
- `facebook/blenderbot-400M-distill` - Facebook's conversational AI
- `EleutherAI/gpt-neo-125M` - GPT-style text generation
- `distilgpt2` - Lightweight GPT-2 variant

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/convox-examples/llm-gpu-api.git
cd llm-gpu-api
```

### 2. Set Up Convox Account and AWS Integration

1. **Create Convox Account**: [Sign up for Convox](https://console.convox.com/signup)
2. **AWS Runtime Integration**:
   - In Convox Console → **Integrations** → Click **+** in Runtime section
   - Select **AWS** and follow prompts to create IAM role
   - This allows Convox to manage GPU infrastructure securely

### 3. Install GPU-Enabled Production Rack

```bash
# Install Convox CLI first (see section below)
convox racks install ai-production \
  --region us-east-1 \
  --type production \
  --node-type t3.medium \
  --build-node-type c5.xlarge
```

### 4. Configure GPU Node Groups

Create `gpu-nodes.json` (already included in repo):

```json
[
  {
    "id": 101,
    "type": "g4dn.xlarge",
    "capacity_type": "ON_DEMAND",
    "min_size": 0,
    "max_size": 5,
    "dedicated": true,
    "label": "gpu-inference",
    "tags": "workload=llm-inference,environment=production,cost-center=ai"
  },
  {
    "id": 102,
    "type": "g4dn.2xlarge", 
    "capacity_type": "SPOT",
    "min_size": 0,
    "max_size": 3,
    "dedicated": true,
    "label": "gpu-inference-large",
    "tags": "workload=llm-inference-large,environment=production,cost-center=ai"
  }
]
```

Apply GPU configuration to your rack:

```bash
convox rack params set \
  nvidia_device_plugin_enable=true \
  additional_node_groups_config=./gpu-nodes.json \
  -r ai-production
```

This creates:
- **Scale-to-zero GPU nodes** - Only run when needed
- **Mixed instance types** - Spot instances for cost savings
- **Dedicated scheduling** - Prevents non-GPU workloads from using expensive GPU nodes
- **Proper tagging** - For AWS cost allocation

### 5. Install Convox CLI and Deploy

**Install Convox CLI:**

```bash
# Linux (x86_64)
curl -L https://github.com/convox/convox/releases/latest/download/convox-linux -o /tmp/convox
sudo mv /tmp/convox /usr/local/bin/convox && sudo chmod 755 /usr/local/bin/convox

# macOS (Intel)
curl -L https://github.com/convox/convox/releases/latest/download/convox-macos -o /tmp/convox
sudo mv /tmp/convox /usr/local/bin/convox && sudo chmod 755 /usr/local/bin/convox

# macOS (M1/ARM64)
curl -L https://github.com/convox/convox/releases/latest/download/convox-macos-arm64 -o /tmp/convox
sudo mv /tmp/convox /usr/local/bin/convox && sudo chmod 755 /usr/local/bin/convox
```

**Login and Deploy:**

```bash
# Login (get command from Convox Console → Account)
convox login console.convox.com -t YOUR_API_KEY

# Switch to GPU rack
convox switch ai-production

# Create and deploy the app
convox apps create llm-api
convox deploy
```

The deployment process:
- Builds GPU-enabled Docker image using dedicated build nodes
- Deploys to GPU nodes with `nodeSelectorLabels: gpu-inference`
- Sets up automatic scaling based on CPU/memory targets
- Configures health checks optimized for LLM loading times

### 6. Test Your API

```bash
# Get your app URL
convox services

# Test with the provided script
python test_api.py https://api.llm-api.YOUR_RACK_DOMAIN.convox.cloud
```

## 📝 API Usage Examples

### Health Check
```bash
curl https://your-api-url/health
```

**Response:**
```json
{
  "status": "healthy",
  "model": "microsoft/DialoGPT-medium",
  "device": "cuda",
  "gpu_available": true,
  "gpu_name": "Tesla T4",
  "gpu_memory_allocated": "2.34GB",
  "gpu_memory_reserved": "2.56GB"
}
```

### Generate Text
```bash
curl -X POST https://your-api-url/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "The future of AI is",
    "max_new_tokens": 50,
    "temperature": 0.7,
    "top_p": 0.9
  }'
```

**Response:**
```json
{
  "prompt": "The future of AI is",
  "generated_text": "bright and full of possibilities. As we continue to advance machine learning and develop more sophisticated algorithms...",
  "processing_time": 1.234,
  "device_used": "cuda",
  "cached": false,
  "tokens_generated": 45
}
```

### Available Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `prompt` | string | required | 1-2000 chars | Input text to generate from |
| `max_new_tokens` | int | 100 | 1-500 | Maximum tokens to generate |
| `temperature` | float | 0.7 | 0.1-2.0 | Creativity level (higher = more creative) |
| `top_p` | float | 0.9 | 0.1-1.0 | Nucleus sampling threshold |
| `do_sample` | bool | true | - | Enable/disable sampling |
| `stream` | bool | false | - | Future: streaming responses |

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `microsoft/DialoGPT-medium` | HuggingFace model identifier |
| `MAX_MEMORY_GB` | `12` | Maximum GPU memory to use |
| `PORT` | `8000` | API server port |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU device selection |

### Scaling Configuration

The app automatically scales GPU instances based on:

```yaml
scale:
  count: 1-5        # Scale from 1 to 5 instances
  cpu: 3500         # 3.5 CPU cores per instance
  memory: 14336     # 14GB RAM per instance
  gpu: 1            # 1 GPU per instance
  targets:
    cpu: 70         # Scale up at 70% CPU
    memory: 75      # Scale up at 75% memory
```

### Resource Allocation Per Instance

- **1 NVIDIA GPU** (Tesla T4, V100, or A10G depending on instance type)
- **3.5 CPU cores** (optimized for GPU workloads)
- **14GB RAM** (sufficient for model + inference)
- **Shared Redis cache** for response caching

## 🔧 Customization

### Using Different Models

Update `convox.yml`:

```yaml
environment:
  - MODEL_NAME=microsoft/DialoGPT-large  # Larger, more capable
  - MAX_MEMORY_GB=24                     # Increase for larger models
```

**Memory Requirements by Model:**
- `DialoGPT-small`: ~4GB GPU memory
- `DialoGPT-medium`: ~8GB GPU memory  
- `DialoGPT-large`: ~16GB GPU memory
- Custom models: Check HuggingFace model card

### Advanced GPU Configuration

For larger models requiring more resources:

```yaml
services:
  api:
    scale:
      count: 1-2        # Fewer instances for resource-intensive models
      cpu: 8000         # 8 CPU cores
      memory: 32768     # 32GB RAM
      gpu: 1            # Single GPU
    nodeSelectorLabels:
      convox.io/label: gpu-inference-large  # Target larger GPU nodes
```

For multi-GPU models:

```yaml
services:
  api:
    scale:
      gpu: 2            # Request 2 GPUs per instance
      count: 1          # Typically only 1 instance for multi-GPU
      cpu: 16000        # More CPU for multi-GPU coordination
      memory: 65536     # 64GB RAM
```

### Adding Persistent Storage

For production systems requiring model storage or training data:

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

## 📊 Monitoring and Observability

### Built-in Endpoints

- **`/health`** - Comprehensive health check with GPU status
- **`/metrics`** - GPU utilization and performance metrics  
- **`/`** - API information and available endpoints

### GPU Metrics

The `/metrics` endpoint provides:

```json
{
  "model": "microsoft/DialoGPT-medium",
  "device": "cuda", 
  "gpu_memory_used": "8.24GB",
  "requests_cached": 0
}
```

### Monitoring Through Convox Console

- **Real-time logs**: `convox logs -f`
- **Resource usage**: `convox ps`
- **Scaling events**: `convox logs --filter scaling`
- **Health dashboard**: Available in Convox Console

### Kubernetes-Level Monitoring

```bash
# Get kubeconfig for direct Kubernetes access
convox rack kubeconfig > ~/.kube/convox-config
export KUBECONFIG=~/.kube/convox-config

# View pod placement on GPU nodes
kubectl get pods -n ai-production-llm-api -o wide

# Monitor GPU node utilization
kubectl get nodes -l convox.io/label=gpu-inference
```

## 💰 Cost Optimization

### Automatic Cost Management

This deployment includes several cost optimization features:

1. **Scale-to-Zero GPU Nodes**: GPU instances only run when needed
2. **Spot Instance Support**: Use `capacity_type: "SPOT"` for 60-90% savings
3. **Dedicated Node Scheduling**: Prevents expensive GPU resources from non-GPU workloads
4. **Intelligent Caching**: Reduces duplicate inference costs with Redis
5. **Right-Sized Instances**: Match GPU memory to model requirements

### Instance Cost Comparison

| Instance Type | GPU | vCPUs | RAM | Cost/Hour* | Best For |
|---------------|-----|-------|-----|------------|----------|
| g4dn.xlarge | T4 (16GB) | 4 | 16GB | ~$0.526 | Development, small models |
| g4dn.2xlarge | T4 (16GB) | 8 | 32GB | ~$0.752 | Production workloads |
| p3.2xlarge | V100 (16GB) | 8 | 61GB | ~$3.06 | High-performance inference |
| p3.8xlarge | 4x V100 | 32 | 244GB | ~$12.24 | Multi-GPU models |

*Prices vary by region and are subject to change

### Cost Monitoring

Track costs using the configured AWS tags:

```bash
# View cost allocation by workload (requires AWS CLI)
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --group-by Type=TAG,Key=workload \
  --granularity MONTHLY \
  --metrics BlendedCost
```

## 🔒 Production Considerations

### Security Features

- **HTTPS by default** with automatic SSL certificates
- **VPC isolation** with private networking
- **Environment variable encryption** for sensitive configuration
- **IAM role-based access** to AWS resources
- **Container image scanning** through Convox registry

### Reliability Features

- **Health checks** with appropriate timeouts for GPU model loading
- **Graceful shutdown** handling (90s termination grace period)
- **Redis failover** support for cache availability
- **Multi-AZ deployment** for high availability
- **Circuit breaker patterns** for external dependencies

### Performance Optimizations

- **Model quantization** (8-bit) for memory efficiency
- **Response caching** with configurable TTL
- **Optimized Docker layers** for faster deployments
- **GPU memory management** with automatic cleanup
- **Request batching** support (future enhancement)

## 🐛 Troubleshooting

### Common GPU Issues

**GPU Not Available:**
```bash
# Check if NVIDIA plugin is enabled
convox rack params | grep nvidia_device_plugin_enable
# Should show: nvidia_device_plugin_enable=true

# Verify GPU nodes exist
kubectl get nodes -l convox.io/label=gpu-inference
```

**Workloads Not Scheduling on GPU Nodes:**
```bash
# Check pod placement
kubectl get pods -n ai-production-llm-api -o wide

# Verify node labels
kubectl get nodes --show-labels | grep gpu-inference
```

**Out of Memory Errors:**
- Reduce `max_new_tokens` in API requests
- Enable more aggressive quantization
- Scale to more instances with lower concurrency
- Consider larger GPU instances (g4dn.2xlarge → p3.2xlarge)

**Slow Model Loading:**
- First deployment takes 3-5 minutes for model download
- Health check grace period is set to 180 seconds
- Subsequent deployments use cached models (~30 seconds)

### Performance Issues

**High Latency:**
- Check cache hit rate at `/metrics`
- Monitor GPU utilization
- Consider keeping minimum instances warm: `convox scale api --count=2`

**Scaling Issues:**
```bash
# Check scaling configuration
convox apps info

# Monitor scaling events
convox logs --filter "scaling\|autoscaling"

# Manual scaling if needed
convox scale api --count=3
```

**Cost Optimization:**
```bash
# Check current resource usage
convox ps

# Monitor node group scaling
kubectl get nodes -l convox.io/label=gpu-inference

# Verify spot instance usage
kubectl describe nodes | grep "instance-type\|spot"
```

## 🧪 Testing

### Automated Testing

The repository includes a comprehensive test script:

```bash
# Test all endpoints and functionality
python test_api.py https://your-api-url

# The script tests:
# - Health endpoint with GPU information
# - Text generation with various parameters
# - Caching functionality
# - Error handling
# - Performance metrics
```

### Load Testing

For production validation:

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Simple load test
ab -n 100 -c 10 -p test_request.json -T application/json \
   https://your-api-url/generate
```

Create `test_request.json`:
```json
{
  "prompt": "Load test prompt",
  "max_new_tokens": 20,
  "temperature": 0.7
}
```

## 🚀 Advanced Usage

### Multi-Model Deployment

Deploy different models for different use cases:

```yaml
services:
  api-small:
    build: .
    environment:
      - MODEL_NAME=microsoft/DialoGPT-small
    nodeSelectorLabels:
      convox.io/label: gpu-inference
  
  api-large:
    build: .
    environment:
      - MODEL_NAME=microsoft/DialoGPT-large
    nodeSelectorLabels:
      convox.io/label: gpu-inference-large
```

### Custom Model Integration

For custom or fine-tuned models:

```python
# Add to app.py
CUSTOM_MODEL_PATH = os.getenv('CUSTOM_MODEL_PATH')
if CUSTOM_MODEL_PATH:
    MODEL_NAME = CUSTOM_MODEL_PATH
    logger.info(f"Loading custom model from {CUSTOM_MODEL_PATH}")
```

### Streaming Responses (Future Enhancement)

The API includes infrastructure for streaming responses:

```python
# Placeholder for streaming implementation
if request.stream:
    # Future: implement streaming response
    pass
```

## 📚 Additional Resources

- [Convox Documentation](https://docs.convox.com)
- [Workload Placement & GPU Scaling Guide](https://docs.convox.com/configuration/workload-placement)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Test your changes with `python test_api.py`
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/convox-examples/llm-gpu-api.git
cd llm-gpu-api

# Local development (CPU-only)
pip install -r requirements.txt
python app.py

# Test locally
python test_api.py http://localhost:8000
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Ready to deploy your own GPU-accelerated LLM API?** 

[🚀 Start with Convox](https://console.convox.com/signup) | [📖 Read the Full Guide](https://docs.convox.com/example-apps/llm-gpu-api)