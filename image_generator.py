import argparse
import os
import random
from diffusers import AutoPipelineForText2Image
import torch
from typing import Optional, Union

def main(
    image_filename: str, 
    prompt: str = "A cat in cup.",
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    cfg_scale: float = 0.0,
    num_inference_steps: int = 1,
    seed: Union[int, None] = None
) -> None:
    # Security check: Prevent path traversal attacks
    if os.path.isabs(image_filename) or ".." in image_filename:
        raise ValueError("Output filename cannot contain absolute path or parent directory references (../)")
    
    # Resolution validation: Must be multiple of 64 and within valid range
    if width % 64 != 0 or height % 64 != 0:
        raise ValueError(f"Resolution must be multiple of 64. Current input: {width}x{height}")
    if width < 256 or width > 1024 or height < 256 or height > 1024:
        raise ValueError(f"Resolution must be between 256x256 and 1024x1024")
    
    # CFG Scale validation: Must be within reasonable range
    if cfg_scale < 0.0 or cfg_scale > 10.0:
        raise ValueError(f"CFG Scale must be between 0.0 and 10.0. Current input: {cfg_scale}")
    
    # Create output directory if it doesn't exist
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, image_filename)

    # Set random seed for reproducibility
    if seed is not None:
        torch.manual_seed(seed)
        random.seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    else:
        seed = random.randint(0, 10**8)  # Generate random seed if not provided

    # Load SD-Turbo model with optimal device and dtype
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sd-turbo",
        torch_dtype=dtype,
        safety_checker=None
    )
    
    # Auto-select best device (GPU preferred)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipe = pipe.to(device)

    try:
        # Generate image without progress tracking
        with torch.no_grad():  # Disable gradient calculation to save memory
            image = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                width=width,
                height=height,
                guidance_scale=cfg_scale,
                generator=torch.Generator(device=device).manual_seed(seed)
                # Removed callback parameter entirely
            ).images[0]

        # Save image to disk
        image.save(output_path)
        print(f"\nImage successfully saved to: {output_path}")
        print(f"Generation parameters: Resolution={width}x{height}, CFG Scale={cfg_scale}, Steps={num_inference_steps}, Seed={seed}")
    finally:
        # Force memory cleanup to prevent leaks
        del pipe
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate images using SD-Turbo with advanced parameter control")
    parser.add_argument(
        "--output", 
        type=str, 
        required=True,
        help="Output image filename (e.g.: output.jpg)"
    )
    parser.add_argument(
        "--prompt", 
        type=str, 
        default="A cat in cup.",
        help="Text prompt for image generation"
    )
    parser.add_argument(
        "--negative-prompt", 
        type=str, 
        default="",
        help="Negative prompt to exclude unwanted elements (e.g.: blurry, low quality)"
    )
    parser.add_argument(
        "--width", 
        type=int, 
        default=512,
        help="Image width (must be multiple of 64, range: 256-1024)"
    )
    parser.add_argument(
        "--height", 
        type=int, 
        default=512,
        help="Image height (must be multiple of 64, range: 256-1024)"
    )
    parser.add_argument(
        "--cfg-scale", 
        type=float, 
        default=0.0,
        help="CFG Scale parameter (0.0-10.0, 0.0 = most creative, 3.0 = most prompt-faithful)"
    )
    parser.add_argument(
        "--steps", 
        type=int, 
        default=1,
        help="Number of inference steps (1-5 recommended for SD-Turbo)"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=None,
        help="Random seed for reproducible results (0-10^8, leave blank for random seed)"
    )
    
    args = parser.parse_args()
    main(
        image_filename=args.output, 
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        width=args.width,
        height=args.height,
        cfg_scale=args.cfg_scale,
        num_inference_steps=args.steps,
        seed=args.seed
    )