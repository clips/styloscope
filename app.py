import gradio as gr
import pandas as pd
import stylo_app

theme = gr.themes.Soft(
    primary_hue="amber",
    secondary_hue="amber",
    neutral_hue="neutral",
    font=['Montserrat', 'ui-sans-serif', 'system-ui', 'sans-serif'],
    font_mono=['IBM Plex Mono', 'ui-monospace', 'Consolas', 'monospace'],
)

css = """
h1 {
    display: block;
    text-align: center;
    font-size: 50pt;
}

.gradio-container {
    background-color: #222222;
}

table {
  border-collapse: collapse;
  width: 100%;
}

th, td {
  border-right: 1px solid white; /* Vertical border between columns */
  padding: 0.3em;
}

tr:not(:first-child) td {
  border-bottom: 1px solid white; /* Horizontal border after the first row */
}

th {
  border-top: 1px solid white; /* Border above the header */
}

th:last-child, td:last-child {
  border-right: none; 
}
"""

def visible_output(input_text):
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def visible_plots(file):
    return gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)

with gr.Blocks(title="Stylene", theme=theme, css=css) as demo:
    title = gr.Markdown("""# Stylene""")
    
    with gr.Tab("Pipeline"):

        # components
        file = gr.File(file_types = ['.csv'], file_count = "single")
        lang = gr.Dropdown(["Dutch", "English", "French", "German"], label="Language", value="Dutch", interactive=True)
        readability = gr.Dropdown(["ARI", "Coleman-Liau", "Flesch reading ease", "Flesch Kincaid grade level", "Gunning Fog", "SMOG", "LIX", "RIX"], label="Readability metric", value="RIX", interactive=True)
        diversity = gr.Dropdown(["STTR", "TTR", "RTTR", "CTTR", "Herdan", "Summer", "Dugast", "Maas"], label="Lexical diversity metric", value="STTR", interactive=True)
        button = gr.Button('Submit')

        # outputs
        zip_out = gr.File(label='Output', visible=False)
        dep_plot = gr.Plot(label='Distribution of syntactic dependencies', show_label=True, visible=False)
        pos_plot = gr.Plot(label='Distribution of part-of-speech tags', show_label=True, visible=False)
        punct_plot = gr.Plot(label='Distribution of punctuation marks', show_label=True, visible=False)
        len_plot = gr.Plot(label='Distribution of word lengths', show_label=True, visible=False)

        button.click( # first make zip output component visible (so that progress bar is visible)
            visible_output, 
            inputs=file, 
            outputs=[zip_out, dep_plot, pos_plot, punct_plot, len_plot]
            ).then( # then run pipeline
                stylo_app.main, 
                inputs=[file, lang, readability, diversity], 
                outputs=[zip_out, dep_plot, pos_plot, punct_plot, len_plot]
                ).then( # then make plots visible
                    visible_plots,
                    inputs=file,
                    outputs=[dep_plot, pos_plot, punct_plot, len_plot]
                )
        
    with gr.Tab("User guidelines"):
        gr.Markdown("""### Readability metrics""")
        gr.Markdown(
            """
            We recommend using RIX, because it is the most intuitive metric, and it is was not designed for a specific language or text genre.           
            | Metric       | Formula                                          | Language  |
            |--------------|--------------------------------------------------|--------|
            | ARI | 4.71 * (characters / words) + 0.5 * (words / sentences) - 21.43 | English |
            | Coleman-Liau* | 0.0588 * L - 0.296 * S - 15.8 | English;<br />Texts must be > 100 tokens |
            | Flesch reading ease | 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words) | English |
            | Flesch Kincaid grade level | 11.8 * (syllables / words) + 0.39 * (words / sentences) - 15.59 | English |
            | Gunning Fog** | 0.4 * (words / sentences + % complex words) | English;<br />Texts must be > 100 syllables |
            | LIX*** | (words / sentences) + (100 * (long words / words)) | Language-independant |
            | RIX*** | (long words / sentences) + (words / sentences) | Language-independant;<br />More interpretable version of LIX |
            | SMOG** | sqrt(complex words) + 3 | English;<br />Orig. developed for clinical texts);<br />Texts must be > 30 sentences. |

            *L = Average number of characters per 100 tokens<br /> S = Average number of sentences per 100 tokens
            
            **Complex words = words that contain at least 3 syllables
            
            ***Long words = words longer than 6 characters
            """
        )
        gr.Markdown("""### Lexical diversity metrics""")
        gr.Markdown("""
            We recommend using the standardized type-token ratio (STTR), since it is less likely to be influenced by varying text lengths.
            | Metric | Formula                                         | 
            |--------|-------------------------------------------------|
            | TTR    | Number of unique words / Total number of words |
            | STTR   | Mean of TTR scores per 100 words |
            | RTTR   | Number of unique words / sqrt(Total number of words) |
            | CTTR   | Number of unique words / sqrt(2 * Total number of words) |
            | Herdan | log(Number of unique words) / log(Total number of words) |
            | Summer | log( log(Number of unique words) ) / log( log(Total number of words) ) |
            | Dugast | log(Total number of words)**2) / ( log(Total number of words) - log(Number of unique words) ) |
            | Maas   | ( log(Total number of words) - log(Number of unique words) ) / log(Total number of words)**2 |
            """
        )

demo.queue(default_concurrency_limit=10).launch(share=True)