import pandas as pd
import numpy as np
import plotly.graph_objs as go
import os

def prepare_df(input_df, task_name, lang): 

    """
    Prepares datafame for bar chart visualization.
    """
    #load and concatenate reference statistics
    if lang == 'Dutch':
        reference_df = pd.read_csv(f'reference_corpora/nl/{task_name}_combined.csv')
    elif lang == 'English':
        reference_df = pd.read_csv(f'reference_corpora/en/{task_name}_combined.csv')
    elif lang == 'German':
        reference_df = pd.read_csv(f'reference_corpora/de/{task_name}_combined.csv')
    elif lang == 'French':
        reference_df = pd.read_csv(f'reference_corpora/fr/{task_name}_combined.csv')
    else:
        raise ValueError('Language must be one of the following: "Dutch", "English", "German", "French".')
        
    if task_name == 'word_length_distribution':
        reference_df.columns = [int(col) if col not in {"source", "doc"} else col for col in reference_df.columns]
        input_df.columns = [int(col) if col not in {"source", "doc"} else col for col in input_df.columns]
    
    reference_df = pd.concat([input_df, reference_df]).fillna(0)
    
    #get df with only mean statistics
    mean_df = reference_df[reference_df['doc']=='mean']
    mean_df.drop(columns=['doc'], inplace=True)
    mean_df.set_index('source', inplace=True)

    #get df with only std statistics
    std_df = reference_df[reference_df['doc']=='std']
    std_df.drop(columns=['doc'], inplace=True)
    std_df.set_index('source', inplace=True)

    return mean_df, std_df

def generate_bar_chart(mean_df, std_df, savename, output_dir):

    """
    Generates bar chart visualizations for various feature comparisons.
    Arguments:
        dataframe: pd.DataFrame (rows are documents, columns are features)
        savename: filename that should be used to save the bar chart
    Returns:
        None
    """

    if savename == 'word_length_distribution': # remove columns of word length 26 and up which is usually noise and completely distorts the visualization
        filtered_columns = [col for col in mean_df.columns if type(col) == int and col < 24]
        mean_df = mean_df[filtered_columns]
        std_df = std_df[filtered_columns]
    
    # Transpose the dataframe to have corpora as rows and features as columns
    transposed_df = mean_df.transpose().replace({0: np.nan})
    std_df = std_df.transpose()

    # Define data for the bar chart
    data = []
    for column in transposed_df.columns:
        trace = go.Bar(
            x=transposed_df.index,
            y=transposed_df[column],
            name=column,
            visible=(column == 'input corpus'),  # Show only 'Input corpus' initially, reference corpora can be toggled
            error_y=dict(
                type='data',
                array=std_df[column],
                visible=True
            )
        )
        data.append(trace)

    # Define layout for the plot
    layout = go.Layout(
        barmode='group',
        width=1024,
        height=512,
        showlegend=True,
        # plot_bgcolor='rgba(0, 0, 0, 0)',
        # paper_bgcolor='rgba(0, 0, 0, 0)',
        template='plotly_white', #ploty_dark
    )

    # Create the figure
    fig = go.Figure(data=data, layout=layout)

    # Update visibility toggling for legend items
    for i in range(len(fig.data)):
        if fig.data[i].name != 'input corpus':
            fig.data[i].visible = 'legendonly'

    # Sort columns based on 'input corpus' values
    input_corpus_values = transposed_df['input corpus']
    if savename == 'word_length_distribution': # Conditionally sort by x-ticks if savename is 'word_length_distribution'
        sorted_columns = sorted(transposed_df.index, key=lambda x: int(x))
    else:
        sorted_columns = input_corpus_values.sort_values(ascending=False).index
    fig.update_xaxes(categoryorder='array', categoryarray=sorted_columns)

    # Display the plot
    save_path = os.path.join(output_dir, 'visualizations', savename+'.html')
    fig.write_html(save_path)

    return fig