import streamlit as st
import json
import os
import requests
import re  # Import re for regular expressions

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
    Removes "Node (number): " prefix from each node text.
    """
    nodes = []
    if language == 'English' and st.session_state.get('use_causal_relations', False):
        node_url = f"{BASE_URL}/{language}/causal_graphs/{os.path.splitext(video_name)[0]}_nodes.txt"

        response = requests.get(node_url)
        if response.status_code == 200:
            nodes_raw = response.text.strip().split('\n')
            # Remove "Node (number): " prefix if present
            nodes = [re.sub(r'^Node \d+:\s*', '', line) for line in nodes_raw]
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
        matched = item.get('matched', 'no').lower().strip()  # Trim whitespace
        node_id = index  # Assign node_id based on index

        # Determine CSS class based on 'matched' status
        matched_class = 'matched' if matched == 'yes' else 'unmatched'

        # Handle missing start and end times
        data_start = f'data-start="{start}"' if start != '' else ''
        data_end = f'data-end="{end}"' if end != '' else ''

        # Add data-matched attribute for reliable checking in JS
        data_matched = f'data-matched="{matched}"'

        transcript_html += f'''
        <p class="sentence {matched_class}" {data_start} {data_end} {data_matched} data-node="{node_id}">
            {text}
        </p>
        '''
    return transcript_html

def main():
    st.title("📝 Multilingual Video Annotation Viewer")

    # Add project explanation under the title
    st.write("""
    This platform serves as a demonstration of the research presented in [Synopses of Movie Narratives: A Video-Language Dataset for Story Understanding](https://arxiv.org/abs/2203.05711). The study focuses on video-text retrieval and zero-shot alignment in movie summary videos by utilizing corresponding video frames to enhance story comprehension.
    """)

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
        # Add explanation under the checkbox
        st.sidebar.write("""
        This feature displays the extracted causal structures of the narrative, generated by GPT and other large language models (LLMs).
        """)
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
            box-sizing: border-box;
            background-color: #0e0e0e;
        }}
        #videoPlayer {{
            flex: 1;
            width: 100%;
        }}
        .sentence {{
            cursor: pointer;
            padding: 10px;
            color: white;
            transition: background-color 0.3s, color 0.3s;
            margin: 5px 0;
            border-radius: 5px;
        }}
        .sentence:hover {{
            background-color: #1a1a1a;
        }}
        .matched {{
            /* No additional styles for matched sentences */
        }}
        .unmatched {{
            color: #b0b0b0;
            font-style: italic;
        }}
        .highlight {{
            background-color: #ffff66; /* Yellow */
            color: black;
        }}
        .predecessor-highlight {{
            background-color: #66b3ff; /* Light Blue */
            color: black;
        }}
        .successor-highlight {{
            background-color: #66ff66; /* Light Green */
            color: black;
        }}
        .unmatched-highlight {{
            background-color: #b0b0b0;
            color: #0e0e0e;
        }}
        /* Graph section */
        #graph-section {{
            padding: 10px;
            box-sizing: border-box;
            background-color: #0e0e0e;
        }}
        #graph {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 40px; /* Increase spacing between node groups */
        }}
        .node-group {{
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 20px 0;
        }}
        .node-group-title {{
            font-weight: bold;
            margin-bottom: 10px;
            color: white;
        }}
        .node-container {{
            display: flex;
            flex-direction: row;
            align-items: center;
            gap: 40px; /* Increase spacing between nodes */
            flex-wrap: wrap;
            justify-content: center;
        }}
        .node {{
            padding: 10px;
            background-color: #1a1a1a;
            color: white;
            border-radius: 5px;
            text-align: center;
            max-width: 300px;
            cursor: default;
        }}
        .edge {{
            color: white;
            font-size: 24px;
            margin: 10px 0;
        }}
        .predecessor-node {{
            background-color: #66b3ff; /* Light Blue */
            color: black;
        }}
        .successor-node {{
            background-color: #66ff66; /* Light Green */
            color: black;
        }}
        .selected-node {{
            background-color: #ffff66; /* Yellow */
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
        // Remove all possible highlights
        sentences.forEach(s => s.classList.remove('highlight', 'unmatched-highlight', 'predecessor-highlight', 'successor-highlight'));
        const isMatched = sentence.dataset.matched === 'yes';
        if (isMatched) {{
            sentence.classList.add('highlight');
        }} else {{
            sentence.classList.add('unmatched-highlight');
        }}
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

        // Main Container
        const mainContainer = document.createElement('div');
        mainContainer.style.display = 'flex';
        mainContainer.style.flexDirection = 'column';
        mainContainer.style.alignItems = 'center';

        // Predecessors Group
        if (predecessors.length > 0) {{
            const predecessorsGroup = document.createElement('div');
            predecessorsGroup.classList.add('node-group');

            const title = document.createElement('div');
            title.classList.add('node-group-title');
            title.textContent = 'Predecessors';
            predecessorsGroup.appendChild(title);

            const nodeContainer = document.createElement('div');
            nodeContainer.classList.add('node-container');

            predecessors.forEach(nodeId => {{
                const nodeElement = document.createElement('div');
                nodeElement.classList.add('node', 'predecessor-node');
                const nodeText = nodes[nodeId];
                nodeElement.textContent = nodeText;
                nodeContainer.appendChild(nodeElement);
            }});

            predecessorsGroup.appendChild(nodeContainer);
            mainContainer.appendChild(predecessorsGroup);

            // Arrow pointing down to selected node
            const arrowElement = document.createElement('div');
            arrowElement.classList.add('edge');
            arrowElement.textContent = '↓';
            mainContainer.appendChild(arrowElement);
        }}

        // Current Node Group
        const currentNodeGroup = document.createElement('div');
        currentNodeGroup.classList.add('node-group');

        const currentTitle = document.createElement('div');
        currentTitle.classList.add('node-group-title');
        currentTitle.textContent = 'Current Event';
        currentNodeGroup.appendChild(currentTitle);

        const selectedNodeElement = document.createElement('div');
        selectedNodeElement.classList.add('node', 'selected-node');
        const selectedNodeText = nodes[selectedNodeId];
        selectedNodeElement.textContent = selectedNodeText;
        currentNodeGroup.appendChild(selectedNodeElement);

        mainContainer.appendChild(currentNodeGroup);

        // Successors Group
        if (successors.length > 0) {{
            // Arrow pointing down to successors
            const arrowElement = document.createElement('div');
            arrowElement.classList.add('edge');
            arrowElement.textContent = '↓';
            mainContainer.appendChild(arrowElement);

            const successorsGroup = document.createElement('div');
            successorsGroup.classList.add('node-group');

            const title = document.createElement('div');
            title.classList.add('node-group-title');
            title.textContent = 'Successors';
            successorsGroup.appendChild(title);

            const nodeContainer = document.createElement('div');
            nodeContainer.classList.add('node-container');

            successors.forEach(nodeId => {{
                const nodeElement = document.createElement('div');
                nodeElement.classList.add('node', 'successor-node');
                const nodeText = nodes[nodeId];
                nodeElement.textContent = nodeText;
                nodeContainer.appendChild(nodeElement);
            }});

            successorsGroup.appendChild(nodeContainer);
            mainContainer.appendChild(successorsGroup);
        }}

        graphContainer.appendChild(mainContainer);
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
                const isMatched = sentence.dataset.matched === 'yes';
                if (isMatched) {{
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
            }} else {{
                clearCausalHighlights();
                if (graphContainer) {{
                    graphContainer.innerHTML = '';  // Clear the graph if causal relations are not enabled
                }}
            }}
        }});
    }});

    function checkAndHighlightCurrentSentence() {{
        const currentTime = video.currentTime;
        let matchedFound = false;  // Flag to check if any sentence matches the current time

        sentences.forEach(sentence => {{
            const startAttr = sentence.getAttribute('data-start');
            const endAttr = sentence.getAttribute('data-end');
            const start = startAttr ? parseFloat(startAttr) : null;
            const end = endAttr ? parseFloat(endAttr) : null;
            if (start !== null && end !== null && !isNaN(start) && !isNaN(end)) {{
                if (currentTime >= start && currentTime < end) {{
                    matchedFound = true;
                    highlightSentence(sentence);

                    const nodeId = parseInt(sentence.getAttribute('data-node'), 10);

                    if (useCausalRelations && causalEdges.length > 0) {{
                        const isMatched = sentence.dataset.matched === 'yes';
                        if (isMatched) {{
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
                    }} else {{
                        clearCausalHighlights();
                        if (graphContainer) {{
                            graphContainer.innerHTML = '';  // Clear the graph if causal relations are not enabled
                        }}
                    }}
                }}
            }}
        }});

        if (!matchedFound) {{
            // Clear all highlights and causal graph if no sentence matches the current time
            sentences.forEach(sentence => {{
                sentence.classList.remove('highlight', 'unmatched-highlight', 'predecessor-highlight', 'successor-highlight');
            }});
            clearCausalHighlights();
            if (graphContainer) {{
                graphContainer.innerHTML = '';
            }}
        }}
    }}

    video.addEventListener('timeupdate', checkAndHighlightCurrentSentence);

    // Add 'seeked' event listener to handle seeking
    video.addEventListener('seeked', () => {{
        checkAndHighlightCurrentSentence();
    }});
    </script>
    '''

    # Adjust the height based on whether causal relations are enabled
    if use_causal_relations:
        component_height = 1200  # Adjusted height to accommodate the graph
    else:
        component_height = 620  # Reduce height when the graph is not displayed

    st.components.v1.html(html_content, height=component_height, scrolling=False)

    # Inform the user if causal relations are not available
    if selected_language != 'English':
        st.write("⚠️ Causal relations are not available for this video.")
    elif selected_language == 'English' and use_causal_relations and not edges:
        st.write("⚠️ Causal relations data is not available for this video.")

    # Add a separator
    st.markdown("---")

    # Display the references at the bottom in a separate box
    st.markdown("""
    ### References
    1. **Sun, Y., Chao, Q., & Li, B. (2024).** *Event Causality Is Key to Computational Story Understanding*. arXiv preprint arXiv:[2311.09648](https://arxiv.org/abs/2311.09648).
    2. **Sun, Y., Chao, Q., Ji, Y., & Li, B. (2023).** *Synopses of Movie Narratives: A Video-Language Dataset for Story Understanding*. arXiv preprint arXiv:[2203.05711](https://arxiv.org/abs/2203.05711).
    """)

# ------------------------------
# Run the App
# ------------------------------

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {e}")

