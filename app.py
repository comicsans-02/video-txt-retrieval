import streamlit as st
import json
import os
import requests

# ------------------------------
# Streamlit App Setup
# ------------------------------

# Set page configuration
st.set_page_config(page_title="📝 Multilingual Video Annotation Viewer", layout="wide")

# Base URL for your data hosted on Cloudflare R2
BASE_URL = 'https://pub-ab749ed8594a49d8bdd397eb3de407e0.r2.dev/data'

# Function to load video URL
def load_video(language, video_name):
    """
    Constructs the URL to access the video via Cloudflare R2.
    """
    video_url = f"{BASE_URL}/{language}/videos/{video_name}"
    return video_url

# Function to load transcript
def load_transcript(language, video_name):
    """
    Loads the transcript data from Cloudflare R2.
    """
    transcript_url = f"{BASE_URL}/{language}/time_stamp/{os.path.splitext(video_name)[0]}.json"

    response = requests.get(transcript_url)
    if response.status_code == 200:
        try:
            transcript_data = response.json()
            return transcript_data
        except ValueError:
            st.error(f"Error decoding JSON from: {transcript_url}")
            return []
    else:
        st.error(f"Transcript file not found: {transcript_url}")
        return []

# Function to load nodes from nodes file
def load_nodes(language, video_name):
    """
    Loads the node texts from the nodes file.
    Only applicable for English videos when causal relations are enabled.
    """
    nodes = []
    if language == 'English' and st.session_state.get('use_causal_relations', False):
        node_url = f"{BASE_URL}/{language}/causal_graphs/{os.path.splitext(video_name)[0]}_nodes.txt"

        response = requests.get(node_url)
        if response.status_code == 200:
            nodes = response.text.strip().split('\n')
        else:
            st.warning(f"Nodes file not found: {node_url}")
    return nodes

# Function to load causal graph
def load_causal_graph(language, video_name):
    """
    Loads the causal graph data from edge files.
    """
    edges = []
    if language == 'English' and st.session_state.get('use_causal_relations', False):
        edge_url = f"{BASE_URL}/{language}/causal_graphs/{os.path.splitext(video_name)[0]}_edges.txt"

        response = requests.get(edge_url)
        if response.status_code == 200:
            edges = response.text.strip().split('\n')
        else:
            st.warning(f"Edges file not found: {edge_url}")
    return edges

# Function to generate transcript HTML
def generate_transcript_html(transcript_data):
    """
    Generates the HTML for the transcript section.
    """
    transcript_html = ''
    for index, item in enumerate(transcript_data):
        start = item.get('begin_time', '')
        end = item.get('end_time', '')
        text = item['text']
        matched = item.get('matched', 'no').lower()
        node_id = index  # Assign node_id based on index

        # Determine CSS class based on 'matched' status
        matched_class = 'matched' if matched == 'yes' else 'unmatched'

        # Handle missing start and end times
        data_start = f'data-start="{start}"' if start else ''
        data_end = f'data-end="{end}"' if end else ''

        transcript_html += f'''
        <p class="sentence {matched_class}" {data_start} {data_end} data-node="{node_id}">
            {text}
        </p>
        '''
    return transcript_html

