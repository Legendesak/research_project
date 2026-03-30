import streamlit as st
import pandas as pd

from load_data import load_internships, get_all_skills
from matcher import build_similarity_model, match_student_profile


st.set_page_config(page_title="Internship Matching System", layout="wide")

st.title("Localized Internship Matching System")
st.subheader("Prototype for Sri Lankan Tech Internship Matching")

CSV_PATH = "/mount/src/research_project/skill_pipeline_v2/output/internships_with_skills_v2.csv"  # Change this if your file is somewhere else

@st.cache_data
def cached_load_data(path: str):
    return load_internships(path)

df = cached_load_data(CSV_PATH)
all_skills = get_all_skills(df)
vectorizer, internship_matrix = build_similarity_model(df)

with st.sidebar:
    st.header("Student Profile")
    student_name = st.text_input("Student Name")
    preferred_location = st.text_input("Preferred Location")
    student_skills = st.multiselect("Select Your Skills", all_skills)

    top_n = st.slider("Number of Matches", min_value=5, max_value=20, value=10)

    run_match = st.button("Find Matching Internships")

tab1, tab2, tab3 = st.tabs(["Matcher", "Skill Gap View", "Market Insights"])

with tab1:
    st.write("### Internship Matcher")

    if run_match:
        if not student_skills:
            st.warning("Please select at least one skill.")
        else:
            results = match_student_profile(
                student_skills=student_skills,
                df=df,
                vectorizer=vectorizer,
                internship_matrix=internship_matrix,
                top_n=top_n
            )

            if preferred_location.strip():
                results = results[
                    results["town"].fillna("").str.lower().str.contains(preferred_location.lower(), na=False)
                ]

            if results.empty:
                st.error("No matching internships found.")
            else:
                st.success(f"Found {len(results)} matching internships")

                for _, row in results.iterrows():
                    with st.container():
                        st.markdown(f"## {row.get('title', 'Untitled Internship')}")
                        st.write(f"**Company:** {row.get('company', 'N/A')}")
                        st.write(f"**Location:** {row.get('town', 'N/A')}")
                        st.write(f"**Match Score:** {row['match_percentage']}%")
                        st.write(f"**Required Skills:** {row.get('tech_skills', '')}")
                        st.write(f"**Matched Skills:** {row.get('matched_skills', '')}")
                        st.write(f"**Missing Skills:** {row.get('missing_skills', '')}")

                        ad_url = str(row.get("ad_url", "")).strip()
                        if ad_url:
                            st.markdown(f"[View Advertisement]({ad_url})")

                        st.divider()
    else:
        st.info("Enter your skills in the sidebar and click 'Find Matching Internships'.")

with tab2:
    st.write("### Skill Gap Analysis")

    if run_match and student_skills:
        results = match_student_profile(
            student_skills=student_skills,
            df=df,
            vectorizer=vectorizer,
            internship_matrix=internship_matrix,
            top_n=top_n
        )

        gap_rows = []
        for _, row in results.iterrows():
            gap_rows.append({
                "Title": row.get("title", ""),
                "Company": row.get("company", ""),
                "Match %": row.get("match_percentage", 0),
                "Matched Skills": row.get("matched_skills", ""),
                "Missing Skills": row.get("missing_skills", "")
            })

        gap_df = pd.DataFrame(gap_rows)
        st.dataframe(gap_df, use_container_width=True)
    else:
        st.info("Run the matcher first to see skill gaps.")

with tab3:
    st.write("### Market Insights")

    # explode skills for frequency analysis
    exploded = df.explode("tech_skills_list")
    exploded = exploded[exploded["tech_skills_list"].notna() & (exploded["tech_skills_list"] != "")]

    if not exploded.empty:
        skill_counts = exploded["tech_skills_list"].value_counts().head(15)
        st.bar_chart(skill_counts)

        st.write("### Top Skills in Internship Dataset")
        st.dataframe(skill_counts.rename_axis("Skill").reset_index(name="Count"), use_container_width=True)
    else:
        st.warning("No skill data found.")
