"""
AI Resume Screener — Streamlit frontend.

What changed vs the original:
- Accepts PDF, DOCX, and TXT (not just .txt)
- File size validation before processing
- Cached computation — no redundant refitting on Streamlit reruns
- Composite score with four named, explained components
- Score gauge with colour coding
- Skills shown as coloured badges, not comma-separated strings
- Interview prep questions generated from detected gaps
- Full error handling with user-facing messages (no raw Python tracebacks)
- Session state clears results when new files are uploaded
"""
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

st.set_page_config(page_title="AI Resume Screener", layout="wide")

# ── Page header ───────────────────────────────────────────────────────────────
st.title("AI Resume Screener")
st.write(
    "Upload your CV and a job description. "
    "You'll get a composite match score with explanations for each component."
)

# ── File uploaders ─────────────────────────────────────────────────────────────
col_cv, col_jd = st.columns(2)

with col_cv:
    cv_file = st.file_uploader(
        "Upload your CV",
        type=["pdf", "docx", "txt"],
        help="PDF, Word document, or plain text. Max 5 MB.",
    )

with col_jd:
    job_file = st.file_uploader(
        "Upload the job description",
        type=["pdf", "docx", "txt"],
        help="PDF, Word document, or plain text. Max 5 MB.",
    )

# ── Reset state when new files are uploaded ───────────────────────────────────
# Without this, old results linger on screen when the user swaps files.
if "last_cv_name" not in st.session_state:
    st.session_state.last_cv_name = None
if "last_job_name" not in st.session_state:
    st.session_state.last_job_name = None

new_cv_name  = cv_file.name  if cv_file  else None
new_job_name = job_file.name if job_file else None

if (new_cv_name != st.session_state.last_cv_name or
        new_job_name != st.session_state.last_job_name):
    st.session_state.result = None
    st.session_state.last_cv_name  = new_cv_name
    st.session_state.last_job_name = new_job_name

