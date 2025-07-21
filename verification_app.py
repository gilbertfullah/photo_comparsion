import os
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime

# Set page config
st.set_page_config(page_title="RDN Property Verification", page_icon="🏠", layout="wide")

# Custom CSS styling
st.markdown("""
<style>
    .main {background-color: #f5f5f5;}
    .stButton>button {width: 150px; margin: 5px;}
    .green-button {background-color: #4CAF50 !important; color: white !important;}
    .red-button {background-color: #f44336 !important; color: white !important;}
    .gray-button {background-color: #607D8B !important; color: white !important;}
    .progress-bar {padding: 10px; background-color: #eee; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

def get_image_pairs(folder_path):
    """Organize images into pairs based on ID"""
    try:
        files = os.listdir(folder_path)
        image_pairs = {}
        
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                if '_original' in file:
                    base_id = file.split('_original')[0]
                    image_pairs.setdefault(base_id, {})['original'] = file
                elif '_proof' in file:
                    base_id = file.split('_proof')[0]
                    image_pairs.setdefault(base_id, {})['proof'] = file
        
        # Filter only pairs with both images
        valid_pairs = []
        for base_id, pair in image_pairs.items():
            if 'original' in pair and 'proof' in pair:
                valid_pairs.append({
                    'id': base_id,
                    'original': os.path.join(folder_path, pair['original']),
                    'proof': os.path.join(folder_path, pair['proof'])
                })
        
        return valid_pairs
    except Exception as e:
        st.error(f"Error processing images: {str(e)}")
        return []

def main():
    st.title("🏠 RDN Property Verification System")
    st.markdown("### Manual Verification of Property Photos")
    
    # Initialize session state
    if 'verification_data' not in st.session_state:
        st.session_state.verification_data = {
            'current_pair': 0,
            'decisions': [],
            'image_pairs': [],
            'verification_complete': False,
            'folder_path': None
        }
    
    # Folder input
    folder_path = st.text_input("Enter path to image folder:")
    
    # Reset state if folder path changes
    if folder_path and folder_path != st.session_state.verification_data['folder_path']:
        st.session_state.verification_data = {
            'current_pair': 0,
            'decisions': [],
            'image_pairs': get_image_pairs(folder_path),
            'verification_complete': False,
            'folder_path': folder_path
        }
    
    # Main verification logic
    if folder_path:
        if not os.path.exists(folder_path):
            st.error("The specified folder path does not exist!")
            return
        
        if not st.session_state.verification_data['image_pairs']:
            st.error("No valid image pairs found in the folder!")
            return
        
        total_pairs = len(st.session_state.verification_data['image_pairs'])
        
        # Check if verification is complete
        if st.session_state.verification_data['current_pair'] >= total_pairs:
            st.session_state.verification_data['verification_complete'] = True
        else:
            # Get current pair data
            current_data = st.session_state.verification_data['image_pairs'][st.session_state.verification_data['current_pair']]
            
            # Display progress
            progress = (st.session_state.verification_data['current_pair'] + 1) / total_pairs
            st.markdown(f"""
            <div class="progress-bar">
                Progress: {st.session_state.verification_data['current_pair'] + 1} of {total_pairs} pairs verified
                <div style="width: {progress * 100}%; height: 10px; background-color: #4CAF50; margin-top: 5px;"></div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display images
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Original Photo")
                try:
                    original_img = Image.open(current_data['original'])
                    st.image(original_img, use_column_width=True)
                except Exception as e:
                    st.error(f"Error loading original image: {str(e)}")
            
            with col2:
                st.markdown("### Proof Photo")
                try:
                    proof_img = Image.open(current_data['proof'])
                    st.image(proof_img, use_column_width=True)
                except Exception as e:
                    st.error(f"Error loading proof image: {str(e)}")
            
            # Decision buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Yes - Same Property", key="yes", use_container_width=True):
                    st.session_state.verification_data['decisions'].append({
                        'property_id': current_data['id'],
                        'decision': 'Yes',
                        'timestamp': datetime.now().isoformat()
                    })
                    st.session_state.verification_data['current_pair'] += 1
                    st.rerun()  # Changed from experimental_rerun() to rerun()
            
            with col2:
                if st.button("❌ No - Different Property", key="no", use_container_width=True):
                    st.session_state.verification_data['decisions'].append({
                        'property_id': current_data['id'],
                        'decision': 'No',
                        'timestamp': datetime.now().isoformat()
                    })
                    st.session_state.verification_data['current_pair'] += 1
                    st.rerun()  # Changed from experimental_rerun() to rerun()
            
            with col3:
                if st.button("➖ No Decision", key="undecided", use_container_width=True):
                    st.session_state.verification_data['decisions'].append({
                        'property_id': current_data['id'],
                        'decision': 'No Decision',
                        'timestamp': datetime.now().isoformat()
                    })
                    st.session_state.verification_data['current_pair'] += 1
                    st.rerun()  # Changed from experimental_rerun() to rerun()
    
    # Show completion message and download button
    if st.session_state.verification_data.get('verification_complete', False):
        st.success("🎉 All properties have been verified!")
        
        if st.session_state.verification_data['decisions']:
            df = pd.DataFrame(st.session_state.verification_data['decisions'])
            
            # Download buttons
            st.markdown("### Download Verification Results")
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )

if __name__ == "__main__":
    main()