def main():
    st.title("📝 Multilingual Video Annotation Viewer")

    # Sidebar for language and video selection
    st.sidebar.header("📁 Select Language and Video")

    # List available languages (keeping the incorrect Portuguese spelling)
    languages = ['English', 'Chinese', 'French', 'Hindi', 'Portuguese', 'Russian', 'Spanish']

    selected_language = st.sidebar.selectbox("🌐 Language", languages)

    # List available videos in the selected language
    videos = {
        'English': ['MSrzeH5n-1o.mp4', 'LcqZ_7lNzOY.mp4', 'MoLei0grJ7I.mp4', 'vqIiCEEwxao.mp4'],
        'Chinese': ['FsMgMb_yF88.mp4', 'jf383t0GY08.mp4'],
        'French': ['b_Cdq3QkogY.mp4', 'NG7snqVvf2o.mp4'],
        'Hindi': ['V4fAA3Kxa90.mp4', 'ZH3USZAyrP8.mp4'],
        'Portuguese': ['nuks1jnUbss.mp4', 'SpmYKDC69Ms.mp4'],  # Incorrect spelling kept
        'Russian': ['IO_ilU3cFJ0.mp4', 'q-TsK_gFZXk.mp4'],
        'Spanish': ['FD_-JlsDTvk.mp4', 'Z5EqZ57exMA.mp4']
    }

    if selected_language in videos and videos[selected_language]:
        selected_video = st.sidebar.selectbox("🎬 Video", videos[selected_language])
    else:
        st.error(f"No video files found for language: {selected_language}")
        return

    # Add checkbox for enabling causal relations (only for English videos)
    use_causal_relations = False
    if selected_language == 'English':
        use_causal_relations = st.sidebar.checkbox("🔗 Enable Causal Relations")
        st.session_state.use_causal_relations = use_causal_relations  # Store in session_state
    else:
        st.session_state.use_causal_relations = False  # Ensure it's False for non-English languages

    # Load video URL
    video_url = load_video(selected_language, selected_video)

    # Load transcript data
    transcript_data = load_transcript(selected_language, selected_video)

    # Load nodes and causal graph data if enabled and English
    if selected_language == 'English' and use_causal_relations:
        nodes = load_nodes(selected_language, selected_video)
        edges = load_causal_graph(selected_language, selected_video)
    else:
        nodes = []
        edges = []

    # Prepare causal edges data for JavaScript
    if edges:
        causal_edges_json = json.dumps(edges)
    else:
        causal_edges_json = '[]'

    # Prepare nodes data for JavaScript (to get node texts)
    if nodes:
        nodes_json = json.dumps(nodes)
    else:
        nodes_json = '[]'

    # Generate transcript HTML
    transcript_html = generate_transcript_html(transcript_data)

    # Conditionally include the graph section in the HTML content
    if use_causal_relations:
        graph_section_html = '''
        <!-- Graph Section -->
        <div id="graph-section">
            <h3>🧩 Causal Relationship Graph</h3>
            <div id="graph"></div>
        </div>
        '''
    else:
        graph_section_html = ''

    # Combine video, transcript, and graph into a single HTML content
    html_content = f'''
    <style>
        body {{
            margin: 0;
            padding: 0;
            color: white;
            background-color: #0e0e0e;
            font-family: Arial, sans-serif;
        }}
        /* Container for video and transcript */
        #video-transcript-container {{
            display: flex;
            flex-direction: row;
            width: 100%;
            background-color: #0e0e0e;
            height: 600px;
            box-sizing: border-box;
        }}
        #video-section {{
            flex: 1;
            padding: 10px;
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
        }}
        #transcript-section {{
            flex: 1;
            padding: 10px;
            overflow-y: auto;
            background-color: #0e0e0e;
            box-sizing: border-box;
        }}
        #videoPlayer {{
            flex: 1;
            width: 100%;
        }}
        .sentence {{
            cursor: pointer;
            padding: 5px;
            color: white;
            transition: background-color 0.3s, color 0.3s;
            margin: 5px 0;
        }}
        .sentence:hover {{
            background-color: #444;
        }}
        .matched {{
            /* No additional styles for matched sentences */
        }}
        .unmatched {{
            color: grey;
            font-style: italic;
        }}
        .highlight {{
            background-color: yellow;
            color: black;
        }}
        .predecessor-highlight {{
            background-color: lightgreen;
            color: black;
        }}
        .successor-highlight {{
            background-color: lightblue;
            color: black;
        }}
        .unmatched-highlight {{
            background-color: grey;
            color: black;
        }}
        /* Graph section */
        #graph-section {{
            padding: 10px;
            background-color: #0e0e0e;
            box-sizing: border-box;
        }}
        #graph {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .node {{
            padding: 10px;
            background-color: #444;
            color: white;
            border-radius: 5px;
            text-align: center;
            max-width: 200px;
            /* Removed hover effects */
            cursor: default;
        }}
        .edge {{
            margin: 0 5px;
            color: white;
            font-size: 24px;
        }}
        .predecessor-node {{
            background-color: lightgreen;
            color: black;
        }}
        .successor-node {{
            background-color: lightblue;
            color: black;
        }}
        .selected-node {{
            background-color: yellow;
            color: black;
        }}
    </style>

    <!-- Video and Transcript Container -->
    <div id="video-transcript-container">
        <div id="video-section">
            <video id="videoPlayer" controls>
                <source src="{video_url}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        <div id="transcript-section">
            {transcript_html}
        </div>
    </div>

    {graph_section_html}

    <script>
    // Pass Python variables to JavaScript
    const useCausalRelations = {str(use_causal_relations).lower()};
    const causalEdges = {causal_edges_json};
    const nodes = {nodes_json};

    const video = document.getElementById('videoPlayer');
    const sentences = document.querySelectorAll('.sentence');
    const graphContainer = document.getElementById('graph');

    function getDirectPredecessors(nodeId, edges) {{
        const predecessors = [];
        edges.forEach(edge => {{
            const [sourceStr, targetStr] = edge.split('->');
            const source = parseInt(sourceStr.trim(), 10);
            const target = parseInt(targetStr.trim(), 10);
            if (target === nodeId) {{
                predecessors.push(source);
            }}
        }});
        return predecessors;
    }}

    function getDirectSuccessors(nodeId, edges) {{
        const successors = [];
        edges.forEach(edge => {{
            const [sourceStr, targetStr] = edge.split('->');
            const source = parseInt(sourceStr.trim(), 10);
            const target = parseInt(targetStr.trim(), 10);
            if (source === nodeId) {{
                successors.push(target);
            }}
        }});
        return successors;
    }}

    function highlightSentence(sentence) {{
        sentences.forEach(s => s.classList.remove('highlight', 'unmatched-highlight'));
        const isMatched = sentence.classList.contains('matched');
        if (isMatched) {{
            sentence.classList.add('highlight');
        }} else {{
            sentence.classList.add('unmatched-highlight');
        }}
        // Remove other highlights from the selected sentence
        sentence.classList.remove('predecessor-highlight', 'successor-highlight');
    }}

    function highlightCausalSentences(predecessorIds, successorIds) {{
        sentences.forEach(sentence => {{
            const nodeId = parseInt(sentence.getAttribute('data-node'), 10);
            if (sentence.classList.contains('highlight') || sentence.classList.contains('unmatched-highlight')) {{
                // Skip the selected sentence
                return;
            }}
            sentence.classList.remove('predecessor-highlight', 'successor-highlight');
            if (predecessorIds.includes(nodeId)) {{
                sentence.classList.add('predecessor-highlight');
            }} else if (successorIds.includes(nodeId)) {{
                sentence.classList.add('successor-highlight');
            }}
        }});
    }}

    function clearCausalHighlights() {{
        sentences.forEach(sentence => {{
            sentence.classList.remove('predecessor-highlight', 'successor-highlight');
        }});
    }}

    function updateGraph(selectedNodeId, predecessors, successors) {{
        if (!useCausalRelations || !graphContainer) {{
            return;
        }}
        // Clear the graph container
        graphContainer.innerHTML = '';

        // Create elements for predecessors, selected node, and successors
        const elements = [];

        // Predecessors
        predecessors.forEach(nodeId => {{
            const nodeText = nodes[nodeId];
            const nodeElement = document.createElement('div');
            nodeElement.classList.add('node', 'predecessor-node');
            nodeElement.textContent = nodeText;
            elements.push(nodeElement);

            // Add arrow
            const arrowElement = document.createElement('div');
            arrowElement.classList.add('edge');
            arrowElement.textContent = '→';
            elements.push(arrowElement);
        }});

        // Selected Node
        const selectedNodeText = nodes[selectedNodeId];
        const selectedNodeElement = document.createElement('div');
        selectedNodeElement.classList.add('node', 'selected-node');
        selectedNodeElement.textContent = selectedNodeText;
        elements.push(selectedNodeElement);

        // Successors
        successors.forEach(nodeId => {{
            // Add arrow
            const arrowElement = document.createElement('div');
            arrowElement.classList.add('edge');
            arrowElement.textContent = '→';
            elements.push(arrowElement);

            const nodeText = nodes[nodeId];
            const nodeElement = document.createElement('div');
            nodeElement.classList.add('node', 'successor-node');
            nodeElement.textContent = nodeText;
            elements.push(nodeElement);
        }});

        // Append elements to the graph container
        elements.forEach(el => {{
            graphContainer.appendChild(el);
        }});
    }}

    sentences.forEach(sentence => {{
        sentence.addEventListener('click', () => {{
            const startTimeAttr = sentence.getAttribute('data-start');
            const startTime = startTimeAttr ? parseFloat(startTimeAttr) : null;
            const nodeId = parseInt(sentence.getAttribute('data-node'), 10);

            highlightSentence(sentence);

            if (startTime !== null && !isNaN(startTime)) {{
                video.currentTime = startTime;
                video.play();
            }}

            if (useCausalRelations && causalEdges.length > 0) {{
                const predecessors = getDirectPredecessors(nodeId, causalEdges);
                const successors = getDirectSuccessors(nodeId, causalEdges);
                highlightCausalSentences(predecessors, successors);
                updateGraph(nodeId, predecessors, successors);
            }} else {{
                clearCausalHighlights();
                if (graphContainer) {{
                    graphContainer.innerHTML = '';  // Clear the graph if causal relations are not enabled
                }}
            }}
        }});
    }});

    video.addEventListener('timeupdate', () => {{
        const currentTime = video.currentTime;

        sentences.forEach(sentence => {{
            const startAttr = sentence.getAttribute('data-start');
            const endAttr = sentence.getAttribute('data-end');
            const start = startAttr ? parseFloat(startAttr) : null;
            const end = endAttr ? parseFloat(endAttr) : null;
            if (start !== null && end !== null && !isNaN(start) && !isNaN(end)) {{
                if (currentTime >= start && currentTime <= end) {{
                    highlightSentence(sentence);

                    const nodeId = parseInt(sentence.getAttribute('data-node'), 10);

                    if (useCausalRelations && causalEdges.length > 0) {{
                        const predecessors = getDirectPredecessors(nodeId, causalEdges);
                        const successors = getDirectSuccessors(nodeId, causalEdges);
                        highlightCausalSentences(predecessors, successors);
                        updateGraph(nodeId, predecessors, successors);
                    }} else {{
                        clearCausalHighlights();
                        if (graphContainer) {{
                            graphContainer.innerHTML = '';  // Clear the graph if causal relations are not enabled
                        }}
                    }}
                }}
            }}
        }});
    }});
    </script>
    '''

    # Adjust the height based on whether causal relations are enabled
    if use_causal_relations:
        component_height = 900  # Increase height to accommodate the graph
    else:
        component_height = 620  # Reduce height when the graph is not displayed

    st.components.v1.html(html_content, height=component_height, scrolling=False)

    # Inform the user if causal relations are not available
    if selected_language != 'English':
        st.write("⚠️ Causal relations are not available for this video.")
    elif selected_language == 'English' and use_causal_relations and not edges:
        st.write("⚠️ Causal relations data is not available for this video.")

# ------------------------------
# Run the App
# ------------------------------

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {e}")
