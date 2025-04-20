import requests
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import io
import base64
import json
import os
from PIL import Image, ImageTk
import configparser
import threading

class TryOnDiffusionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Try-On Diffusion Client")
        self.root.geometry("1000x800")
        
        # Application variables
        self.person_image_path = None
        self.garment_image_path = None
        self.result_image = None
        self.api_url = tk.StringVar(value="https://try-on-diffusion.p.rapidapi.com/try-on-url")
        self.api_key = tk.StringVar(value="3524bd5ff5mshc7b0a63e4d67405p1c12a4jsn8c7dc8273722")
        self.config_file = "tryon_config.ini"
        
        # Load configuration if exists
        self.load_config()
        
        # Create the user interface
        self.create_ui()
        
    def load_config(self):
        """Load configuration from file if exists"""
        config = configparser.ConfigParser()
        
        if os.path.exists(self.config_file):
            try:
                config.read(self.config_file)
                if 'API' in config:
                    if 'key' in config['API']:
                        self.api_key.set(config['API']['key'])
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save current configuration to file"""
        config = configparser.ConfigParser()
        config['API'] = {
            'key': self.api_key.get()
        }
        
        try:
            with open(self.config_file, 'w') as f:
                config.write(f)
            self.log_message("Configuration saved successfully")
            messagebox.showinfo("Success", "API key saved successfully")
        except Exception as e:
            self.log_message(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def create_ui(self):
        """Create the application UI"""
        # Main container with tabs
        tab_control = ttk.Notebook(self.root)
        
        # Tab 1: Main try-on interface
        main_tab = ttk.Frame(tab_control)
        tab_control.add(main_tab, text="Try-On")
        
        # Tab 2: Settings
        settings_tab = ttk.Frame(tab_control)
        tab_control.add(settings_tab, text="Settings")
        
        # Tab 3: Logs
        logs_tab = ttk.Frame(tab_control)
        tab_control.add(logs_tab, text="Logs")
        
        tab_control.pack(expand=1, fill="both")
        
        # ---- Configure Main Tab ----
        self.setup_main_tab(main_tab)
        
        # ---- Configure Settings Tab ----
        self.setup_settings_tab(settings_tab)
        
        # ---- Configure Logs Tab ----
        self.setup_logs_tab(logs_tab)
    
    def setup_main_tab(self, parent):
        """Set up the main try-on interface tab"""
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input section for images
        input_frame = ttk.LabelFrame(main_frame, text="Input Images", padding="10")
        input_frame.pack(fill=tk.X, pady=10)
        
        # Person image selection
        person_frame = ttk.Frame(input_frame)
        person_frame.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        
        ttk.Label(person_frame, text="Person Image:").pack(anchor=tk.W)
        self.person_preview = ttk.Label(person_frame, text="No image selected")
        self.person_preview.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Button(person_frame, text="Select Person Image", command=self.select_person_image).pack(fill=tk.X)
        
        # Garment image selection
        garment_frame = ttk.Frame(input_frame)
        garment_frame.pack(side=tk.RIGHT, padx=10, fill=tk.BOTH, expand=True)
        
        ttk.Label(garment_frame, text="Garment Image:").pack(anchor=tk.W)
        self.garment_preview = ttk.Label(garment_frame, text="No image selected")
        self.garment_preview.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Button(garment_frame, text="Select Garment Image", command=self.select_garment_image).pack(fill=tk.X)
        
        # Process controls
        process_frame = ttk.Frame(main_frame)
        process_frame.pack(fill=tk.X, pady=10)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(process_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        self.process_button = ttk.Button(
            process_frame, 
            text="Generate Try-On", 
            command=self.process_images
        )
        self.process_button.pack(side=tk.RIGHT)
        self.process_button["state"] = "disabled"
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Results section
        result_frame = ttk.LabelFrame(main_frame, text="Result", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.result_preview = ttk.Label(result_frame, text="No result yet")
        self.result_preview.pack(fill=tk.BOTH, expand=True)
        
        # Save button (initially disabled)
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        self.save_button = ttk.Button(buttons_frame, text="Save Result", command=self.save_result)
        self.save_button.pack(side=tk.RIGHT, padx=5)
        self.save_button["state"] = "disabled"
        
        ttk.Button(buttons_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
    
    def setup_settings_tab(self, parent):
        """Set up the settings tab"""
        settings_frame = ttk.Frame(parent, padding="20")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # API Configuration
        api_frame = ttk.LabelFrame(settings_frame, text="RapidAPI Configuration", padding="10")
        api_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(api_frame, text="RapidAPI Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(api_frame, textvariable=self.api_key, width=50, show="*").grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(api_frame, text="Save API Key", command=self.save_config).grid(row=1, column=1, sticky=tk.E, pady=10)
        
        # API Information
        info_frame = ttk.LabelFrame(settings_frame, text="API Information", padding="10")
        info_frame.pack(fill=tk.X, pady=10)
        
        info_text = """
