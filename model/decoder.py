from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# model_name = "Qwen/Qwen2.5-Coder-3B-Instruct"
model_name = "Qwen/Qwen2.5-Coder-3B"
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

print("yay")
model.eval()

input_ids = None
output = model.generate(
    input_ids, 
    output_scores=True, 
    output_hidden_states=True, 
    output_attentions=True, 
    return_dict_in_generate=True, 
    max_new_tokens=1)

# "for single step probing"
# with torch.no_grad():
#     out = model(
#         input_ids, 
#         output_hidden_states=True, 
#         output_attentions=True)

