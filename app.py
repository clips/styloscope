import gradio as gr
import uuid, os
import stylo_app

import smtplib 
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

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

def set_visibility():
    """
    Sets the visibility of the output widgets to False
    when initiating a new run.
    """
    return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def send_mail(receiver, run_id):
  
  """Sends email with pipeline output attached to user."""

  if receiver.strip(): #check if user actually wants to receive output

    # specify header
    msg = MIMEMultipart()
    msg['From'] = 'styloscope.ua@gmail.com'
    msg['To'] = receiver.strip()
    msg['Subject'] = f'Output {run_id}'

    # add body of message
    body = f'Dear Styloscope user,\n\nAttached you can find the output of run {run_id}.\n\nKind regards.'
    msg.attach(MIMEText(body, 'plain'))

    # attach output
    with open(f'./outputs/{run_id}.zip', 'rb') as file:
      msg.attach(MIMEApplication(file.read(), Name=f'{run_id}.zip'))
      text = msg.as_string()

    # set up mailing server
    path = '/var/www/CLARIAH-stylo/app_password.txt' 
    if os.path.exists(path):
        with open(path) as f:
            app_password = f.read()

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('styloscope.ua@gmail.com', app_password)
        server.sendmail('styloscope.ua@gmail.com', receiver, text)
        server.quit()

def generate_run_id():
    run_id = str(uuid.uuid4())
    return gr.update(value=run_id, visible=True)

def show_input(input_type):
    """
    Used to control which input widget is being shown.
    """
    if input_type == "Corpus":
        return gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=True)


def show_sttr_span_textbox(metric):
    """
    Used to toggle token span size parameter when STTR is selected as diversity metric.
    """
    if metric == "STTR":
        return gr.update(visible=True)
    else: 
        return gr.update(visible=False)

def visible_output(input_text):
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def visible_plots(file):
    return gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)