# ── Main processing ───────────────────────────────────────────────────────────
if cv_file and job_file:

    if st.session_state.get("result") is None:
        with st.spinner("Analysing your CV against the job description…"):
            try:
                from parser import parse_uploaded_file
                from scorer import screen_cv

                cv_text  = parse_uploaded_file(cv_file)
                job_text = parse_uploaded_file(job_file)

                if len(cv_text.split()) < 30:
                    st.warning("Your CV appears very short. Make sure the correct file was uploaded.")
                if len(job_text.split()) < 20:
                    st.warning("The job description appears very short. Make sure the correct file was uploaded.")

                result = screen_cv(cv_text, job_text)
                st.session_state.result = result

            except ValueError as e:
                st.error(str(e))
                st.stop()
            except ImportError as e:
                st.error(f"Missing dependency: {e}")
                st.stop()
            except Exception as e:
                st.error(f"Unexpected error during analysis: {e}")
                st.stop()

    result = st.session_state.result
    if result is None:
        st.stop()

    # ── Composite score ────────────────────────────────────────────────────────
    st.divider()

    score_col, rating_col = st.columns([1, 2])

    with score_col:
        score = result.composite_score
        colour = (
            "#2ecc71" if score >= 70
            else "#f39c12" if score >= 45
            else "#e74c3c"
        )
        st.markdown(
            f"""
            <div style="text-align:center; padding: 1.5rem;
                        border-radius: 12px; border: 2px solid {colour};">
              <div style="font-size: 3rem; font-weight: 700; color: {colour};">
                {score:.0f}
              </div>
              <div style="font-size: 1rem; color: #888; margin-top: 4px;">
                out of 100
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with rating_col:
        st.subheader(result.rating)

        role_labels = {"intern": "🎓 Intern/Graduate mode", "mid": "💼 Mid-level mode", "senior": "🏆 Senior mode"}
        st.caption(f"{role_labels[result.role_level]} — weights adjusted accordingly")

        st.write(result.summary)

        # ── ATS / recruiter outcome prediction ────────────────────────────
        if score >= 75:
            st.success(
                "**Likely outcome**: Your CV should pass ATS filtering and land in a recruiter's shortlist. "
                "At this score, you're likely to be invited for a phone screen or first-stage interview — "
                "provided your experience level matches the role."
            )
        elif score >= 60:
            st.info(
                "**Likely outcome**: Your CV may pass ATS filtering but could be borderline for a human reviewer. "
                "A recruiter might glance at it but move on unless your opening summary immediately signals fit. "
                "Tailor your personal statement closely to the job description language."
            )
        elif score >= 45:
            st.warning(
                "**Likely outcome**: Your CV is at risk of being filtered out before a human sees it. "
                "ATS systems often use a score threshold of around 50–60%. "
                "Focus on closing the missing skills gap and mirroring the job description's exact phrasing."
            )
        else:
            st.error(
                "**Likely outcome**: Your CV is unlikely to pass automated screening for this specific role. "
                "This doesn't mean you're unqualified — it means this CV isn't tailored for this job. "
                "Consider whether this role is the right fit, or do a significant rewrite targeting the key requirements."
            )

        st.markdown("**Candidate summary**")
        st.write(result.composite_summary)

    # ── Score breakdown ────────────────────────────────────────────────────────
    st.subheader("Score breakdown")

    for comp in result.components:
        label = f"{comp.name} ({int(comp.weight * 100)}% weight)"
        bar_colour = (
            "green" if comp.score >= 70
            else "orange" if comp.score >= 45
            else "red"
        )
        st.progress(
            int(comp.score) / 100,
            text=f"{label}: **{comp.score:.0f}%**"
        )
        st.caption(comp.explanation)

    # ── Skills analysis ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Skills analysis")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Skills in your CV",       len(result.cv_skills))
    c2.metric("Skills required by role", len(result.job_skills))
    c3.metric("Matched",                 len(result.matched_skills))
    c4.metric("Missing",                 len(result.missing_skills), delta=f"-{len(result.missing_skills)}", delta_color="inverse")

    skill_col1, skill_col2 = st.columns(2)

    with skill_col1:
        st.markdown("**✅ Matched skills**")
        if result.matched_skills:
            badges = " ".join(
                f'<span style="background:#d4edda;color:#155724;padding:2px 8px;'
                f'border-radius:4px;margin:2px;display:inline-block;font-size:13px;">{s}</span>'
                for s in result.matched_skills
            )
            st.markdown(badges, unsafe_allow_html=True)
        else:
            st.write("No skills matched from the detected list.")

    with skill_col2:
        st.markdown("**❌ Missing skills**")
        if result.missing_skills:
            badges = " ".join(
                f'<span style="background:#f8d7da;color:#721c24;padding:2px 8px;'
                f'border-radius:4px;margin:2px;display:inline-block;font-size:13px;">{s}</span>'
                for s in result.missing_skills
            )
            st.markdown(badges, unsafe_allow_html=True)
        else:
            st.write("No missing skills detected from the job description.")

    if result.extra_skills:
        with st.expander("Bonus skills in your CV (not required by this role)"):
            badges = " ".join(
                f'<span style="background:#cce5ff;color:#004085;padding:2px 8px;'
                f'border-radius:4px;margin:2px;display:inline-block;font-size:13px;">{s}</span>'
                for s in result.extra_skills
            )
            st.markdown(badges, unsafe_allow_html=True)

    # ── CV formatting feedback ─────────────────────────────────────────────────
    st.divider()
    st.subheader("CV formatting feedback")

    icons = {"good": "✅", "warning": "⚠️", "error": "❌"}
    for note in result.formatting_notes:
        icon = icons.get(note["level"], "•")
        if note["level"] == "good":
            st.success(f"{icon} {note['message']}")
        elif note["level"] == "warning":
            st.warning(f"{icon} {note['message']}")
        else:
            st.error(f"{icon} {note['message']}")

    # ── Visualisation ──────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Visual summary")

    fig_col1, fig_col2 = st.columns(2)

    with fig_col1:
        # Grouped bar: matched vs missing
        fig, ax = plt.subplots(figsize=(5, 3))
        bars = ax.bar(
            ["Matched", "Missing"],
            [len(result.matched_skills), len(result.missing_skills)],
            color=["#2ecc71", "#e74c3c"],
            edgecolor="none",
            width=0.5,
        )
        ax.set_title("Matched vs Missing Skills", pad=10, fontsize=12)
        ax.set_ylabel("Count")
        ax.set_ylim(0, max(len(result.matched_skills), len(result.missing_skills)) + 2)
        ax.spines[["top", "right"]].set_visible(False)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.1, str(int(h)),
                    ha="center", va="bottom", fontsize=11)
        st.pyplot(fig)
        plt.close(fig)

    with fig_col2:
        # Radar / score breakdown bar
        names   = [c.name for c in result.components]
        scores  = [c.score for c in result.components]
        colours = ["#2ecc71" if s >= 70 else "#f39c12" if s >= 45 else "#e74c3c" for s in scores]

        fig2, ax2 = plt.subplots(figsize=(5, 3))
        ax2.barh(names, scores, color=colours, edgecolor="none")
        ax2.set_xlim(0, 100)
        ax2.set_xlabel("Score (%)")
        ax2.set_title("Score by Component", pad=10, fontsize=12)
        ax2.spines[["top", "right"]].set_visible(False)
        for i, (name, score) in enumerate(zip(names, scores)):
            ax2.text(score + 1, i, f"{score:.0f}%", va="center", fontsize=10)
        ax2.axvline(70, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
        st.pyplot(fig2)
        plt.close(fig2)

    # ── Improvement suggestions ────────────────────────────────────────────────
    st.divider()
    st.subheader("Improvement suggestions")

    _SUGGESTION_TEMPLATES = [
    ("**{skill}**: Add a bullet point or project that shows you've used this in practice.", ),
    ("**{skill}**: If you've touched this even briefly, mention it — a side project or coursework counts.", ),
    ("**{skill}**: Consider framing an existing project to highlight any overlap with {skill}.", ),
    ("**{skill}**: This appears multiple times in the job description — it's clearly a priority. Address it directly.", ),
    ("**{skill}**: Even a line like 'Familiar with {skill}' signals awareness if you've done any self-study.", ),
    ]

    if result.missing_skills:
        st.markdown("Consider adding evidence of these skills if you genuinely have experience with them:")
        import random
        templates = [t[0] for t in _SUGGESTION_TEMPLATES]
        random.shuffle(templates)
        for i, skill in enumerate(result.missing_skills):
            template = templates[i % len(templates)]
            st.markdown(f"- {template.format(skill=skill)}")
    
    # ── Interview questions ─────────────────────────────────────────────────────
    if result.interview_questions:
        st.divider()
        st.subheader("Interview preparation")
        st.write("Based on the gaps identified, be ready to answer these questions:")
        for q in result.interview_questions:
            st.markdown(f"> {q}")


    # ── Export ────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Export results")

    import csv
    import io as _io

    def build_csv(r) -> str:
        buf = _io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Field", "Value"])
        writer.writerow(["Composite score", r.composite_score])
        writer.writerow(["Rating", r.rating])
        writer.writerow(["Candidate summary", r.composite_summary])
        writer.writerow([])
        writer.writerow(["Score component", "Score (%)", "Weight (%)", "Explanation"])
        for c in r.components:
            writer.writerow([c.name, f"{c.score:.1f}", f"{int(c.weight*100)}", c.explanation])
        writer.writerow([])
        writer.writerow(["Matched skills"])
        for s in r.matched_skills:
            writer.writerow([s])
        writer.writerow([])
        writer.writerow(["Missing skills"])
        for s in r.missing_skills:
            writer.writerow([s])
        writer.writerow([])
        writer.writerow(["Interview questions"])
        for q in r.interview_questions:
            writer.writerow([q])
        return buf.getvalue()

    st.download_button(
        label="Download results as CSV",
        data=build_csv(result),
        file_name="cv_screening_results.csv",
        mime="text/csv",
    )


    # ── Disclaimer ─────────────────────────────────────────────────────────────
    st.divider()
    st.info(
        "**Important**: This tool uses keyword and statistical matching — not human judgement. "
        "Scores are indicative only. Do not add skills you don't have. "
        "Always tailor your CV honestly to each role."
    )

    #st.write("DEBUG:", {c.name: round(c.score, 1) for c in result.components})
