import argparse
import os
import random
import asyncio
import logging
from typing import Optional, Union

import torch
from diffusers import AutoPipelineForText2Image
from slixmpp import ClientXMPP
from slixmpp.xmlstream import ElementBase
from slixmpp.plugins.xep_0066 import stanza as oob_stanza
import base64

class XMPPImageBot(ClientXMPP):
    def __init__(self, jid, password, model="stabilityai/sd-turbo"):
        ClientXMPP.__init__(self, jid, password)
        
        # Initialize image generation pipeline
        self._init_image_pipeline(model)
        
        # Register XMPP event handlers
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        
        # Register required plugins for file transfer
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0066')  # Out-of-band Data
        # self.register_plugin('xep_0363')  # HTTP File Upload
        self.register_plugin('xep_0071')  # XHTML-IM

    def _init_image_pipeline(self, model_name):
        """Initialize SD-Turbo image generation pipeline"""
        self.dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.pipe = AutoPipelineForText2Image.from_pretrained(
            model_name,
            torch_dtype=self.dtype,
            safety_checker=None
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = self.pipe.to(self.device)
        print(f"Image generation pipeline initialized on {self.device}")

    async def session_start(self, event):
        """Handle XMPP session start"""
        self.send_presence()
        await self.get_roster()
        print("XMPP session started successfully")

    def message(self, msg):
        """Handle incoming XMPP messages"""
        if msg['type'] in ('chat', 'normal') and msg['body'].strip():
            prompt = msg['body'].strip()
            print(f"Received prompt from {msg['from']}: {prompt}")
            
            # Run image generation in separate thread to avoid blocking XMPP
            asyncio.create_task(self._generate_and_reply(msg, prompt))

    async def _generate_and_reply(self, msg, prompt):
        """Generate image and reply to sender"""
        try:
            # Generate random seed
            seed = random.randint(0, 10**8)
            
            # Generate image
            with torch.no_grad():
                image = self.pipe(
                    prompt=prompt,
                    num_inference_steps=1,
                    width=512,
                    height=512,
                    guidance_scale=0.0,
                    generator=torch.Generator(device=self.device).manual_seed(seed)
                ).images[0]
            
            # Save image temporarily
            temp_filename = f"temp_{seed}.jpg"
            temp_path = os.path.join("./temp", temp_filename)
            os.makedirs("./temp", exist_ok=True)
            image.save(temp_path)
            print(f"Generated image saved to: {temp_path}")
            self._send_image_via_oob(msg, temp_path, prompt, seed)
                
        except Exception as e:
            error_msg = f"Failed to generate image: {str(e)}"
            print(error_msg)
            self.send_message(mto=msg['from'], mbody=error_msg, mtype='chat')
        finally:
            # Clean up temporary file
            # if 'temp_path' in locals() and os.path.exists(temp_path):
            #     os.remove(temp_path)
            
            # Clear memory cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def _send_image_via_oob(self, msg, file_path, prompt, seed):
        """Send image via Out-of-Band Data (slixmpp compatible way)"""
        # body = (
        #     f"Image generated for prompt: {prompt}\n"
        #     f"Seed: {seed}\n"
        #     "Image attached below:"
        # )
        
        # # Create message with OOB attachment using slixmpp's native API
        # reply = self.make_message(mto=msg['from'], mbody=body, mtype='chat')
        
        # # Create OOB element using slixmpp's stanza API (recommended method)
        # oob = oob_stanza.OOB()
        # oob['url'] = f"file://{os.path.abspath(file_path)}"
        
        # # Attach OOB element to message
        # reply.append(oob)
        
        # # Send message
        # reply.send()
        # print(f"OOB message sent with file: {file_path}")
        
        with open(file_path, 'rb') as image_file:
            image_data = image_file.read()
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            
        filename = os.path.basename(file_path)
        mime_type = self.get_mime_type(filename)
        
        xhtml_content = (
            f"<html xmlns='http://www.w3.org/1999/xhtml'>"
            f"<body>"
            f"<p>Image generated for prompt: {prompt}</p>"
            f"<p>Seed: {seed}</p>"
            f"<img src='data:{mime_type};base64,{encoded_image}' alt='' style='max-width:300px;'/>"
            f"</body>"
            f"</html>"
        )

        try:
            reply = self.make_message(
                mto=msg['from'],
                mbody=f"sent: {filename}",
                mtype='chat'
            )
            
            # add XEP-0066 Out of Band Data
            oob = reply['oob']
            oob['url'] = f"cid:{filename}"  # use Content-ID URL
            oob['desc'] = f"file: {filename}"
            
            # add XHTML-IM
            reply['html']['body'] = xhtml_content
            
            # send
            reply.send()
            print(f"sent ok: {filename}")
        except Exception as e:
            print(f"fail : {str(e)}")
        
    def get_mime_type(self, filename):
        extension = filename.lower().split('.')[-1]
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'webp': 'image/webp'
        }
        return mime_types.get(extension, 'image/jpeg')

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="XMPP Image Generation Bot")
    parser.add_argument('--jid', required=True, help="XMPP JID (e.g., user@server.com)")
    parser.add_argument('--password', required=True, help="XMPP password")
    parser.add_argument(
        '--model', 
        default="stabilityai/sd-turbo", 
        help="Stable Diffusion model to use (default: stabilityai/sd-turbo)"
    )
    parser.add_argument(
        '--max-file-size', 
        type=int, 
        default=5, 
        help="Maximum allowed file size in MB (default: 5)"
    )
    
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)-8s %(message)s'
    )

    # Initialize and run XMPP bot
    xmpp = XMPPImageBot(args.jid, args.password, args.model)
    
    # Connect to XMPP server and run event loop (slixmpp compatible way)
    if xmpp.connect():
        try:
            # Run event loop with asyncio
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            xmpp.disconnect()
            print("XMPP bot stopped by user")
    else:
        print("Could not connect to XMPP server")

if __name__ == "__main__":
    main()