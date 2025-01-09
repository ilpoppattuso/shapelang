import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re
import sys
from io import StringIO
import importlib
import traceback
import asyncio

def sqrt(value):
    return np.sqrt(value)

def std(value):
    if isinstance(value, set):
        value = list(value)
    return np.std(value)

def power(x, n):
    return x**n


inf = float('inf')








def execute_code():
    code = text_area.get("1.0", "end-1c")
    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        asyncio.run(parse_shapelang_code(code))
    except Exception as e:
        captured_output.write(f"Errore: {str(e)}\n")
        traceback.print_exc()
    finally:
        sys.stdout = sys.__stdout__

    output = captured_output.getvalue()
    console_output.delete(1.0, tk.END)
    console_output.insert(tk.END, output)

async def parse_shapelang_code(code, local_scope=None):
    if local_scope is None:
        local_scope = {}
    command_aliases = {}
    imported_modules = {}
    
    lines = code.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        
        # Normalizzazione degli spazi
        line = re.sub(r'\s*=\s*', '=', line)
        line = re.sub(r'\s*,\s*', ',', line)
        line = re.sub(r'\s*\+\s*', '+', line)
        line = re.sub(r'\s*>\s*', '>', line)
        line = re.sub(r'\s*<\s*', '<', line)
        line = re.sub(r'\s*>=\s*', '>=', line)
        line = re.sub(r'\s*<=\s*', '<=', line)
        line = re.sub(r'\s*==\s*', '==', line)
        
        if line.startswith("import"):
            match = re.match(r'import\s+(\w+)', line)
            if match:
                module_name = match.group(1)
                try:
                    module = importlib.import_module(module_name)
                    imported_modules[module_name] = module
                    local_scope[module_name] = module
                except ImportError:
                   raise ValueError(f"Modulo non trovato: {module_name}")
            i += 1
            continue
        
        if line.startswith("define"):
            alias_match = re.match(r'define\s+(\w+)\s+as\s+(\w+)', line)
            if alias_match:
                alias_name = alias_match.group(1)
                original_command = alias_match.group(2)
                command_aliases[original_command] = alias_name
            i += 1
            continue
        
        first_word = line.split(" ", 1)[0]
        if first_word in command_aliases:
            line = line.replace(first_word, command_aliases[first_word], 1)

        if "::reset" in line:
            for widget in frame_results.winfo_children():
                widget.destroy()
            line = line.replace("::reset", "")

        # cicli
        if line.startswith("while"):
            i = await handle_while(lines, i, local_scope)
        elif line.startswith("for"):
            i = await handle_for(lines, i, local_scope)
        elif line.startswith("if"):
            i = await handle_if(lines, i, local_scope)
   
        elif "line_plot" in line:
           await plot_code(line, local_scope)
        elif "print" in line:
            handle_print(line, local_scope)

        else:
            parse_assignment(line, local_scope)
        
        i += 1

    return str(local_scope)

def parse_assignment(line, local_scope):
    if "=" in line:
        var_name, value = line.split("=")
        var_name = var_name.strip()
        value = evaluate_expression(value.strip(), local_scope)
        local_scope[var_name] = value
    elif "++" in line:
        var_name = line.split("++")[0].strip()
        if var_name not in local_scope:
            local_scope[var_name] = 0
        local_scope[var_name] += 1


def evaluate_expression(expr, local_scope):

    def resolve_attribute(match):
        name = match.group(0)
        parts = name.split('.')
        current = local_scope.get(parts[0])
        
        if current is not None and len(parts) > 1:
            for part in parts[1:]:
                try:
                    current = getattr(current, part)
                except AttributeError:
                    return match.group(0)
            return str(current)
        return str(local_scope.get(name, name))

    expr = re.sub(r'\b[\w\.]+\b', resolve_attribute, expr)
    

    if expr.startswith('[') and expr.endswith(']'):
        try:
            return eval(expr)
        except Exception:
            pass

    # inf
    if 'inf' in expr:
        return inf

    expr = expr.replace("^", "**")
    
    try:
        if any(op in expr for op in ['>', '<', '>=', '<=', '==']):
            result = eval(expr)
            return bool(result)
        return eval(expr)
    except NameError as e:
        raise ValueError(f"Variabile non definita: {str(e)}")
    except SyntaxError:
        raise ValueError(f"Errore di sintassi nell'espressione: {expr}")

async def handle_while(lines, i, local_scope):
    condition = lines[i][6:].strip().rstrip(':')
    i += 1
    start = i
    
    body_lines = []
    while i < len(lines) and lines[i].strip() != "end":
        body_lines.append(lines[i])
        i += 1
    
    while evaluate_expression(condition, local_scope):
        print(f"Evaluating while condition: {condition} -> {evaluate_expression(condition, local_scope)}")
        await parse_shapelang_code("\n".join(body_lines), local_scope)
        condition = lines[start-1][6:].strip().rstrip(':') 
                
    return i

