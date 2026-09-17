from importlib.metadata import version
import torch #type:ignore
import pandas as pd
import sklearn

def main():
    print("=== Environment Sanity Check ===")
    print(f"PyTorch Version: {torch.__version__}")
    print(f"Pandas Version:  {version('pandas')}")
    print(f"Scikit-Learn Version: {version('scikit-learn')}")
    print(f"CUDA Available:  {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Device Name: {torch.cuda.get_device_name(0)}")

if __name__ == "__main__":
    main()