Try-On Diffusion API Information:
- API Provider: RapidAPI
- API: Try-On Diffusion API
- Endpoint: https://try-on-diffusion.p.rapidapi.com/api/v1/tryon
- Purpose: Virtual try-on of garments on person images
- Format: Sends base64-encoded images and receives try-on result

To use this application:
1. Enter your RapidAPI key above
2. Select person and garment images
3. Click "Generate Try-On" to create the virtual try-on result
        """
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, wraplength=550)
        info_label.pack(fill=tk.X, pady=5)
        
        # Test Connection
        ttk.Button(settings_frame, text="Test API Connection", command=self.test_connection).pack(pady=10)
    
    def setup_logs_tab(self, parent):
        """Set up the logs tab"""
        logs_frame = ttk.Frame(parent, padding="10")
        logs_frame.pack(fill=tk.BOTH, expand=True)
        
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=20)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        buttons_frame = ttk.Frame(logs_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(buttons_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.RIGHT)
        ttk.Button(buttons_frame, text="Export Logs", command=self.export_logs).pack(side=tk.RIGHT, padx=5)
    
    def log_message(self, message):
        """Add a message to the logs"""
        self.logs_text.insert(tk.END, f"{message}\n")
        self.logs_text.see(tk.END)  # Scroll to the end
        print(message)  # Also print to console
    
    def clear_logs(self):
        """Clear the logs text area"""
        self.logs_text.delete(1.0, tk.END)
    
    def export_logs(self):
        """Export logs to a file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Logs",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(self.logs_text.get(1.0, tk.END))
                self.log_message(f"Logs exported to {file_path}")
            except Exception as e:
                self.log_message(f"Error exporting logs: {e}")
    
    def select_person_image(self):
        """Select person image from file system"""
        file_path = filedialog.askopenfilename(
            title="Select Person Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            self.person_image_path = file_path
            self.display_preview(file_path, self.person_preview)
            self.check_process_button()
            self.log_message(f"Person image selected: {file_path}")
    
    def select_garment_image(self):
        """Select garment image from file system"""
        file_path = filedialog.askopenfilename(
            title="Select Garment Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            self.garment_image_path = file_path
            self.display_preview(file_path, self.garment_preview)
            self.check_process_button()
            self.log_message(f"Garment image selected: {file_path}")
    
    def display_preview(self, image_path, label_widget):
        """Display image preview in a label widget"""
        try:
            img = Image.open(image_path)
            img.thumbnail((200, 200))  # Resize for preview
            photo = ImageTk.PhotoImage(img)
            label_widget.config(image=photo)
            label_widget.image = photo  # Keep a reference
        except Exception as e:
            self.log_message(f"Error displaying preview: {e}")
            label_widget.config(text="Error loading image")
    
    def check_process_button(self):
        """Enable process button if both images are selected"""
        if self.person_image_path and self.garment_image_path:
            self.process_button["state"] = "normal"
        else:
            self.process_button["state"] = "disabled"
    
    def process_images(self):
        """Start the try-on process"""
        if not self.api_key.get():
            messagebox.showerror("API Key Required", "Please enter your RapidAPI key in the Settings tab")
            return
            
        self.status_var.set("Processing...")
        self.progress.start()
        self.process_button["state"] = "disabled"
        self.save_button["state"] = "disabled"
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=self.call_api, daemon=True).start()
    
    def clear_all(self):
        """Clear all selections and results"""
        self.person_image_path = None
        self.garment_image_path = None
        self.result_image = None
        
        self.person_preview.config(image="", text="No image selected")
        self.garment_preview.config(image="", text="No image selected")
        self.result_preview.config(image="", text="No result yet")
        
        self.status_var.set("Ready")
        self.process_button["state"] = "disabled"
        self.save_button["state"] = "disabled"
        
        self.log_message("All selections cleared")
    
    def encode_image_to_base64(self, image_path):
        """Encode image file to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return encoded_string
        except Exception as e:
            self.log_message(f"Error encoding image: {e}")
            return None
    
    def call_api(self):
        """Make the API call to the Try-On Diffusion service"""
        try:
            # Encode images to base64
            self.log_message("Encoding person image to base64...")
            person_base64 = self.encode_image_to_base64(self.person_image_path)
            
            self.log_message("Encoding garment image to base64...")
            garment_base64 = self.encode_image_to_base64(self.garment_image_path)
            
            if not person_base64 or not garment_base64:
                self.log_message("Failed to encode images")
                self.status_var.set("Error encoding images")
                return
            
            # Prepare headers for RapidAPI
            headers = {
                "Content-Type": "application/json",
                "X-RapidAPI-Key": self.api_key.get(),
                "X-RapidAPI-Host": "try-on-diffusion.p.rapidapi.com"
            }
            
            # Prepare data payload
            data = {
                "person_image": person_base64,
                "garment_image": garment_base64
            }
            
            # Make API call
            self.log_message("Sending request to Try-On Diffusion API...")
            response = requests.post(self.api_url.get(), json=data, headers=headers)
            
            # Process response
            status_code = response.status_code
            self.log_message(f"Response status code: {status_code}")
            
            if status_code == 200:
                # Log response details for debugging
                content_type = response.headers.get('Content-Type', 'unknown')
                self.log_message(f"Response content type: {content_type}")
                
                # Try to parse as JSON first
                try:
                    result = response.json()
                    self.log_message("Successfully parsed JSON response")
                    
                    # Extract result image from standard format
                    if "result" in result and "image" in result["result"]:
                        # Get base64 image data
                        result_base64 = result["result"]["image"]
                        
                        # Convert base64 to image
                        image_data = base64.b64decode(result_base64)
                        self.result_image = Image.open(io.BytesIO(image_data))
                        
                        # Display result
                        self.display_result()
                        self.status_var.set("Try-on generated successfully!")
                        self.save_button["state"] = "normal"
                    else:
                        # Try to find any base64 image in the JSON response
                        self.log_message("Standard result format not found, searching for image data in response")
                        self.extract_image_from_json(result)
                
                except json.JSONDecodeError:
                    self.log_message("Response is not valid JSON, trying to process as direct image data")
                    
                    # Try to interpret response as direct image data (binary or base64)
                    self.extract_image_from_raw_response(response)
                    
            else:
                # Handle error responses
                self.log_message(f"API Error: {status_code}")
                try:
                    error_data = response.json()
                    self.log_message(f"Error details: {json.dumps(error_data, indent=2)}")
                    self.status_var.set(f"Error {status_code}: {error_data.get('message', 'Unknown error')}")
                except:
                    self.log_message(f"Error response: {response.text[:100]}...")
                    self.status_var.set(f"Error {status_code}")
                
        except Exception as e:
            self.log_message(f"Error during API call: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
        
        finally:
            self.progress.stop()
            self.process_button["state"] = "normal"
    
    def extract_image_from_json(self, json_data):
        """Try to find and extract image data from JSON response"""
        found_image = False
        
        # Recursively search through nested dictionaries
        def search_for_base64(obj, path=""):
            nonlocal found_image
            if found_image:
                return
                
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if isinstance(value, (dict, list)):
                        search_for_base64(value, new_path)
                    elif isinstance(value, str) and len(value) > 100:
                        if self.try_decode_as_image(value, f"JSON path: {new_path}"):
                            found_image = True
                            return
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]"
                    if isinstance(item, (dict, list)):
                        search_for_base64(item, new_path)
                    elif isinstance(item, str) and len(item) > 100:
                        if self.try_decode_as_image(item, f"JSON path: {new_path}"):
                            found_image = True
                            return
        
        # Start recursive search
        search_for_base64(json_data)
        
        if not found_image:
            self.log_message("Could not extract any image from JSON response")
            self.status_var.set("Error: Could not extract result image")
    
    def extract_image_from_raw_response(self, response):
        """Try to interpret the raw response as image data"""
        
        # First try as direct binary image
        try:
            image_data = response.content
            self.result_image = Image.open(io.BytesIO(image_data))
            self.display_result()
            self.status_var.set("Image extracted directly from response")
            self.save_button["state"] = "normal"
            self.log_message("Successfully interpreted response as binary image data")
            return True
        except Exception as e:
            self.log_message(f"Not a direct binary image: {e}")
        
        # Try as base64 encoded image
        try:
            # Some APIs return raw base64 without JSON wrapping
            image_data = base64.b64decode(response.text)
            self.result_image = Image.open(io.BytesIO(image_data))
            self.display_result()
            self.status_var.set("Base64 image extracted from response")
            self.save_button["state"] = "normal"
            self.log_message("Successfully interpreted response as base64 string")
            return True
        except Exception as e:
            self.log_message(f"Not a valid base64 image: {e}")
        
        # If both attempts failed
        self.status_var.set("Error: Could not interpret response")
        return False
    
    def try_decode_as_image(self, base64_str, source_info=""):
        """Try to decode a string as base64 image"""
        try:
            # Try to decode - skip common prefixes if present
            if "," in base64_str:
                # Handle data URIs like "data:image/jpeg;base64,/9j/4AAQ..."
                base64_str = base64_str.split(",", 1)[1]
                
            image_data = base64.b64decode(base64_str)
            self.result_image = Image.open(io.BytesIO(image_data))
            self.display_result()
            self.status_var.set("Try-on generated successfully!")
            self.save_button["state"] = "normal"
            self.log_message(f"Successfully extracted image from {source_info}")
            return True
        except Exception as e:
            self.log_message(f"Failed to decode potential image data from {source_info}: {e}")
            return False
    
    def display_result(self):
        """Display the result image"""
        if self.result_image:
            img_copy = self.result_image.copy()
            img_copy.thumbnail((500, 500))  # Resize for display
            photo = ImageTk.PhotoImage(img_copy)
            self.result_preview.config(image=photo)
            self.result_preview.image = photo  # Keep a reference
    
    def save_result(self):
        """Save the result image to file"""
        if self.result_image:
            save_path = filedialog.asksaveasfilename(
                title="Save Result Image",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")]
            )
            if save_path:
                try:
                    self.result_image.save(save_path)
                    self.status_var.set(f"Image saved to {save_path}")
                    self.log_message(f"Result saved to: {save_path}")
                except Exception as e:
                    self.log_message(f"Error saving image: {e}")
    
    def test_connection(self):
        """Test the API connection"""
        if not self.api_key.get():
            messagebox.showerror("API Key Required", "Please enter your RapidAPI key first")
            return
            
        self.log_message("Testing connection to Try-On Diffusion API...")
        
        headers = {
            "X-RapidAPI-Key": self.api_key.get(),
            "X-RapidAPI-Host": "try-on-diffusion.p.rapidapi.com"
        }
        
        try:
            # Just a simple GET request to test authentication
            response = requests.get(
                "https://try-on-diffusion.p.rapidapi.com/api/v1/health", 
                headers=headers,
                timeout=10
            )
            
            status_code = response.status_code
            self.log_message(f"Connection test result: {status_code}")
            
            if status_code < 400:
                messagebox.showinfo("Connection Test", "Connection successful! Your API key is valid.")
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', 'Unknown error')
                    messagebox.showerror("Connection Test", f"Connection failed: {error_message}")
                except:
                    messagebox.showerror("Connection Test", f"Connection failed with status code: {status_code}")
        
        except requests.exceptions.RequestException as e:
            self.log_message(f"Connection test failed: {e}")
            messagebox.showerror("Connection Test", f"Connection failed: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TryOnDiffusionApp(root)
    root.mainloop()