import streamlit as st
from parser import process_resumes

# UI
st.title("📄 AI Resume Ranker")
st.markdown("Upload resumes to rank them based on a job description.")

# Upload resumes folder
resumes_folder = "./resumes"  # you can keep this static for now

# Text area for job description
job_desc = st.text_area("🧾 Enter Job Description", height=200)

# Button to start ranking
if st.button("⚡ Rank Resumes"):
    if job_desc:
        with st.spinner("Processing resumes..."):
            results = process_resumes(resumes_folder, job_desc)
        
        st.success("✅ Done!")
        for r in results:
            st.subheader(f"{r['info'].get('name', 'Unknown')} - {r['relevance_score']}")
            st.write(f"📧 Email: {r['info'].get('email', 'N/A')}")
            st.write("🧠 Skills: " + ", ".join(r['info'].get('skills', [])))
            st.write("💼 Experience:")
            for exp in r['info'].get('experience', []):
                st.markdown(f"- {exp}")
            st.markdown("---")
    else:
        st.warning("Please enter a job description.")