async def handle_for(lines, i, local_scope):
    match = re.match(r'for\s+(\w+)\s+in\s+\{([^\}]+)\}', lines[i])
    if match:
        var_name = match.group(1)
        values = list(map(int, match.group(2).split(',')))
        i += 1
        start = i
        while i < len(lines) and lines[i].strip() != "end":
            i += 1
        end = i
        for value in values:
            local_scope[var_name] = value
            await parse_shapelang_code("\n".join(lines[start:end]), local_scope)
    return i

async def handle_if(lines, i, local_scope):
    condition = lines[i][3:].strip()
    i += 1
    
    body_lines = []
    while i < len(lines) and lines[i].strip() != "end" and not lines[i].strip().startswith("else") and not lines[i].strip().startswith("else if"):
        body_lines.append(lines[i])
        i += 1
    
    if evaluate_expression(condition, local_scope):
        for line in body_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            if "print" in line:
                handle_print(line, local_scope)
            elif "++" in line or "=" in line:
                parse_assignment(line, local_scope)
    else:
        if i < len(lines) and lines[i].strip().startswith("else if"):
            i = await handle_else_if(lines, i, local_scope)
        elif i < len(lines) and lines[i].strip().startswith("else"):
            i = await handle_else(lines, i, local_scope)
            
    return i

async def handle_else_if(lines, i, local_scope):
    condition = lines[i][7:].strip()
    i += 1
    
    body_lines = []
    while i < len(lines) and lines[i].strip() != "end" and not lines[i].strip().startswith("else") and not lines[i].strip().startswith("else if"):
        body_lines.append(lines[i])
        i += 1
    
    if evaluate_expression(condition, local_scope):
        for line in body_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            if "print" in line:
                handle_print(line, local_scope)
            elif "++" in line or "=" in line:
                parse_assignment(line, local_scope)
    else:
        if i < len(lines) and lines[i].strip().startswith("else if"):
            i = await handle_else_if(lines, i, local_scope)
        elif i < len(lines) and lines[i].strip().startswith("else"):
            i = await handle_else(lines, i, local_scope)
            
    return i

async def handle_else(lines, i, local_scope):
    i += 1
    
    body_lines = []
    while i < len(lines) and lines[i].strip() != "end":
        body_lines.append(lines[i])
        i += 1
    
    for line in body_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
            
        if "print" in line:
            handle_print(line, local_scope)
        elif "++" in line or "=" in line:
            parse_assignment(line, local_scope)
            
    return i

def handle_print(line, local_scope):
    content = line.split("print", 1)[1].strip()
    if content.startswith('"') and content.endswith('"'):
        print(content[1:-1])
    else:
        parts = re.split(r'(\+)', content)
        evaluated_parts = []
        for part in parts:
            part = part.strip()
            if part == '+':
                evaluated_parts.append(part)
            else:
                try:
                    evaluated_parts.append(str(evaluate_expression(part, local_scope)))
                except Exception as e:
                    print(f"Error during evaluation: {e}")
                    evaluated_parts.append(str(part))
        result = ''.join(evaluated_parts)
        print(result)

async def sleep_async(duration):
    await asyncio.sleep(duration)

async def plot_code(line, local_scope):
    if "line_plot" in line:
        match = re.match(r"line_plot\(\s*([^,]+)\s*,\s*([^)]+)\s*\)", line)
        if match:
            x_values_expr = match.group(1).strip()
            y_values_expr = match.group(2).strip()
            
            x_values = evaluate_expression(x_values_expr, local_scope)
            y_values = evaluate_expression(y_values_expr, local_scope)
            
            if not isinstance(x_values, list):
                x_values = [x_values]
            if not isinstance(y_values, list):
                y_values = [y_values]    
                
            create_line_plot(x_values, y_values)

def create_line_plot(x, y):
    fig = plt.Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(x, y)
    ax.set_title('Grafico a Linee')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')

    canvas = FigureCanvasTkAgg(fig, master=frame_results)
    canvas.draw()
    canvas.get_tk_widget().pack()







root = tk.Tk()
root.title("Editor ShapeLang")

text_area = tk.Text(root, height=15, width=80)
text_area.pack(padx=10, pady=10)

execute_button = tk.Button(root, text="Esegui", command=execute_code)
execute_button.pack(pady=10)

console_output = tk.Text(root, height=10, width=80, bg="black", fg="white")
console_output.pack(padx=10, pady=10)

result_text = tk.StringVar()
result_label = tk.Label(root, textvariable=result_text, height=2)
result_label.pack(pady=10)

frame_results = tk.Frame(root)
frame_results.pack(padx=10, pady=10)

root.mainloop()