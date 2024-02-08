import gradio as gr
import pandas as pd
import stylo_app

css = """
h1 {
    display: block;
    text-align: center;
    font-size: 32pt;
}
.progress-bar-wrap.progress-bar-wrap.progress-bar-wrap
{
	border-radius: var(--input-radius);
	height: 1.25rem;
	margin-top: 1rem;
	overflow: hidden;
	width: 70%;
}
"""
theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="amber",
).set(
    button_primary_background_fill='*secondary_500',
    button_primary_background_fill_hover='*secondary_400',
    block_label_background_fill='*primary_50',
)

def visible_output(input_text):
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def visible_plots(file):
    return gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)

with gr.Blocks(title="CLARIAH-VL Stylometry Pipeline", theme=theme, css=css) as demo:
    title = gr.Markdown("""# CLARIAH-VL Stylometry Pipeline""")
    
    with gr.Tab("Pipeline"):

        # components
        with gr.Row(variant='panel'):
            file = gr.File(file_types = ['.csv', '.zip'], file_count = "single")

        with gr.Row(variant='panel'):
            lang = gr.Dropdown(["Dutch", "English", "French", "German"], label="Language", value="Dutch", interactive=True)
            readability = gr.Dropdown(["ARI", "Coleman-Liau", "Flesch reading ease", "Flesch Kincaid grade level", "Gunning Fog", "SMOG", "LIX", "RIX"], label="Readability metric", value="RIX", interactive=True)
            diversity = gr.Dropdown(["STTR", "TTR", "RTTR", "CTTR", "Herdan", "Summer", "Dugast", "Maas"], label="Lexical diversity metric", value="STTR", interactive=True)
        
        button = gr.Button('Submit', variant='primary')

        # outputs
        zip_out = gr.File(label='Output', visible=False)
        basic_statistics = gr.Dataframe(headers=['Corpus statistics', 'Mean', 'Std.'], visible=False)
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
                outputs=[zip_out, basic_statistics, dep_plot, pos_plot, punct_plot, len_plot]
                ).then( # then make plots visible
                    visible_plots,
                    inputs=file,
                    outputs=[basic_statistics, dep_plot, pos_plot, punct_plot, len_plot]
                )
    
    with gr.Tab("Authorship attribution demo"):
        gr.load("clips/xlm-roberta-text-genre-dutch", src="models", title="", description="**Text genre prediction**")
        gr.load("clips/robbert-2023-dutch-base-gender", src="models", title="", description="**Gender prediction**")
        
    with gr.Tab("User guidelines"):

        gr.Markdown("""### Input""")
        gr.Markdown("""The input of the pipeline must be either a .zip folder containing UTF8-encoded .txt files, or a .csv file containing one document per row (this can be a complete text or, if desired, a single sentence). The documents should be placed under a column named "text". Additional columns are allowed and do not affect the pipeline.""")
        
        gr.Markdown("""### Language""")
        gr.Markdown("""The user must specify the language of the input corpus (Dutch, French, German, English). Note that the tools used in this pipeline have been trained on standard, contemporary language, and will therefore perform best on this type of data. When using a multilingual corpus, it is best to split up the data per language and run the pipeline multiple times while selecting a different language per run.""")

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
    
    with gr.Tab("About"):
        gr.Markdown("""        
        ### Project
        This stylometry pipeline was developed by [CLiPS](https://www.uantwerpen.be/en/research-groups/clips/) ([University of Antwerp](https://www.uantwerpen.be/en/)) during the [CLARIAH-VL](https://clariahvl.hypotheses.org/) project.

        ### Contact
        If you have questions, please send them to [Jens Lemmens](mailto:jens.lemmens@uantwerpen.be) or [Walter Daelemans](mailto:walter.daelemans@uantwerpen.be)
        """)
    
    with gr.Row():
        gr.Markdown("""<center><img src="https://platformdh.uantwerpen.be/wp-content/uploads/2019/03/clariah_def.png" alt="Image" width="200"/></center>""")
        gr.Markdown("""<center><img src="https://thomasmore.be/sites/default/files/2022-11/UA-hor-1-nl-rgb.jpg" alt="Image" width="175"/></center>""")


demo.queue(default_concurrency_limit=10).launch(share=False)
