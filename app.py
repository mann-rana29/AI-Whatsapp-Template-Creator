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
    json_str = json.dumps(new_template, indent=2)
    
    name = new_template.get("name", "")
    category = new_template.get("category", "")
    language = new_template.get("language", "")
    
    return "", chat_history, new_template, preview_html, json_str, name, category, language

def generate_preview_html(template):
    if not template or not template.get("components"):
        return "<div style='padding:20px; font-family:sans-serif; color: #555;'>Preview not available. Generate a template first.</div>"
        
    components = template.get("components", [])
    category = template.get("category", "N/A")
    language = template.get("language", "N/A")
    
    # WhatsApp Chat Background wrapper
    html = f"<div style='margin-bottom: 10px; font-family: sans-serif; font-size: 14px; color: #555;'><strong>Category:</strong> {category} &nbsp;|&nbsp; <strong>Language:</strong> {language}</div>"
    html += "<div style='width: 100%; max-width: 450px; background-color: #efeae2; background-image: url(\"https://i.pinimg.com/736x/8c/98/99/8c98994518b575bfd8c949e91d20548b.jpg\"); background-size: cover; border-radius: 12px; padding: 20px; font-family: \"Segoe UI\", \"Helvetica Neue\", Helvetica, Arial, sans-serif; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: flex; flex-direction: column; align-items: flex-start;'>"
    
    # WhatsApp Message Bubble
    html += "<div style='background-color: white; color: #111b21; padding: 4px; border-radius: 8px; border-top-left-radius: 0; box-shadow: 0 1px 2px rgba(11,20,26,0.1); width: 100%; max-width: 380px; position: relative;'>"
    
    # SVG Tail for Bubble
    html += "<svg viewBox=\"0 0 8 13\" width=\"8\" height=\"13\" style=\"position: absolute; top: 0; left: -8px; color: white;\"><path opacity=\".13\" fill=\"#00000000\" d=\"M1.533 3.118L8 12.114V1h-3.28c-1.23 0-2.058.914-2.128 2.118z\"></path><path opacity=\".08\" fill=\"#00000000\" d=\"M1.121 3.28L8 12.28V.5h-3.28c-1.23 0-2.058.914-2.128 2.118z\"></path><path opacity=\".04\" fill=\"#00000000\" d=\"M.708 3.441L8 12.441V0h-3.28c-1.23 0-2.058.914-2.128 2.118z\"></path><path fill=\"currentColor\" d=\"M1.533 3.118L8 12.114V1h-3.28c-1.23 0-2.058.914-2.128 2.118z\"></path></svg>"
    
    html += "<div style='padding: 8px;'>"
    
    for comp in components:
        comp_type = comp.get("type", "")
        if comp_type == "HEADER":
            if comp.get("format") == "TEXT":
                html += f"<strong style='display:block; margin-bottom:6px; font-size:16px; line-height: 22px; color: #111b21;'>{comp.get('text','')}</strong>"
            else:
                fmt = comp.get('format', 'MEDIA')
                example = comp.get('example', {})
                handles = example.get('header_handle', [])
                media_url = handles[0] if handles else ""
                
                if fmt == "IMAGE" and media_url:
                    html += f"<div style='margin-bottom: 8px; border-radius: 6px; overflow: hidden; height: 160px; background-color: #ccd0d5; display:flex; align-items:center; justify-content:center;'><img src='{media_url}' style='width: 100%; height: 100%; object-fit: cover;' onerror=\"this.style.display='none'; this.nextElementSibling.style.display='block';\" /><span style='display:none; color:#54656f; font-weight:600; font-size: 14px;'>IMAGE HEADER</span></div>"
                else:
                    html += f"<div style='background-color: #ccd0d5; height: 160px; border-radius: 6px; margin-bottom: 8px; display:flex; align-items:center; justify-content:center; color:#54656f; font-weight:600; font-size: 14px;'>{fmt} HEADER</div>"
        elif comp_type == "BODY":
            text = comp.get("text", "").replace('\n', '<br>')
            html += f"<div style='font-size:15px; margin-bottom:6px; line-height: 20px; color: #111b21; word-wrap: break-word;'>{text}</div>"
        elif comp_type == "FOOTER":
            html += f"<div style='font-size:13px; color: #667781; line-height: 18px;'>{comp.get('text', '')}</div>"
            
    html += "</div>" # end inner padding
    
    buttons_comp = next((c for c in components if c.get("type") == "BUTTONS"), None)
    if buttons_comp:
        for btn in buttons_comp.get("buttons", []):
            btn_type = btn.get('type', '')
            btn_text = btn.get('text', '')
            extra = ""
            icon = ""
            if btn_type == "URL":
                icon = "🔗 "
                extra = f" <br><span style='font-size:11px; color:#667781; font-weight:normal;'>{btn.get('url', '')}</span>"
            elif btn_type == "PHONE_NUMBER":
                icon = "📞 "
                extra = f" <br><span style='font-size:11px; color:#667781; font-weight:normal;'>{btn.get('phone_number', '')}</span>"
            elif btn_type in ["OTP", "COPY_CODE"]:
                icon = "📋 "
            elif btn_type == "QUICK_REPLY":
                icon = "↩️ "
                
            html += f"<div style='border-top: 1px solid #f0f2f5; text-align: center; color: #00a884; padding: 12px 10px; cursor: pointer; font-weight: 500; font-size:15px; background-color: transparent;'>{icon}{btn_text}{extra}</div>"
            
    carousel_comp = next((c for c in components if c.get("type") == "CAROUSEL"), None)
    if carousel_comp:
        html += "<div style='display:flex; overflow-x:auto; padding: 8px 4px 8px 8px; gap: 8px; scrollbar-width: thin;'>"
        for card in carousel_comp.get("cards", []):
            html += "<div style='min-width: 240px; background-color: #f0f2f5; border-radius: 8px; border: 1px solid #e9edef; display: flex; flex-direction: column; overflow: hidden;'>"
            for c_comp in card.get("components", []):
                if c_comp.get("type") == "HEADER":
                    fmt = c_comp.get('format', 'MEDIA')
                    example = c_comp.get('example', {})
                    handles = example.get('header_handle', [])
                    media_url = handles[0] if handles else ""
                    
                    if fmt == "IMAGE" and media_url:
                        html += f"<div style='background-color: #ccd0d5; height: 120px; display:flex; align-items:center; justify-content:center; overflow: hidden;'><img src='{media_url}' style='width: 100%; height: 100%; object-fit: cover;' onerror=\"this.style.display='none'; this.nextElementSibling.style.display='block';\" /><span style='display:none; font-size:12px; color: #54656f; font-weight:600;'>IMAGE</span></div>"
                    else:
                        html += f"<div style='background-color: #ccd0d5; height: 120px; display:flex; align-items:center; justify-content:center; font-size:12px; color: #54656f; font-weight:600;'>{fmt}</div>"
                elif c_comp.get("type") == "BODY":
                    html += f"<div style='padding: 10px; font-size:14px; line-height: 19px; color: #111b21; flex-grow: 1;'>{c_comp.get('text','')}</div>"
                elif c_comp.get("type") == "BUTTONS":
                    for c_btn in c_comp.get("buttons", []):
                        btn_type = c_btn.get('type', '')
                        btn_text = c_btn.get('text', '')
                        extra = ""
                        icon = ""
                        if btn_type == "URL":
                            icon = "🔗 "
                        elif btn_type == "PHONE_NUMBER":
                            icon = "📞 "
                        html += f"<div style='border-top: 1px solid #d1d7db; text-align: center; color: #00a884; padding: 10px; font-size: 14px; font-weight: 500; background-color: white;'>{icon}{btn_text}</div>"
            html += "</div>"
        html += "</div>"
            
    html += "</div>" # end bubble
    html += "</div>" # end chat background wrapper
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
            gr.Markdown("### Template Preview")
            preview_html = gr.HTML(value="<div style='background-color:#E1F5FE; color: black; padding:20px; border-radius:10px; font-family:sans-serif;'>Preview area</div>")
            
            gr.Markdown("### JSON Output")
            json_output = gr.Code(language="json", interactive=False)
            
            with gr.Accordion("Template Data & Save", open=False):
                name_input = gr.Textbox(label="Template Name", interactive=False)
                category_input = gr.Textbox(label="Category", interactive=False)
                language_input = gr.Textbox(label="Language", interactive=False)
                
                submit_btn = gr.Button("Validate & Save", variant="primary")
                submit_result = gr.Textbox(label="Status", interactive=False)
            
    user_input.submit(
        fn=process_message,
        inputs=[user_input, chatbot, template_state],
        outputs=[user_input, chatbot, template_state, preview_html, json_output, name_input, category_input, language_input]
    )
    
    submit_btn.click(
        fn=submit_and_save,
        inputs=[template_state],
        outputs=[submit_result]
    )

if __name__ == "__main__":
    demo.launch()
