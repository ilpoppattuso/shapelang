# ShapeLang Editor

ShapeLang Editor is a simple graphical user interface (GUI) application for writing and executing ShapeLang code. It is built using Python and the Tkinter library.

## Features

- Write and execute ShapeLang (Python adaptation) code;
- Display console output;
- Plot line graphs using Matplotlib;
- Define custom aliases for commands;
- Support for basic mathematical functions and operations;
- Handle loops (`while`, `for`) and conditional statements (`if`, `else if`, `else`).

## Requirements

- Python 3.x
- Tkinter
- NumPy
- Matplotlib

## Installation

1. Clone the repository or download the source code;
2. Install the required dependencies using pip:
    ```sh
    pip install numpy matplotlib
    ```

## Usage

1. Run the main.py script:
    ```sh
    python main.py
    ```
2. Write your ShapeLang code in the text area;
3. Click the Execute button to execute the code;
4. View the console output and any generated plots in the respective areas.

## Example ShapeLang Code

```
define print as p

test = 1
p "Hello world!" 
p test

a = [1,2,3] 
b = [1,2,3] 
c = [1,2,3] 
d = [3,2,1]

line_plot(a,b)::reset
```
