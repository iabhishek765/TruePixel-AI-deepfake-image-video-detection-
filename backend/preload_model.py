import sys
print("Preloading Deepfake Detection Model...")
try:
    from transformers import AutoImageProcessor, AutoModelForImageClassification
    model_name = "umm-maybe/AI-image-detector"
    print(f"Downloading processor for {model_name}...")
    AutoImageProcessor.from_pretrained(model_name)
    print(f"Downloading model for {model_name}...")
    AutoModelForImageClassification.from_pretrained(model_name)
    print("Model preloaded successfully!")
    sys.exit(0)
except Exception as e:
    print(f"Error preloading model: {e}")
    sys.exit(1)
