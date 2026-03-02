import argparse  # For parsing command-line arguments
from diffusers import AutoPipelineForText2Image
import torch

def main(image_filename: str, prompt: str = "A cat in cup."):
    # Load the SD-Turbo model
    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sd-turbo",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )
    pipe.to("cpu")  # Force CPU execution (change to "cuda" if you have an NVIDIA GPU)

    # Generate image (SD-Turbo only needs 1 inference step)
    image = pipe(
        prompt=prompt,
        num_inference_steps=1,
        guidance_scale=0.0,  # SD-Turbo doesn't require guidance scale
        width=256,
        height=256
    ).images[0]

    # Save image to specified path
    image.save(f"./output/{image_filename}")
    print(f"Image successfully saved to: {image_filename}")

if __name__ == "__main__":
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Generate images using SD-Turbo")
    parser.add_argument(
        "--output", 
        type=str, 
        required=True,  # Mandatory parameter: output filename
        help="Output image filename (e.g.: output.jpg)"
    )
    parser.add_argument(
        "--prompt", 
        type=str, 
        default="A cat in cup.",  # Optional parameter: default prompt
        help="Text prompt for image generation"
    )
    
    # Parse command-line arguments
    args = parser.parse_args()
    
    # Execute main function
    main(image_filename=args.output, prompt=args.prompt)
