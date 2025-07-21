import streamlit as st
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os
from datetime import datetime
from PIL import Image
import io

# Set page config
st.set_page_config(page_title="RDN Property Photo Comparison", page_icon="🏠", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .main {background-color: #f5f5f5;}
    .stButton>button {background-color: #4CAF50; color: white;}
    .stFileUploader>div>div>button {background-color: #4CAF50; color: white;}
    .sidebar .sidebar-content {background-color: #e8f5e9;}
    h1 {color: #2e7d32;}
    h2 {color: #388e3c;}
    .similarity-high {color: #2e7d32; font-weight: bold;}
    .similarity-medium {color: #fbc02d; font-weight: bold;}
    .similarity-low {color: #d32f2f; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

def compare_images(image1, image2):
    """Compare two images and return similarity score and difference visualization"""
    try:
        # Convert to numpy arrays if they aren't already
        if isinstance(image1, Image.Image):
            image1 = np.array(image1)
        if isinstance(image2, Image.Image):
            image2 = np.array(image2)
        
        # Convert BGR to RGB if needed
        if len(image1.shape) == 3 and image1.shape[2] == 3:
            image1 = cv2.cvtColor(image1, cv2.COLOR_RGB2BGR)
        if len(image2.shape) == 3 and image2.shape[2] == 3:
            image2 = cv2.cvtColor(image2, cv2.COLOR_RGB2BGR)
        
        # Resize images to the same dimensions
        height = min(image1.shape[0], image2.shape[0])
        width = min(image1.shape[1], image2.shape[1])
        
        image1 = cv2.resize(image1, (width, height))
        image2 = cv2.resize(image2, (width, height))
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        
        # Calculate Structural Similarity Index (SSIM)
        score, diff = ssim(gray1, gray2, full=True)
        diff = (diff * 255).astype("uint8")
        
        # Threshold the difference image
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        
        # Find contours to highlight differences
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw rectangles around differences
        image_copy = image2.copy()
        for contour in contours:
            if cv2.contourArea(contour) > 100:  # Only consider significant differences
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(image_copy, (x, y), (x + w, y + h), (0, 0, 255), 2)
        
        # Convert back to RGB for display
        image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2RGB)
        image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
        image_copy = cv2.cvtColor(image_copy, cv2.COLOR_BGR2RGB)
        
        return score, image1, image2, image_copy
    except Exception as e:
        st.error(f"Error comparing images: {str(e)}")
        return None, None, None, None

def get_similarity_class(score):
    """Return CSS class based on similarity score"""
    if score > 0.8:
        return "similarity-high"
    elif score > 0.6:
        return "similarity-medium"
    else:
        return "similarity-low"

def main():
    st.title("🏠 RDN Property Photo Comparison")
    st.markdown("Compare reference property photos with field photos for Rate Demand Notice delivery in Makeni, Sierra Leone")
    
    # Sidebar for options
    with st.sidebar:
        st.header("Comparison Options")
        comparison_mode = st.radio(
            "Select comparison mode:",
            ("Single Comparison", "Batch Comparison")
        )
        
        if comparison_mode == "Single Comparison":
            st.markdown("### Single Photo Comparison")
            st.markdown("Upload one reference photo and one field photo for comparison.")
        else:
            st.markdown("### Batch Photo Comparison")
            st.markdown("Upload multiple reference and field photos for batch processing.")
            st.warning("Note: For batch processing, ensure filenames match between reference and field photos.")
    
    if comparison_mode == "Single Comparison":
        st.subheader("Single Photo Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Reference Photo")
            ref_file = st.file_uploader("Upload reference property photo", type=["jpg", "jpeg", "png"], key="ref")
            if ref_file:
                ref_image = Image.open(ref_file)
                st.image(ref_image, caption="Reference Property Photo", use_column_width=True)
        
        with col2:
            st.markdown("### Field Photo")
            field_file = st.file_uploader("Upload field property photo", type=["jpg", "jpeg", "png"], key="field")
            if field_file:
                field_image = Image.open(field_file)
                st.image(field_image, caption="Field Property Photo", use_column_width=True)
        
        if ref_file and field_file:
            if st.button("Compare Photos", key="compare_single"):
                with st.spinner("Comparing images..."):
                    score, img1, img2, diff_img = compare_images(ref_image, field_image)
                
                if score is not None:
                    st.success("Comparison completed!")
                    
                    # Display similarity score with color coding
                    similarity_class = get_similarity_class(score)
                    st.markdown(f"### Similarity Score: <span class='{similarity_class}'>{score:.3f}</span>", 
                                unsafe_allow_html=True)
                    
                    # Display comparison results
                    st.subheader("Comparison Results")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.image(img1, caption="Reference Photo", use_column_width=True)
                    with col2:
                        st.image(img2, caption="Field Photo", use_column_width=True)
                    with col3:
                        st.image(diff_img, caption="Differences Highlighted", use_column_width=True)
                    
                    # Interpretation guidance
                    st.markdown("""
                    **Similarity Score Interpretation:**
                    - **Above 0.8**: Very similar (likely same property)
                    - **0.6 - 0.8**: Moderately similar (possible changes or angle differences)
                    - **Below 0.6**: Low similarity (possible different property)
                    """)
                    
                    # Download button for the difference image
                    buf = io.BytesIO()
                    diff_pil = Image.fromarray(diff_img)
                    diff_pil.save(buf, format="JPEG")
                    byte_im = buf.getvalue()
                    
                    st.download_button(
                        label="Download Comparison Result",
                        data=byte_im,
                        file_name=f"comparison_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                        mime="image/jpeg"
                    )
    
    else:  # Batch Comparison
        st.subheader("Batch Photo Comparison")
        
        st.markdown("""
        ### Instructions for Batch Comparison:
        1. Prepare two folders:
           - One with reference photos (original property photos)
           - One with field photos (taken by enumerators)
        2. Ensure matching filenames between the folders
        3. Upload both folders below
        """)
        
        ref_files = st.file_uploader("Upload reference photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        field_files = st.file_uploader("Upload field photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        
        if ref_files and field_files:
            if st.button("Process Batch Comparison", key="compare_batch"):
                # Create dictionaries of uploaded files by filename
                ref_dict = {os.path.basename(f.name): f for f in ref_files}
                field_dict = {os.path.basename(f.name): f for f in field_files}
                
                # Find matching filenames
                common_files = set(ref_dict.keys()) & set(field_dict.keys())
                
                if not common_files:
                    st.error("No matching filenames found between reference and field photos.")
                else:
                    progress_bar = st.progress(0)
                    results = []
                    
                    for i, filename in enumerate(sorted(common_files)):
                        progress_bar.progress((i + 1) / len(common_files))
                        
                        ref_img = Image.open(ref_dict[filename])
                        field_img = Image.open(field_dict[filename])
                        
                        score, _, _, diff_img = compare_images(ref_img, field_img)
                        
                        if score is not None:
                            results.append({
                                'filename': filename,
                                'score': score,
                                'match': score > 0.75,
                                'diff_img': diff_img
                            })
                    
                    # Display batch results
                    st.success(f"Batch comparison completed for {len(results)} properties!")
                    
                    # Summary statistics
                    matched = sum(1 for r in results if r['match'])
                    total = len(results)
                    
                    st.markdown(f"""
                    ### Summary Statistics:
                    - **Total properties compared**: {total}
                    - **Matching properties**: {matched} ({matched/total*100:.1f}%)
                    - **Non-matching properties**: {total - matched}
                    """)
                    
                    # Detailed results in an expandable section
                    with st.expander("View Detailed Results"):
                        for result in results:
                            similarity_class = get_similarity_class(result['score'])
                            
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                st.markdown(f"**{result['filename']}**")
                                st.markdown(f"Score: <span class='{similarity_class}'>{result['score']:.3f}</span>", 
                                            unsafe_allow_html=True)
                                st.markdown(f"Match: {'✅' if result['match'] else '❌'}")
                            
                            with col2:
                                st.image(result['diff_img'], caption=f"Differences for {result['filename']}", 
                                        use_column_width=True)
                            
                            st.markdown("---")

if __name__ == "__main__":
    main()