import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel
from PIL import Image, ImageTk
import json
import numpy as np
import cv2

def process_segmentation(json_input):
    with open(json_input, 'r') as file:
        data = json.load(file)
    
    areas = {}
    
    for i, annotation in enumerate(data['annotations'], 1):
        segmentation = annotation['segmentation'][0]
        pairs = [[segmentation[j], segmentation[j+1]] for j in range(0, len(segmentation), 2)]
        np_array = np.array(pairs, dtype=np.float32)
        np_array = np.round(np_array).astype(np.int32)
        areas[f'area{i}'] = np_array
    
    return areas

def format_results(areas):
    result = ""
    for area, np_array in areas.items():
        result += f"{area} = np.array({np_array.tolist()}, dtype=np.int32)\n\n"
    return result

def draw_polyzones(img, areas):
    overlay = img.copy()
    
    colors = [
        (0, 100, 200),  # reddish
        (200, 100, 0),  # bluish
        (100, 200, 0),  # greenish
        (200, 0, 100),  # purplish
        (0, 200, 100),  # tealish
    ]
    
    for i, (area_name, points) in enumerate(areas.items()):
        pts = points.reshape((-1, 1, 2))
        color = colors[i % len(colors)]
        
        # Draw filled polygon
        cv2.fillPoly(overlay, [pts], color)
        
        # Draw outline
        cv2.polylines(img, [pts], True, (0, 0, 0), 2)
    
    # Blend the overlay with the original image
    alpha = 0.4
    img_with_polyzones = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
    
    return img_with_polyzones

def generate_boilerplate(areas):
    boilerplate = """
import cv2
import numpy as np

# Define the polyzone coordinates
"""
    for area_name, points in areas.items():
        boilerplate += f"{area_name} = np.array({points.tolist()}, dtype=np.int32)\n"
    
    boilerplate += """
def draw_polyzones(image_path, output_path):
    img = cv2.imread(image_path)
    
    if img is None:
        print(f"Error: Could not read image at {image_path}")
        return
    
    overlay = img.copy()
    
    colors = [
        (0, 100, 200),  # reddish
        (200, 100, 0),  # bluish
        (100, 200, 0),  # greenish
        (200, 0, 100),  # purplish
        (0, 200, 100),  # tealish
    ]
    
    areas = ["""
    
    for area_name in areas.keys():
        boilerplate += f"{area_name}, "
    boilerplate = boilerplate.rstrip(", ")
    boilerplate += "]\n"
    
    boilerplate += """
    for i, pts in enumerate(areas):
        color = colors[i % len(colors)]
        cv2.fillPoly(overlay, [pts], color)
        cv2.polylines(img, [pts], True, (0, 0, 0), 2)
    
    alpha = 0.4
    img_with_polyzones = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
    
    cv2.imwrite(output_path, img_with_polyzones)
    print(f"Image saved as {output_path}")

# Example usage
if __name__ == "__main__":
    input_image_path = "input_image.jpg"  # Replace with your image path
    output_image_path = "output_image.jpg"  # Replace with desired output path
    draw_polyzones(input_image_path, output_image_path)
"""
    return boilerplate

def show_image(img):
    # Convert the image from BGR to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Convert the image to PIL Image
    pil_img = Image.fromarray(img_rgb)
    
    # Create a new window
    image_window = Toplevel(root)
    image_window.title("Processed Image")
    
    # Resize the image to fit in the window if it's too large
    max_size = (800, 600)
    pil_img.thumbnail(max_size, Image.LANCZOS)
    
    # Convert PIL image to PhotoImage
    tk_img = ImageTk.PhotoImage(pil_img)
    
    # Create a label and display the image
    label = tk.Label(image_window, image=tk_img)
    label.image = tk_img  # Keep a reference to prevent garbage collection
    label.pack()

    # Add a save button to the image window
    save_button = tk.Button(image_window, text="Save Image", command=lambda: save_image(img))
    save_button.pack(pady=10)

def save_image(img):
    output_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg")])
    if output_path:
        cv2.imwrite(output_path, img)
        messagebox.showinfo("Success", f"Image saved as {output_path}")

def upload_and_process():
    json_file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if json_file_path:
        try:
            areas = process_segmentation(json_file_path)
            formatted_result = format_results(areas)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, formatted_result)
            
            # Generate and display boilerplate code
            boilerplate_code = generate_boilerplate(areas)
            boilerplate_text.delete(1.0, tk.END)
            boilerplate_text.insert(tk.END, boilerplate_code)
            
            # Prompt for image selection and processing
            image_file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")])
            if image_file_path:
                img = cv2.imread(image_file_path)
                if img is None:
                    messagebox.showerror("Error", f"Could not read image at {image_file_path}")
                    return
                processed_image = draw_polyzones(img, areas)
                show_image(processed_image)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Create the main window
root = tk.Tk()
root.title("JSON Segmentation Processor and Visualizer")
root.geometry("800x600")

# Create and pack the upload button
upload_button = tk.Button(root, text="Upload and Process JSON", command=upload_and_process)
upload_button.pack(pady=10)

# Create and pack the result text area
result_text = tk.Text(root, height=10, width=80)
result_text.pack(pady=10)

# Create and pack the boilerplate code text area
boilerplate_text = tk.Text(root, height=20, width=80)
boilerplate_text.pack(pady=10)

# Start the GUI event loop
root.mainloop()