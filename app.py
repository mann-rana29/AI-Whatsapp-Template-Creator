import gradio as gr
import json
import os
from dotenv import load_dotenv
from services.llm_service import generate_response
from services.validator import validate_template

load_dotenv()

def process_message(user_input, chat_history, template_state):
    result = generate_response(user_input, chat_history, template_state)
    
    ai_msg = result.get("ai_message", "")
    new_template = result.get("template", template_state)
    
    chat_history.append({"role": "user", "content": user_input})
    chat_history.append({"role": "assistant", "content": ai_msg})
    
    preview_html = generate_preview_html(new_template)
    
    name = new_template.get("name", "")
    category = new_template.get("category", "")
    language = new_template.get("language", "")
    
    return "", chat_history, new_template, preview_html, name, category, language

def generate_preview_html(template):
    if not template or not template.get("components"):
        return "<div style='padding:20px; font-family:sans-serif; color: black;'>Preview not available.</div>"
        
    components = template.get("components", [])
    
    html = "<div style='width: 320px; background-color: #efeae2; color: black; border-radius: 10px; padding: 15px; font-family: sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.1);'>"
    html += "<div style='background-color: white; color: black; padding: 12px; border-radius: 8px; margin-bottom: 10px; border-top-left-radius: 0; box-shadow: 0 1px 1px rgba(0,0,0,0.1);'>"
    
    for comp in components:
        comp_type = comp.get("type", "")
        if comp_type == "HEADER":
            if comp.get("format") == "TEXT":
                html += f"<strong style='display:block; margin-bottom:8px; font-size:16px;'>{comp.get('text','')}</strong>"
            else:
                fmt = comp.get('format', 'MEDIA')
                html += f"<div style='background-color: #ddd; height: 120px; border-radius: 6px; margin-bottom: 8px; display:flex; align-items:center; justify-content:center; color:#666; font-weight:bold;'>{fmt} HEADER</div>"
        elif comp_type == "BODY":
            text = comp.get("text", "").replace('\n', '<br>')
            html += f"<div style='font-size:15px; margin-bottom:8px; line-height: 1.4;'>{text}</div>"
        elif comp_type == "FOOTER":
            html += f"<div style='font-size:13px; color: #888;'>{comp.get('text', '')}</div>"
            
    html += "</div>"
    
    buttons_comp = next((c for c in components if c.get("type") == "BUTTONS"), None)
    if buttons_comp:
        for btn in buttons_comp.get("buttons", []):
            html += f"<div style='background-color: white; text-align: center; color: #00a884; padding: 10px; border-radius: 8px; margin-top: 6px; cursor: pointer; font-weight: bold; box-shadow: 0 1px 1px rgba(0,0,0,0.1); font-size:15px;'>{btn.get('text', '')}</div>"
            
    carousel_comp = next((c for c in components if c.get("type") == "CAROUSEL"), None)
    if carousel_comp:
        html += "<div style='display:flex; overflow-x:auto; padding-bottom:5px; gap: 10px;'>"
        for card in carousel_comp.get("cards", []):
            html += "<div style='min-width: 200px; background-color: white; padding: 10px; border-radius: 8px; box-shadow: 0 1px 1px rgba(0,0,0,0.1);'>"
            for c_comp in card.get("components", []):
                if c_comp.get("type") == "HEADER":
                    html += f"<div style='background-color: #ddd; height: 80px; border-radius: 4px; margin-bottom: 5px; display:flex; align-items:center; justify-content:center; font-size:10px;'>{c_comp.get('format')}</div>"
                elif c_comp.get("type") == "BODY":
                    html += f"<div style='font-size:13px; margin-bottom:5px;'>{c_comp.get('text','')}</div>"
                elif c_comp.get("type") == "BUTTONS":
                    for c_btn in c_comp.get("buttons", []):
                        html += f"<div style='background-color: #f0f0f0; text-align: center; color: #00a884; padding: 5px; border-radius: 4px; font-size: 12px;'>{c_btn.get('text', '')}</div>"
            html += "</div>"
        html += "</div>"
            
    html += "</div>"
    return html

def submit_and_save(template_state):
    errors = validate_template(template_state)
    if errors:
        return f"Validation Errors:\n" + "\n".join(errors)
    else:
        os.makedirs("output", exist_ok=True)
        name = template_state.get("name", "template")
        lang = template_state.get("language", "en")
        filepath = f"output/{name}_{lang}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(template_state, f, indent=2)
        return f"Success! Saved to {filepath}"

with gr.Blocks(title="WhatsApp Template Creator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# WhatsApp Template Creator")
    
    template_state = gr.State(value={})
    
    with gr.Row():
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(label="Chat", height=600)
            user_input = gr.Textbox(label="Prompt", placeholder="Type here...")
            
        with gr.Column(scale=1):
            with gr.Tab("Preview"):
                preview_html = gr.HTML(value="<div style='background-color:#E1F5FE; color: black; padding:20px; border-radius:10px; font-family:sans-serif;'>Preview area</div>")
                
            with gr.Tab("Data"):
                name_input = gr.Textbox(label="Template Name", interactive=False)
                category_input = gr.Textbox(label="Category", interactive=False)
                language_input = gr.Textbox(label="Language", interactive=False)
                
            submit_btn = gr.Button("Validate & Save", variant="primary")
            submit_result = gr.Textbox(label="Status", interactive=False)
            
    user_input.submit(
        fn=process_message,
        inputs=[user_input, chatbot, template_state],
        outputs=[user_input, chatbot, template_state, preview_html, name_input, category_input, language_input]
    )
    
    submit_btn.click(
        fn=submit_and_save,
        inputs=[template_state],
        outputs=[submit_result]
    )

if __name__ == "__main__":
    demo.launch()