with gr.Blocks(title="Styloscope", theme=theme, css=css) as demo:
    title = gr.Markdown("""# Styloscope""")
    
    with gr.Tab("Pipeline"):

        # components
        with gr.Row():
            gr.Markdown("### Provide input data")

        with gr.Row(variant='panel'):
            input_type = gr.Radio(choices=['Corpus', 'HuggingFace dataset'], value='Corpus', label='Type', interactive=True,
            info="""Upload your own corpus or download a public dataset from the HuggingFace hub.""")
    
        with gr.Row(variant='panel'):
                with gr.Column(visible=True) as corpus_widget:
                    file = gr.File(file_types = ['.csv', '.zip'], file_count = "single")
                
                with gr.Column(visible=False) as hf_widget:
                    dataset = gr.Textbox(label="Name", info="Dataset identifier mentioned on HuggingFace.")
                    subset = gr.Textbox(label="Subset", info="Mandatory if dataset contains subsets.")
                    split = gr.Textbox(label="Split", info="Mandatory if dataset contains splits.")

        with gr.Row(variant='panel'):
            column_name = gr.Textbox(label="Column", info="Column name (for .csv / Huggingface) that will be used for writing style analysis.")

        input_type.change(
            show_input, input_type, [corpus_widget, hf_widget]
        )

        with gr.Row():
            gr.Markdown("### Set pipeline parameters")

        with gr.Row(variant='panel'):
            lang = gr.Dropdown(["Dutch", "English", "French", "German"], label="Language", value="Dutch", interactive=True)
            readability = gr.Dropdown(["ARI", "Coleman-Liau", "Flesch reading ease", "Flesch Kincaid grade level", "Gunning Fog", "SMOG", "LIX", "RIX"], label="Readability metric", value="RIX", interactive=True)
            diversity = gr.Dropdown(["STTR", "TTR", "RTTR", "CTTR", "Herdan", "Summer", "Dugast", "Maas"], label="Lexical diversity metric", value="STTR", interactive=True)
            span_size = gr.Textbox(label='STTR token span', value=100, visible=True)

            diversity.change(
                show_sttr_span_textbox, diversity, [span_size]
            )
        
        with gr.Row(variant="panel"):
            receiver = gr.Textbox(label='E-mail', info="Please provide your e-mail address to receive the output in your mailbox (optional). Personal info will not be saved or used for any other purpose than this application.")
        
        button = gr.Button('Submit', variant='primary')
        cancel_button = gr.Button('Cancel', variant='primary')

        # outputs
        run_id = gr.Textbox(label='Run index', info="", visible=False, interactive=False)
        zip_out = gr.File(label='Output', visible=False)
        basic_statistics = gr.Dataframe(headers=['Corpus statistics', 'Mean', 'Std.'], visible=False)
        dep_plot = gr.Plot(label='Distribution of syntactic dependencies', show_label=True, visible=False)
        pos_plot = gr.Plot(label='Distribution of part-of-speech tags', show_label=True, visible=False)
        punct_plot = gr.Plot(label='Distribution of punctuation marks', show_label=True, visible=False)
        len_plot = gr.Plot(label='Distribution of word lengths', show_label=True, visible=False)

        button.click( # first set visibility of the widgets
            set_visibility,
            outputs=[run_id, zip_out, basic_statistics, dep_plot, pos_plot, punct_plot, len_plot],
            trigger_mode="once",
            ).then( # then generate and show run index
                generate_run_id,
                outputs=run_id,
                ).then( # then make zip output component visible (so that progress bar is visible)
                    visible_output, 
                    inputs=file, 
                    outputs=[zip_out, dep_plot, pos_plot, punct_plot, len_plot]
                    ).then( # then run pipeline
                        stylo_app.main, 
                        inputs=[input_type, file, dataset, subset, split, column_name, lang, readability, diversity, span_size, run_id], 
                        outputs=[zip_out, basic_statistics, dep_plot, pos_plot, punct_plot, len_plot]
                        ).then( # then make plots visible
                            visible_plots,
                            inputs=file,
                            outputs=[basic_statistics, dep_plot, pos_plot, punct_plot, len_plot]
                            ).then(
                                send_mail,
                                inputs=[receiver, run_id]
                            )
    
    with gr.Tab("Authorship attribution demo"):
        gr.load("clips/xlm-roberta-text-genre-dutch", src="models", title="", description="**Text genre prediction**")
        gr.load("clips/robbert-2023-dutch-base-gender", src="models", title="", description="**Gender prediction**")
        
    with gr.Tab("User guidelines"):

        gr.Markdown("""### Input""")
        gr.Markdown("""The input of the pipeline must be either a corpus or a publicly available HuggingFace dataset. 
        Corpora can be uploaded as a .zip folder containing UTF8-encoded .txt files, or as a .csv file containing one document per row (documents must be placed under a column named "text", additional columns are allowed and do not affect the pipeline).
        When using a HuggingFace dataset, you will be asked to specify the dataset identifier, the text column on which an analysis needs to be performed, and optionally the data subset and split of interest.
        """)
        
        gr.Markdown("""### Language""")
        gr.Markdown("""The user must specify the language of the input corpus. Our tools currently supports analysis of Dutch, French, English, and German. Note that the tools used in this pipeline have been trained on standard, contemporary language, and will therefore perform best on this type of data. When using a multilingual corpus, it is best to split up the data per language and run the pipeline multiple times while selecting a different language per run.""")

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
            | STTR   | Mean of TTR scores per n words (if number of tokens > n else no score) |
            | RTTR   | Number of unique words / sqrt(Total number of words) |
            | CTTR   | Number of unique words / sqrt(2 * Total number of words) |
            | Herdan | log(Number of unique words) / log(Total number of words) |
            | Summer | log( log(Number of unique words) ) / log( log(Total number of words) ) |
            | Dugast | ( log(Total number of words)**2) / ( log(Total number of words) - log(Number of unique words) ) |
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

demo.queue(default_concurrency_limit=10)
demo.launch(server_port=7860, share=False, server_name='0.0.0.0')
